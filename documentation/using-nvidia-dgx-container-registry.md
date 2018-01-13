# Introduction

This document explains how to use docker images published at NVIDIA DGX Container Registry to run training jobs on Batch AI
service.

You can use this instructions to configure your own jobs or to update [existing recipes](/recipes) to run jobs on these
images.

Known limitations:
- Batch AI currently doesn't support running distributed CNTK jobs on `nvcr.io/nvidia/cntk:17.*` images;
- Caffe2 recipe in this repo is compatible only with `nvcr.io/nvidia/caffe2:17.10`;
- `nvcr.io/partners/chainer:4.0.0b1` doesn't support distributed training and cannot be used with the distributed chainer
recipe from this repo.

## Create NVIDIA GPU Cloud Account

You need to have a NVIDIA GPU Cloud account in order to use images from DXG Container Registry. If you have no account yet,
please sign up for the service at https://ngc.nvidia.com/signup.

## Find Required Docker Image

You can find a list of available docker images at https://ngc.nvidia.com/registry. Select required image and get its
fully qualified docker image name (for example, `nvcr.io/nvidia/caffe:17.12` for caffe image). You will provide this name
as `image` parameter value and `nvcr.io` as the server URL in container settings.

## Obtain NVIDIA GPU Cloud API key

To use docker images published at NVIDIA DGX Container Registry you need to obtain and provide Batch AI with your API
key.

You can obtain an API key by following the these steps:

1. Login to https://ngc.nvidia.com/registry;
2. Click "Get API Key" button at the top left corner;
3. Generate an API Key by clicking "Generate API Key" button and confirming the action;
4. Copy generated API key.

## Configure Job to Use Required Image and Credential

There are two ways to specify API key:
1. You can provide API key value directly as a password in job configuration (`job.json` for CLI or 
`JobCreateParameter` for SDKs);
2. You can store API key in Azure Key Vault and use key vault reference in job parameters as described
[here](/documentation/using-azure-cli-20.md#using-keyvault-for-storing-secrets).

The following sections demonstrate how to use these approaches using Azure CLI 2.0 and python.
   
### Provide API Key Directly Using Azure CLI 2.0

Here is an example of specifying container settings in `job.json` for running a job in a container with `tensorflow:17.10`
image: 

```json
{
    "properties": {
        "containerSettings": {
            "imageSourceRegistry": {
                "image": "nvcr.io/nvidia/tensorflow:17.10",
                "serverUrl": "nvcr.io",
                "credentials": {
                    "username": "$oauthtoken",
                    "password": "<Your API Key>"
                }
            }
        },
        ... rest of job's parameters ...
    }
}
```

### Provide API Key Directly Using Python

1. Add `container_registry` section into you configuration.json file as
```json
{
    "container_registry" : {
        "user": "$oauthtoken",
        "password": "<Your API Key>"
    },
    ... rest of configuration ...
}
```

2. Configure container settings in `JobCreateParameters` in the following way:

```python
parameters = models.job_create_parameters.JobCreateParameters(
    container_settings=models.ContainerSettings(
         models.ImageSourceRegistry(
             server_url='nvcr.io',
             image='nvcr.io/nvidia/tensorflow:17.10',
             credentials=models.PrivateRegistryCredentials(
                 username=cfg.container_registry_user,
                 password=cfg.container_registry_password))),
    # rest of the parameters
)
```

### Provide API Key via Azure KeyVault Using Azure CLI 2.0

1. Store your API Key in Azure KeyVault using Azure portal or by following these
[instructions](/documentation/using-azure-cli-20.md#using-keyvault-for-storing-secrets).
2. Use secret reference in container settings as shown below:

```json
{
    "properties": {
        "containerSettings": {
            "imageSourceRegistry": {
                "serverUrl": "nvcr.io",
                "image": "nvcr.io/nvidia/tensorflow:17.10",
                "credentials": {
                    "username": "$oauthtoken",
                    "passwordSecretReference": {
                        "sourceVault": {
                            "id": "/subscriptions/<Your Subscription ID>/resourceGroups/<KeyVault Resource Group>/providers/Microsoft.KeyVault/vaults/<Key Vault Name>"
                        },
                        "secretUrl": "https://<KeyVault Name>.vault.azure.net/secrets/<Secret Name>"
                    }
                }
            }
        },
        ... rest of job's parameters ...
    }
}
````

### Provide API Key via Azure KeyVault Using Python

1. Store your API Key in Azure KeyVault using Azure portal or by following these
[instructions](/documentation/using-azure-cli-20.md#using-keyvault-for-storing-secrets).
2. Add KeyVault id and secret url into your configuration.json file as:
```json
{
    "keyvault_id": "/subscriptions/<Your Subscription ID>/resourceGroups/<KeyVault Resource Group>/providers/Microsoft.KeyVault/vaults/<Key Vault Name>",
    "container_registry" : {
        "user": "$oauthtoken",
        "secret_url": "https://<KeyVault Name>.vault.azure.net/secrets/<Secret Name>"
    },
    ... rest of configuration ...
}
```
3. Configure container settings in `JobCreateParameters` in the following way:

```python
parameters = models.job_create_parameters.JobCreateParameters(
    container_settings=models.ContainerSettings(
         models.ImageSourceRegistry(
             server_url='nvcr.io',
             image='nvcr.io/nvidia/tensorflow:17.10',
             credentials=models.PrivateRegistryCredentials(
                 username=cfg.container_registry_user,
                 password_secret_reference=models.KeyVaultSecretReference(
                     source_vault=models.ResourceId(cfg.keyvault_id),
                     secret_url=cfg.container_registry_secret_url)))),
    # rest of the parameters
)
```