* Introduction

This document describes how to publish your image into Azure Container Registry and configure training jobs to use it.

* Create Azure Container Registry (ARC) and publish your image
Please follow the instructions to [publish docker image using Azure CLI](https://docs.microsoft.com/en-us/azure/container-registry/container-registry-get-started-azure-cli) or [publish docker image using Portal](https://docs.microsoft.com/en-us/azure/container-registry/container-registry-get-started-portal).

* Configure the job to use published container

To use published docker image you need to provide container settings in the job's create parameters like this:

```json
{
    "properties": {
        "containerSettings": {
            "imageSourceRegistry": {
                "serverUrl": "FILL-IN-HERE",
                "image": "FILL-IN-HERE",
                "credentials": {
                    "username": "FILL-IN-HERE",
                    "password": "FILL-IN-HERE"
                }
            }
        },
        "$comment": "the rest of job's parameters"
    }
}
```

Here,
- serverUrl is login server of your ACR;
- image is a fully qualified name of your image in form <login server>/<image name>, e.g. demo.azurecr.io/myimage.
- username is name of ACR user who has pull permissions;
- password is the ACR user's password.

If you want to use KeyVault for storing ACR password, configure your job like this:

```json
{
    "properties": {
        "containerSettings": {
            "imageSourceRegistry": {
                "serverUrl": "FILL-IN-HERE",
                "image": "FILL-IN-HERE",
                "credentials": {
                    "username": "FILL-IN-HERE",
                    "passwordSecretReference": {
                        "sourceVault": {
                            "id": "FILL-IN-HERE"
                        },
                        "secretUrl": "FILL-IN-HERE"
                    }
                }
            }
        },
        "$comment": "the rest of job's parameters"
    }
}
```
Here,
- serverUrl is login server of your ACR;
- image is a fully qualified name of your image in form <login server>/<image name>, e.g. demo.azurecr.io/myimage.
- username is user name of ACR user who has pull permissions;
- passwordSecretReference is a reference to KeyVault secret which stores ACR user's password.

Please follow the [following instructions](https://github.com/Azure/BatchAI/blob/master/documentation/using-azure-cli-20.md#using-keyvault-for-storing-secrets) to store the ACR user's
password in KeyVault and give BatchAI access to it.

