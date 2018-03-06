from __future__ import print_function

import json
import os
import time
import zipfile

import azure.mgmt.batchai as training
import azure.mgmt.batchai.models as models
import requests
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient 

POLLING_INTERVAL_SEC = 5


def encode(value):
    if isinstance(value, type('str')):
        return value
    return value.encode('utf-8')


class Configuration:
    """Configuration for recipes and notebooks"""

    def __init__(self, file_name):
        if not os.path.exists(file_name):
            raise ValueError('Cannot find configuration file "{0}"'.
                             format(file_name))

        with open(file_name, 'r') as f:
            conf = json.load(f)

        try:
            self.subscription_id = encode(conf['subscription_id'])
            self.aad_client_id = encode(conf['aad_client_id'])
            self.aad_secret_key = encode(conf['aad_secret'])
            self.aad_token_uri = 'https://login.microsoftonline.com/{0}/oauth2/token'.format(encode(conf['aad_tenant']))
            self.location = encode(conf['location'])
            self.url = encode(conf['base_url'])
            self.resource_group = encode(conf['resource_group'])
            self.storage_account_name = encode(conf['storage_account']['name'])
            self.storage_account_key = encode(conf['storage_account']['key'])
            self.admin = encode(conf['admin_user']['name'])
            self.admin_password = conf['admin_user'].get('password', None)
            if self.admin_password:
                self.admin_password = encode(self.admin_password)
            self.admin_ssh_key = conf['admin_user'].get('ssh_public_key', None)
            if self.admin_ssh_key:
                self.admin_ssh_key = encode(self.admin_ssh_key)
            self.container_registry_user = None
            self.container_registry_password = None
            self.container_registry_secret_url = None
            if 'container_registry' in conf:
                self.container_registry_user = conf['container_registry'].get('user', None)
                self.container_registry_password = conf['container_registry'].get('password', None)
                self.container_registry_secret_url = conf['container_registry'].get('secret_url', None)
            if self.container_registry_user:
                self.container_registry_user = encode(self.container_registry_user)
            if self.container_registry_password:
                self.container_registry_password = encode(self.container_registry_password)
            if self.container_registry_secret_url:
                self.container_registry_secret_url = encode(self.container_registry_secret_url)
            self.keyvault_id = conf.get('keyvault_id', None)
            if self.keyvault_id:
                self.keyvault_id = encode(self.keyvault_id)
            if not self.admin_password and not self.admin_ssh_key:
                raise AttributeError(
                    'Please provide admin user password or public ssh key')
        except KeyError as err:
            raise AttributeError(
                'Please provide a value for "{0}" configuration key'.format(
                    err.args[0]))


class OutputStreamer:
    """Helper class to stream (tail -f) job's output files."""

    def __init__(self, client, resource_group, job_name, output_directory_id,
                 file_name):
        self.client = client
        self.resource_group = resource_group
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
                self.resource_group, self.job_name,
                models.JobsListOutputFilesOptions(
                    self.output_directory_id))
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


def create_batchai_client(configuration):
    client = training.BatchAIManagementClient(
			credentials = ServicePrincipalCredentials(client_id=configuration.aad_client_id, secret=configuration.aad_secret_key, token_uri=configuration.aad_token_uri),
			subscription_id = configuration.subscription_id,
			base_url = configuration.url)
    return client


def create_resource_group(configuration):
	client = ResourceManagementClient(
		credentials = ServicePrincipalCredentials(client_id=configuration.aad_client_id, secret=configuration.aad_secret_key, token_uri=configuration.aad_token_uri), 
		subscription_id = configuration.subscription_id, base_url = configuration.url)
	resource = client.resource_groups.create_or_update(configuration.resource_group, {'location': configuration.location})

	
def download_file(sas, destination):
    dir_name = os.path.dirname(destination)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    print('Downloading {0} ...'.format(sas), end='')
    r = requests.get(sas, stream=True)
    with open(destination, 'wb') as f:
        for chunk in r.iter_content(chunk_size=512 * 1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    f.close()
    print('Done')


def print_job_status(job):
    failure_message = None
    exit_code = 'None'
    if job.execution_info is not None:
        exit_code = job.execution_info.exit_code
    if job.execution_state == models.ExecutionState.failed:
        for error in job.execution_info.errors:
            failure_message = \
                '\nErrorCode:{0}\nErrorMessage:{1}\n'. \
                format(error.code,
                       error.message)
            if error.details is not None:
                failure_message += 'Details:\n'
                for detail in error.details:
                    failure_message += '{0}:{1}\n'.format(detail.name,
                                                          detail.value)
    print('Job state: {0} ExitCode: {1}'.format(job.execution_state.name,
                                                exit_code))
    if failure_message:
        print('FailureDetails: {0}'.format(failure_message))


def print_cluster_status(cluster):
    print(
        'Cluster state: {0} Target: {1}; Allocated: {2}; Idle: {3}; '
        'Unusable: {4}; Running: {5}; Preparing: {6}; Leaving: {7}'.format(
            cluster.allocation_state,
            cluster.scale_settings.manual.target_node_count,
            cluster.current_node_count,
            cluster.node_state_counts.idle_node_count,
            cluster.node_state_counts.unusable_node_count,
            cluster.node_state_counts.running_node_count,
            cluster.node_state_counts.preparing_node_count,
			cluster.node_state_counts.leaving_node_count))
    if not cluster.errors:
        return
    for error in cluster.errors:
        print('Cluster error: {0}: {1}'.format(error.code, error.message))
        if error.details:
            print('Details:')
            for detail in error.details:
                print('{0}: {1}'.format(detail.name, detail.value))


def wait_for_job_completion(client, resource_group, job_name, cluster_name,
                            output_directory_id=None, file_name=None):
    """
    Waits for job completion and tails a file specified by output_directory_id
    and file_name.
    """
    # Wait for job to start running
    while True:
        cluster = client.clusters.get(resource_group, cluster_name)
        print_cluster_status(cluster)
        job = client.jobs.get(resource_group, job_name)
        print_job_status(job)
        if job.execution_state != models.ExecutionState.queued:
            break
        time.sleep(POLLING_INTERVAL_SEC)

    print('Waiting for job output to become available...')

    # Tail the output file and wait for job to complete
    streamer = OutputStreamer(client, resource_group, job_name,
                              output_directory_id, file_name)
    while True:
        streamer.tail()
        job = client.jobs.get(resource_group, job_name)
        if job.execution_state == models.ExecutionState.succeeded or job.execution_state == models.ExecutionState.failed:
            break
        time.sleep(1)
    streamer.tail()
    print_job_status(job)

    
def download_and_upload_mnist_dataset_to_blob(blob_service, azure_blob_container_name, 
                                              mnist_dataset_directory):
    """
    Download and Extract MNIST Dataset, then upload to given Azure Blob Container
    """
    mnist_dataset_url = 'https://batchaisamples.blob.core.windows.net/samples/mnist_dataset_full.zip?st=2018-03-04T00%3A21%3A00Z&se=2099-12-31T23%3A59%3A00Z&sp=rl&sv=2017-04-17&sr=b&sig=rrBgTFeIv3bjsyAfh87RoW5i0ay4mMyMEIh2RI45s%2B0%3D'
    
    mnist_files = ['t10k-images-idx3-ubyte.gz', 't10k-labels-idx1-ubyte.gz',
                   'train-images-idx3-ubyte.gz', 'train-labels-idx1-ubyte.gz',
                   'Train-28x28_cntk_text.txt', 'Test-28x28_cntk_text.txt',
                   os.path.join('mnist_train_lmdb','data.mdb'), 
                   os.path.join('mnist_test_lmdb','data.mdb'),
                   os.path.join('mnist_train_lmdb','lock.mdb'), 
                   os.path.join('mnist_test_lmdb','lock.mdb')]
    
    local_dir = 'mnist_dataset_full'

    if any(not os.path.exists(os.path.join(local_dir, f)) for f in mnist_files):
        download_file(mnist_dataset_url, 'mnist_dataset_full.zip')
        print('Extracting MNIST dataset...')
        with zipfile.ZipFile('mnist_dataset_full.zip', 'r') as z:
            z.extractall(local_dir)
    
    print('Uploading MNIST dataset...')
    for f in mnist_files:
        blob_service.create_blob_from_path(azure_blob_container_name, 
                                           mnist_dataset_directory+'/'+f, os.path.join(local_dir, f))

    print('Done')
    
