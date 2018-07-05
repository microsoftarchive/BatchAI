from __future__ import print_function

import re
import time

import azure.mgmt.batchai.models as models
import requests
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


class MetricExtractor:
    """
    Helper class to extract desired metric from job's output files.
    
    list_option:  job list-file option used to obtain learning log file download URL
    logfile: the name of learning log file
    regex: the regular expression to extract the desired metric from log text
    metric: option to aggregate the desired metric, default is the last occurrence 
    
    """
    def __init__(self, list_option, logfile, regex, metric = "last"):
        self.list_option = list_option
        self.logfile = logfile
        self.regex = regex
        self.metric = metric

    def get_metric(self, job_name, resource_group, workspace_name, experiment_name, client):
        files = client.jobs.list_output_files(resource_group, workspace_name, experiment_name, job_name,
                                              models.JobsListOutputFilesOptions(outputdirectoryid=self.list_option))
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
                if self.metric is "last":
                    val = float(vals[len(vals) - 1])
                elif self.metric is "mean":
                    val = sum([float(m) for m in vals])/len(vals)
                elif self.metric is "min":
                    val = min([float(m) for m in vals])
                elif self.metric is "max":
                    val = max([float(m) for m in vals])
                break

        return val