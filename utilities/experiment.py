from __future__ import print_function

import collections
import concurrent.futures
import hashlib
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import azure.mgmt.batchai.models as models
from msrestazure.azure_exceptions import CloudError
from msrestazure.polling.arm_polling import ARMPolling

from utilities.job import convert_job_to_jcp

NUM_THREADS = 30
RETRY_WAIT_SECS = 5
JOB_NAME_HASH_LENGTH = 16
NUM_RETRIES = 5

JobToSubmit = collections.namedtuple('JobToSubmit', [
    'name',
    'parameters'
])


class ExperimentUtils(object):
    def __init__(self, client, resource_group_name, workspace_name,
                 experiment_name, log_to_stdout=True):
        """
        Create a JobSubmitter object to manage job requests to the
        specified experiment.

        :param client: instance of BatchAIManagementClient
        :param resource_group_name: name of resource group of experiment
        :param workspace_name: name of workspace of experiment
        :param experiment_name: name of the experiment
        """
        self.client = client
        self.resource_group_name = resource_group_name
        self.workspace_name = workspace_name
        self.experiment_name = experiment_name
        self.client.experiments.get(  # Ensure experiment exists
            resource_group_name, workspace_name, experiment_name)
        if log_to_stdout:
            self.log_to_stdout()
        self.logger = logging.getLogger('ExperimentUtils')
        self.logger.info(
            "Initialized JobSubmitter in resource group: {0} | "
            "workspace: {1} | experiment: {2}".format(
                self.resource_group_name, self.workspace_name,
                self.experiment_name
            ))

    def submit_jobs(self, jcp_list, job_name_prefix, max_retries=NUM_RETRIES,
                    num_threads=NUM_THREADS):
        """
        Submit jobs with the JobCreateParameters in jcp_list. Jobs have name
        job_name_prefix with a hash of the JobCreateParameters object appended.

        :param jcp_list: a list of JobCreateParameters objects to submit
        :param job_name_prefix: prefix for job names
        :param max_retries: number of retries if server returns 5xx for
        submission
        :param num_threads: number of threads to use for submission
        :return: a concurrent.futures.Future object. Call .result() on the
        return object to get the list of azure.mgmt.batchai.models.Job submitted
        """
        jobs = [JobToSubmit(
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
        """
        Submits jobs using a thread pool. Returns list of
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
        """
        Submit a job. Returns azure.mgmt.batchai.models.Job object
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
        """
        Generate a hash for the JobCreateParameters object.
        """
        jcp_json_str = json.dumps(
            jcp, default=lambda o: o.__dict__, sort_keys=True)
        hash_str = hashlib.sha1(jcp_json_str.encode()).hexdigest()
        hash_str_substr = hash_str[0:length]
        return hash_str_substr

    def wait_all_jobs(self, job_names=None, on_progress=None, timeout=None):
        """
        Block until all jobs in the experiment are completed (succeeded
        or failed).

        :param job_names: names of jobs to wait for. If None, wait until all
        jobs in experiment are completed.
        :param on_progress: a function that wait_all_jobs will call every 10
        secs with list of azure.mgmt.batchai.models.Job, representing current
        state of jobs
        :param timeout: number of seconds to wait before unblocking
        :return: list of completed Jobs
        """

        jobs = list(self.client.jobs.list_by_experiment(
            self.resource_group_name, self.workspace_name,
            self.experiment_name))
        if job_names:
            jobs = [j for j in jobs if j.name in job_names]
        start = time.time()
        while self._num_jobs_completed(jobs) != len(jobs):
            print("{0}/{1} jobs completed ({2} succeeded, {3} failed)".format(
                self._num_jobs_completed(jobs), len(jobs),
                self._num_jobs_in_state(jobs, models.ExecutionState.succeeded),
                self._num_jobs_in_state(jobs, models.ExecutionState.failed)),
                end='')
            sys.stdout.flush()
            for _ in range(15):
                print('.', end='')
                sys.stdout.flush()
                time.sleep(3)
                if timeout and time.time() - start > timeout:
                    return jobs
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

    def resubmit_failed_jobs(self, job_names=None, max_retries=NUM_RETRIES,
                             num_threads=NUM_THREADS):
        """
        Resubmit the failed jobs in an experiment.

        :param job_names: names of jobs to resubmit. If None, all jobs will
        be resubmitted.
        :param max_retries: number of retries if server returns 5xx for
        submission
        :param num_threads: number of threads to use for submission
        :return: list of Jobs that were resubmitted
        """
        all_jobs = list(self.client.jobs.list_by_experiment(
            self.resource_group_name, self.workspace_name,
            self.experiment_name))
        if job_names:
            all_jobs = [j for j in all_jobs if j.name in job_names]
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
            JobToSubmit(
                name=job.name, parameters=convert_job_to_jcp(job, self.client))
            for job in failed_jobs
        ]
        resubmitted_jobs = self._submit_jobs_threadpool(
            jobs_to_submit, max_retries, num_threads)
        return resubmitted_jobs

    def get_metrics_for_jobs(self, jobs, metric_extractor):
        """
        Gets the metrics for a collection of jobs in the experiment.

        :param jobs: a collection of azure.mgmt.batchai.models.Job objects
        :param metric_extractor: an instance of utilities.job.MetricExtractor
        :return: a list of dictionaries with keys "job_name" (the name of the
        job), "job" (the Job object), "metric_value" (the extracted value of
        the metric).
        """
        self.wait_all_jobs(job_names=[j.name for j in jobs])
        job_results = []
        for idx, job in enumerate(jobs):
            metric = metric_extractor.get_metric(job.name,
                                                 self.resource_group_name,
                                                 self.workspace_name,
                                                 self.experiment_name,
                                                 self.client)
            job_results.append({
                "job_name": job.name,
                "job": job,
                "metric_value": metric
            })
        return job_results

    def delete_jobs_in_experiment(self, execution_state=None, job_names=None,
                                  num_threads=NUM_THREADS):
        """
        Delete the jobs in the experiment.

        :param execution_state: one of
        azure.mgmt.batchai.models.ExecutionState. Delete only jobs with this
        execution state. If None, delete jobs regardless of execution state.
        :param job_names: List of names of jobs to resubmit. If none, all
        failed jobs in the experiment are resubmitted.
        :param job_name_regex: regex used with re.match to match names of jobs
        to delete
        :param num_threads: number of threads to use for deletion.
        :return: None
        """
        jobs = list(self.client.jobs.list_by_experiment(
            self.resource_group_name, self.workspace_name,
            self.experiment_name))
        if execution_state:
            jobs = [j for j in jobs if j.execution_state == execution_state]
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
        self.logger.info(str(len(jobs)) + " jobs in experiment {0} were "
                         "deleted.".format(self.experiment_name))

    def _delete_job(self, job_name):
        """
        Delete a job.

        :param job_name: name of job to delete
        :return: None
        """
        polling = CustomPolling()  # Poll once per second for results
        self.client.jobs.delete(
            self.resource_group_name, self.workspace_name,
            self.experiment_name, job_name,
            polling=polling).result()
        self.logger.info("Deleted Job: {}".format(job_name))

    def log_to_stdout(self):
        """
        Make ExperimentUtils instance log to stdout.

        :return: None
        """
        logger = logging.getLogger('ExperimentUtils')
        logger.setLevel(logging.INFO)
        logger.handlers = [logging.StreamHandler(sys.stdout)]


class CustomPolling(ARMPolling):
    def _delay(self):
        if self._response is None:
            return
        time.sleep(1)  # Override default polling, poll once per second
