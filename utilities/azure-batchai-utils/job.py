from __future__ import print_function

import re
import time

import azure.mgmt.batchai.models as models
import requests
from azure.mgmt.storage import StorageManagementClient
from msrestazure.tools import parse_resource_id

from utilities.cluster import print_cluster_status

POLLING_INTERVAL_SEC = 5


class OutputStreamer:
    """Helper class to stream (tail -f) job's output files."""

    def __init__(self, client, resource_group, workspace_name, experiment_name, 
                 job_name, output_directory_id, file_name):
        self.client = client
        self.resource_group = resource_group
        self.workspace_name = workspace_name
        self.experiment_name = experiment_name
        self.job_name = job_name
        self.output_directory_id = output_directory_id
        self.file_name = file_name
        self.url = None
        self.downloaded = 0
        # if no output_directory_id or file_name specified, the tail call is
        # nope
        if self.output_directory_id is None or self.file_name is None:
            self.tail = lambda: None

    def tail(self):
        if not self.url:
            files = self.client.jobs.list_output_files(
                self.resource_group, self.workspace_name, self.experiment_name, self.job_name,
                models.JobsListOutputFilesOptions(outputdirectoryid=self.output_directory_id))
            if not files:
                return
            else:
                for f in list(files):
                    if f.name == self.file_name:
                        self.url = f.download_url
        if self.url:
            r = requests.get(self.url, headers={
                'Range': 'bytes={0}-'.format(self.downloaded)})
            if int(r.status_code / 100) == 2:
                self.downloaded += len(r.content)
                print(r.content.decode(), end='')


def wait_for_job_completion(client, resource_group, workspace_name, experiment_name, 
                            job_name, cluster_name, output_directory_id=None, file_name=None):
    """
    Waits for job completion and tails a file specified by output_directory_id
    and file_name.
    """
    # Wait for job to start running
    while True:
        cluster = client.clusters.get(resource_group, workspace_name, cluster_name)
        print_cluster_status(cluster)
        job = client.jobs.get(resource_group, workspace_name, experiment_name, job_name)
        print_job_status(job)
        if job.execution_state != models.ExecutionState.queued:
            break
        time.sleep(POLLING_INTERVAL_SEC)

    print('Waiting for job output to become available...')

    # Tail the output file and wait for job to complete
    streamer = OutputStreamer(client, resource_group, workspace_name, experiment_name, 
                              job_name, output_directory_id, file_name)
    while True:
        streamer.tail()
        job = client.jobs.get(resource_group, workspace_name, experiment_name, job_name)
        if job.execution_state in (models.ExecutionState.succeeded, models.ExecutionState.failed):
            break
        time.sleep(1)
    streamer.tail()
    print_job_status(job)


def print_job_status(job):
    failure_message = None
    exit_code = 'None'
    if job.execution_info is not None:
        exit_code = job.execution_info.exit_code
    if job.execution_state == models.ExecutionState.failed:
        for error in job.execution_info.errors:
            failure_message = \
                '\nErrorCode:{0}\nErrorMessage:{1}\n'.format(error.code, error.message)
            if error.details is not None:
                failure_message += 'Details:\n'
                for detail in error.details:
                    failure_message += '{0}:{1}\n'.format(detail.name,
                                                          detail.value)
    print('Job state: {0} ExitCode: {1}'.format(job.execution_state,
                                                exit_code))
    if failure_message:
        print('FailureDetails: {0}'.format(failure_message))


def convert_job_to_jcp(job, client):
    jcp_kwargs = models.JobCreateParameters._attribute_map.keys()
    jcp_dict = {
        kwarg: getattr(job, kwarg)
        for kwarg in jcp_kwargs if hasattr(job, kwarg)
    }
    new_jcp = models.JobCreateParameters(**jcp_dict)
    new_jcp.constraints = None
    for bfs in new_jcp.mount_volumes.azure_blob_file_systems:
        bfs.credentials.account_key = _get_storage_account_key(
            bfs.account_name, client)
    for afs in new_jcp.mount_volumes.azure_file_shares:
        afs.credentials.account_key = _get_storage_account_key(
            afs.account_name, client)
    return new_jcp


def _get_storage_account_key(account_name, client):
    storage_client = StorageManagementClient(
        credentials=client.config.credentials,
        subscription_id=client.config.subscription_id,
        base_url=client.config.base_url)
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


class MetricExtractor:
    """
    Helper class to extract desired metric from job's output files.
    
    output_dir:  job list-file option used to obtain learning log file download URL
    logfile: the name of learning log file
    regex: the regular expression to extract the desired metric from log text
    metric: option to aggregate the desired metric, default is the last occurrence 
    
    """
    def __init__(self, output_dir_id, logfile, regex, calculate_method="last"):
        self.output_dir_id = output_dir_id
        self.logfile = logfile
        self.regex = regex
        self.calculate_method = calculate_method

    def get_metric(self, job_name, resource_group, workspace_name, experiment_name, client):
        files = client.jobs.list_output_files(resource_group, workspace_name, experiment_name, job_name,
                                              models.JobsListOutputFilesOptions(outputdirectoryid=self.output_dir_id))
        val = float("inf")
        for file in list(files):
            if file.name == self.logfile:
                text = ""
                try:
                    r = requests.get(file.download_url, stream=True)
                    for chunk in r.iter_content(chunk_size=512 * 1024):
                        if chunk:  # filter out keep-alive new chunks
                            text += chunk.decode(encoding='UTF-8')
                except Exception as e:
                    print(e)
                vals = re.findall(self.regex, text, re.DOTALL)
                if self.calculate_method is "last":
                    val = float(vals[len(vals) - 1])
                elif self.calculate_method is "mean":
                    val = sum([float(m) for m in vals])/len(vals)
                elif self.calculate_method is "min":
                    val = min([float(m) for m in vals])
                elif self.calculate_method is "max":
                    val = max([float(m) for m in vals])
                break

        return val