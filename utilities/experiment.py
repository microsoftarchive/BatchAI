from __future__ import print_function

import collections
import hashlib
import json
import logging
import re
import time
import sys

import azure.mgmt.batchai.models as models
import concurrent.futures
import requests
from azure.mgmt.storage import StorageManagementClient
from concurrent.futures import ThreadPoolExecutor
from msrestazure.azure_exceptions import CloudError
from msrestazure.polling.arm_polling import ARMPolling
from msrestazure.tools import parse_resource_id

NUM_THREADS = 30
RETRY_WAIT_SECS = 5
JOB_NAME_HASH_LENGTH = 16
NUM_RETRIES = 5

Job = collections.namedtuple('Job', [
    'name',
    'parameters'
])


class ExperimentUtils(object):
    def __init__(self, client, resource_group_name, workspace_name,
                 experiment_name):
        """Create a JobSubmitter object to manage job requests to the
        specified experiment.

        :param BatchAIManagementClient client
        :param str resource_group_name: Name of resource group of experiment
        :param str workspace_name: Name of workspace of experiment
        :param str experiment_name: Name of the experiment
        """
        self.client = client
        self.resource_group_name = resource_group_name
        self.workspace_name = workspace_name
        self.experiment_name = experiment_name
        self.client.experiments.get(  # Ensure experiment exists
            resource_group_name, workspace_name, experiment_name)
        self.logger = logging.getLogger('ExperimentUtils')
        self.logger.info(
            "Initialized JobSubmitter in resource group: {0} | "
            "workspace: {1} | experiment {2}".format(
                self.resource_group_name, self.workspace_name,
                self.experiment_name
            ))

    def submit_jobs(self, jcp_list, job_name_prefix, max_retries=NUM_RETRIES,
                    num_threads=NUM_THREADS):
        """Submit jobs with the JobCreateParameters in jcp_list. Jobs have name
        job_name_prefix with a hash of the JobCreateParameters object appended.

        :param List<azure.mgmt.batchai.models.JobCreateParameters> jcp_list:
        a list of JobCreateParameters objects to submit
        :param str job_name_prefix: prefix for job names
        :param int max_retries: Number of retries if server returns 5xx for
        submission.
        :return: A Future object. Call .result() on the object to get the
        list of azure.mgmt.batchai.models.Job with a blocking call
        :rtype: concurrent.futures.Future
        """
        jobs = [Job(
            name=job_name_prefix + '_' + self._hash_jcp(jcp),
            parameters=jcp) for jcp in jcp_list
        ]
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            self._submit_jobs_threadpool, jobs, max_retries=max_retries,
            num_threads=num_threads)
        executor.shutdown(wait=False)  # Do not block on waiting for results
        return future

    def _submit_jobs_threadpool(self, jobs, max_retries, num_threads):
        """Submits jobs using a threadpool. Returns list of
        azure.mgmt.batchai.models.Job objects representing submitted jobs.
        """
        if len(jobs) == 0:
            return
        job_results = []
        attempts_left = max_retries + 1
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            while jobs and attempts_left > 0:
                futures_to_jobs = {}
                for job in jobs:
                    future = executor.submit(
                        self._submit_job, job.name, job.parameters)
                    futures_to_jobs[future] = job
                jobs = []
                for future in concurrent.futures.as_completed(futures_to_jobs):
                    try:
                        result = future.result()
                        job_results.append(result)
                    except CloudError as ce:
                        if ce.response.status_code >= 500:
                            job = futures_to_jobs[future]
                            print(
                                "Job {0} failed to submit. "
                                "Retrying ({1} attempts remaining)...".format(
                                    job.name, attempts_left))
                            jobs.append(job)
                        else:
                            self.logger.error("Error: %s", str(ce))
                            raise ce
                attempts_left -= 1
                if jobs and attempts_left > 0:
                    print("Waiting {0} seconds...".format(RETRY_WAIT_SECS))
                    time.sleep(RETRY_WAIT_SECS)
        if jobs:
            print("{0} jobs failed to submit.".format(len(jobs)))
        return job_results

    def _submit_job(self, job_name, jcp):
        """Submit a job. Returns azure.mgmt.batchai.models.Job object
        representing the submitted job.
        """
        polling = CustomPolling()  # Poll for results once per second
        job = self.client.jobs.create(
            self.resource_group_name, self.workspace_name,
            self.experiment_name, job_name, jcp, polling=polling).result()
        if not job.environment_variables:
            job.environment_variables = []
        parameters = {ev.name: ev.value for ev in job.environment_variables}
        self.logger.info("Created job \"{0}\" with parameters {1}".format(
            job.name, json.dumps(parameters, sort_keys=True)))
        return job

    def _hash_jcp(self, jcp, length=JOB_NAME_HASH_LENGTH):
        """Generate a hash for the JobCreateParameters object.
        """
        jcp_json_str = json.dumps(
            jcp, default=lambda o: o.__dict__, sort_keys=True)
        hash_str = hashlib.sha1(jcp_json_str.encode()).hexdigest()
        hash_str_substr = hash_str[0:length]
        return hash_str_substr

    def wait_all_jobs(self, job_names=None, on_progress=None):
        """Block until all jobs in the experiment are completed (succeeded
        or failed).

        :param List<str> job_names: names of jobs to wait for. If None, wait
        until all jobs in experiment are completed.
        :param func on_progress: a function called every 10 secs with list of
        azure.mgmt.batchai.models.Job representing current state of jobs
        :return: list of completed jobs
        :rtype: List<azure.mgmt.batchai.models.Job>
        """

        jobs = list(self.client.jobs.list_by_experiment(
            self.resource_group_name, self.workspace_name,
            self.experiment_name))
        if job_names:
            jobs = [j for j in jobs if j.name in job_names]
        while self._num_jobs_completed(jobs) != len(jobs):
            print("{0}/{1} jobs completed ({2} succeeded, {3} failed)".format(
                self._num_jobs_completed(jobs), len(jobs),
                self._num_jobs_in_state(jobs, models.ExecutionState.succeeded),
                self._num_jobs_in_state(jobs, models.ExecutionState.failed)),
                end='')
            sys.stdout.flush()
            for _ in range(10):
                print('.', end='')
                sys.stdout.flush()
                time.sleep(5)
            print()
            jobs = list(self.client.jobs.list_by_experiment(
                self.resource_group_name, self.workspace_name,
                self.experiment_name))
            if job_names:
                jobs = [j for j in jobs if j.name in job_names]
            if on_progress:
                on_progress(jobs)
        print("All jobs completed.")
        return jobs

    def _num_jobs_completed(self, jobs):
        return (
                self._num_jobs_in_state(jobs, models.ExecutionState.succeeded) +
                self._num_jobs_in_state(jobs, models.ExecutionState.failed))

    def _num_jobs_in_state(self, jobs, state):
        return len([j for j in jobs if j.execution_state == state])

    def list_stdouterr_files(self, job_name):
        """List the files of stdout and stderr for a job.
        """
        files = self.client.jobs.list_output_files(
            self.resource_group_name, self.workspace_name,
            self.experiment_name, job_name,
            models.JobsListOutputFilesOptions(outputdirectoryid='stdouterr'))
        for idx, f in enumerate(files):
            print("File {0}: {1} | Download: {2}".format(
                idx + 1, f.name, f.download_url))

    def get_parameters_of_job(self, job_name):
        """Get the parameter sweep variables (through environment variables) of
        a job.
        """
        job = self.client.jobs.get(
            self.resource_group_name, self.workspace_name,
            self.experiment_name, job_name)
        env_vars = job.environment_variables
        parameters = {ev.name: ev.value for ev in env_vars}
        return parameters

    def resubmit_failed_jobs(self, job_names=None, max_retries=NUM_RETRIES,
                             num_threads=NUM_THREADS):
        """Resubmit failed jobs.

        :param List<str> job_names: List of names of jobs to resubmit. If none,
        all failed jobs in the experiment are resubmitted.
        :param job_names: [type], optional
        :param max_retries: [description], defaults to NUM_RETRIES
        :param max_retries: [type], optional
        :param bool confirm: whether confirmation dialogs will be presented
        :return: list of resubmitted jobs
        :rtype: List<azure.mgmt.batchai.models.Job>
        """

        all_jobs = list(self.client.jobs.list_by_experiment(
            self.resource_group_name, self.workspace_name,
            self.experiment_name))
        if job_names:
            all_jobs = [
                j for j in all_jobs if j.name in job_names]
        failed_jobs = [j for j in all_jobs
                       if j.execution_state == models.ExecutionState.failed]
        failed_jobs_names = [j.name for j in failed_jobs]
        if not failed_jobs:
            self.logger.info(
                "There are no failed jobs in the experiment {0}.".format(
                    self.experiment_name))
            return
        print("Deleting the failed jobs...")
        self.delete_jobs_in_experiment(job_names=failed_jobs_names)
        jobs_to_submit = [
            Job(name=job.name, parameters=self._create_jcp_from_job(job))
            for job in failed_jobs
        ]
        resubmitted_jobs = self._submit_jobs_threadpool(
            jobs_to_submit, max_retries, num_threads)
        return resubmitted_jobs

    def _get_storage_account_key(self, account_name):
        storage_client = StorageManagementClient(
            credentials=self.client.config.credentials,
            subscription_id=self.client.config.subscription_id,
            base_url=self.client.config.base_url)
        accounts = [a.id for a in list(storage_client.storage_accounts.list())
                    if a.name == account_name]
        if not accounts:
            raise ValueError(
                'Cannot find "{0}" storage account.'.format(account_name))
        resource_group = parse_resource_id(accounts[0])['resource_group']
        keys_list_result = storage_client.storage_accounts.list_keys(
            resource_group, account_name)
        if not keys_list_result or not keys_list_result.keys:
            raise ValueError(
                'Cannot find a key for "{0}" storage account.'.format(
                    account_name))
        return keys_list_result.keys[0].value

    def _create_jcp_from_job(self, job):
        jcp_kwargs = models.JobCreateParameters._attribute_map.keys()
        jcp_dict = {
            kwarg: getattr(job, kwarg)
            for kwarg in jcp_kwargs if hasattr(job, kwarg)
        }
        new_jcp = models.JobCreateParameters(**jcp_dict)
        for bfs in new_jcp.mount_volumes.azure_blob_file_systems:
            bfs.credentials.account_key = self._get_storage_account_key(
                bfs.account_name)
        for afs in new_jcp.mount_volumes.azure_file_shares:
            afs.credentials.account_key = self._get_storage_account_key(
                afs.account_name
            )
        return new_jcp

    def extract_metric(self, job_name, output_dir_id, logfile_name, regex,
                       calculate="last"):
        """Get the value of a metric from a job's logfile.

        :param str job_name: name of the job
        :param str output_dir_id: models.OutputDirectory.id of the directory
        where the logfile is stored. Use "stdouterr" if logging to stdout (i.e.
        print)
        :param str logfile_name: name of the logfile (with extension) in the
        output directory
        :param str regex: regex used with re.findall for matching numbers
        corresponding to the metric value
        :param str calculate: how to calculate the metric from the matches found
        by regex. Options: last, mean, min, max
        :return: metric value
        :rtype: float
        """
        files = self.client.jobs.list_output_files(
            self.resource_group_name, self.workspace_name,
            self.experiment_name, job_name,
            models.JobsListOutputFilesOptions(outputdirectoryid=output_dir_id))
        val = None
        for f in files:
            if f.name == logfile_name:
                text = ""
                try:
                    r = requests.get(f.download_url, stream=True)
                    for chunk in r.iter_content(chunk_size=512 * 1024):
                        if chunk:  # filter out keep-alive new chunks
                            text += chunk.decode(encoding='UTF-8')
                except Exception as e:
                    print(e)
                vals = re.findall(regex, text, re.DOTALL)
                if not vals:
                    raise ValueError("No matching metric values in log file.")
                if calculate is "last":
                    val = float(vals[len(vals) - 1])
                elif calculate is "mean":
                    val = sum([float(m) for m in vals]) / len(vals)
                elif calculate is "min":
                    val = min([float(m) for m in vals])
                elif calculate is "max":
                    val = max([float(m) for m in vals])
                break
        return val

    def submit_jobs_and_return_metric(self, jcps, output_dir, logfile_name,
                                      regex, metric='last', on_progress=None,
                                      max_retries=NUM_RETRIES,
                                      num_threads=NUM_THREADS):
        """Submits jobs and returns the jobs and their metric value after
        running.
        """
        jobs = [Job(name=self._hash_jcp(jcp), parameters=jcp) for jcp in jcps]
        jobs = self._submit_jobs_threadpool(jobs, max_retries, num_threads)
        self.wait_all_jobs(
            job_names=[j.name for j in jobs], on_progress=on_progress)
        job_results = []
        for idx, job in enumerate(jobs):
            metric = self.extract_metric(
                job.name, output_dir, logfile_name, regex, metric=metric)
            job_results.append({
                "name": job.name,
                "metric": metric,
                "index": idx
            })
        job_results.sort(key=lambda j: j['metric'])
        return job_results

    def delete_jobs_in_experiment(self, execution_state=None, job_names=None,
                                  job_name_regex=None, num_threads=NUM_THREADS):
        """Delete the jobs in the experiment.

        :param one of azure.mgmt.batchai.models.ExecutionState execution_state:
        delete only jobs with this exeuction state. If None, delete jobs
        regardless of execution state.
        :param List<str> job_names: List of names of jobs to resubmit. If none,
        all failed jobs in the experiment are resubmitted.
        :param str job_name_regex: regex used with re.match to match names of
        jobs to delete
        :param job_name_regex: [type], optional
        """

        jobs = list(self.client.jobs.list_by_experiment(
            self.resource_group_name, self.workspace_name,
            self.experiment_name))
        if execution_state:
            jobs = [j for j in jobs if j.execution_state == execution_state]
        if job_name_regex:
            jobs = [j for j in jobs if re.match(job_name_regex, j.name)]
        if job_names:
            jobs = [j for j in jobs if j.name in job_names]
        if len(jobs) == 0:
            print("There are no jobs to delete in the experiment {0}.".format(
                self.experiment_name))
            return
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for job in jobs:
                future = executor.submit(self._delete_job, job.name)
                futures.append(future)
            for future in concurrent.futures.as_completed(futures):
                future.result()
        print(str(len(jobs)) + " jobs in experiment {0} were deleted.".format(
            self.experiment_name))

    def _delete_job(self, job_name):
        """Delete a job.
        """
        polling = CustomPolling()  # Poll once per second for results
        self.client.jobs.delete(
            self.resource_group_name, self.workspace_name,
            self.experiment_name, job_name,
            polling=polling).result()
        print("Deleted Job: {}".format(job_name))


class CustomPolling(ARMPolling):
    def _delay(self):
        if self._response is None:
            return
        time.sleep(1)  # Override default polling, poll once per second
