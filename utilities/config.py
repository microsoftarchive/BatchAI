from __future__ import print_function

import json
import os

import azure.mgmt.batchai as training
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient


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
            self.workspace = encode(conf['workspace'])
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

def create_batchai_client(configuration):
    client = training.BatchAIManagementClient(
        credentials=ServicePrincipalCredentials(client_id=configuration.aad_client_id,
                                                secret=configuration.aad_secret_key,
                                                token_uri=configuration.aad_token_uri),
        subscription_id=configuration.subscription_id,
        base_url=configuration.url)
    return client

def create_resource_group(configuration):
    client = ResourceManagementClient(
        credentials=ServicePrincipalCredentials(client_id=configuration.aad_client_id,
                                                secret=configuration.aad_secret_key,
                                                token_uri=configuration.aad_token_uri),
        subscription_id=configuration.subscription_id, base_url=configuration.url)
    client.resource_groups.create_or_update(configuration.resource_group,
                                            {'location': configuration.location})