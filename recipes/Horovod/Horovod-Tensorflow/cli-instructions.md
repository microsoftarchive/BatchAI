# Introduction

Azure CLI 2.0 allows you to create and manage Batch AI resources - create/delete Batch AI file servers and clusters,
submit and monitor training jobs.

This recipe shows how to create a GPU cluster, run and monitor training job using Microsoft Cognitive Toolkit.

The training script [tensorflow_mnist.py](https://raw.githubusercontent.com/uber/horovod/v0.9.10/examples/tensorflow_mnist.py) is available at Official Horovod GitHub page. This script trains convolutional neural network on MNIST database of handwritten digits.

## The Workflow

To train a model, you typically need to perform the following steps:

* Create a GPU or CPU Batch AI cluster to run the job;
* Make the training data and training scripts available on the cluster nodes;
* Submit the training job and obtain its logs and/or generated models;
* Delete the cluster or resize it to have zero node to not pay for compute resources when you are not using them.

In this recipe, we will:
* Create a two node GPU cluster (with `Standard_NC6` VM size) with name `nc6`;
* Create a new storage account, Azure File Share with two folders `logs` and `scripts` to store jobs output and training scripts, and Azure Blob Contaier `data` to store training data;
* Deploy the training script and the training data to the storage account before job submission;
* During the job submission we will instruct Batch AI to mount the Azure File Share and Azure Blob Container on the
cluster's node and make them available as regular file system at `$AZ_BATCHAI_JOB_MOUNT_ROOT/logs`, `$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts`, where `AZ_BATCHAI_JOB_MOUNT_ROOT` is an environment variable set by Batch AI for the job.
* We will monitor the job execution by streaming its standard output;
* After the job completion, we will inspect its output and generated models;
* At the end, we will cleanup all allocated resources.

# Prerequisites

* Azure subscription - If you don't have an Azure subscription, create a [free account](https://azure.microsoft.com/free/?WT.mc_id=A261C142F)
before you begin.
* Access to Azure CLI 2.0. You can either use Azure CLI 2.0 available in [Cloud Shell](https://docs.microsoft.com/en-us/azure/cloud-shell/overview)
or install and configure it locally using the [following instructions](/documentation/using-azure-cli-20.md).

# Cloud Shell Only

If you are using Cloud Shell, please change the working directory to `/usr/$USER/clouddrive` because your home directory has no empty space:

```azurecli
cd /usr/$USER/clouddrive
```

# Create a Resource Group

An Azure resource group is a logical container for deploying and managing Azure resources. The following command will
create a new resource group ```batchai.recipes``` in East US location:

```azurecli test
az group create -n batchai.recipes -l eastus
```

# Create a Batch AI Workspace

The following command will create a new workspace ```recipe_workspace``` in East US location:

```azurecli test
az batchai workspace create -g batchai.recipes -n recipe_workspace -l eastus
```

# Create GPU cluster

The following command will create a two node GPU cluster (VM size is Standard_NC6) using Ubuntu as the operation system image.

```azurecli test
az batchai cluster create -n nc6 -g batchai.recipes -w recipe_workspace -s Standard_NC6 -t 2 --generate-ssh-keys 
```

`--generate-ssh-keys` option tells Azure CLI to generate private and public ssh keys if you have not them already, so
you can ssh to cluster nodes using the ssh key and you current user name. Note. You need to backup ~/.ssh folder to
some permanent storage if you are using Cloud Shell.

Example output:
```json
{
  "allocationState": "steady",
  "allocationStateTransitionTime": "2018-06-12T21:25:07.039000+00:00",
  "creationTime": "2018-06-12T21:25:07.039000+00:00",
  "currentNodeCount": 2,
  "errors": null,
  "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/clusters/nc6",
  "name": "nc6",
  "nodeSetup": null,
  "nodeStateCounts": {
    "idleNodeCount": 2,
    "leavingNodeCount": 0,
    "preparingNodeCount": 0,
    "runningNodeCount": 0,
    "unusableNodeCount": 0
  },
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2018-06-12T21:25:23.591000+00:00",
  "resourceGroup": "batchai.recipes",
  "scaleSettings": {
    "autoScale": null,
    "manual": {
      "nodeDeallocationOption": "requeue",
      "targetNodeCount": 2
    }
  },
  "subnet": null,
  "type": "Microsoft.BatchAI/workspaces/clusters",
  "userAccountSettings": {
    "adminUserName": "recipeuser",
    "adminUserPassword": null,
    "adminUserSshPublicKey": "<YOUR SSH PUBLIC KEY HERE>"
  },
  "virtualMachineConfiguration": {
    "imageReference": {
      "offer": "UbuntuServer",
      "publisher": "Canonical",
      "sku": "16.04-LTS",
      "version": "latest",
      "virtualMachineImageId": null
    }
  },
  "vmPriority": "dedicated",
  "vmSize": "STANDARD_NC6"
}
```

# Create a Storage Account

Create a new storage account with an unique name in the same region where you are going to create Batch AI cluster and run
the job. Node, each storage account must have an unique name.

```azurecli test
az storage account create -n <storage account name> --sku Standard_LRS -g batchai.recipes
```

If selected storage account name is not available, the above command will report corresponding error. In this case, choose
other name and retry.

# Data Deployment

## Download the Training Script

* Download [tensorflow_mnist.py](https://raw.githubusercontent.com/uber/horovod/v0.9.10/examples/tensorflow_mnist.py) example script into the current folder:

For GNU/Linux or Cloud Shell:

```azurecli test
wget https://raw.githubusercontent.com/uber/horovod/v0.9.10/examples/tensorflow_mnist.py
```

## Create Azure File Share and Deploy the Training Script

The following commands will create Azure File Shares `scripts` and `logs` and will copy training script into `horovod`
folder inside of `scripts` share:

```azurecli test
az storage share create -n scripts --account-name <storage account name>
az storage share create -n logs --account-name <storage account name>
az storage directory create -n horovod -s scripts --account-name <storage account name>
az storage file upload -s scripts --source tensorflow_mnist.py --path horovod --account-name <storage account name> 
```

# Submit Training Job

## Prepare Job Configuration File

Create a training job configuration file `job.json` with the following content:
```json
{
    "$schema": "https://raw.githubusercontent.com/Azure/BatchAI/master/schemas/2018-05-01/job.json",
    "properties": {
        "nodeCount": 2,
        "horovodSettings": {
            "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/horovod/tensorflow_mnist.py"
        },
        "stdOutErrPathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
        "mountVolumes": {
            "azureFileShares": [
                {
                    "azureFileUrl": "https://<AZURE_BATCHAI_STORAGE_ACCOUNT>.file.core.windows.net/logs",
                    "relativeMountPath": "logs"
                },
                {
                    "azureFileUrl": "https://<AZURE_BATCHAI_STORAGE_ACCOUNT>.file.core.windows.net/scripts",
                    "relativeMountPath": "scripts"
                }
            ]
        },
        "jobPreparation": {
          "commandLine": "apt update; apt install mpi-default-dev mpi-default-bin -y; pip install horovod"
        },
        "containerSettings": {
            "imageSourceRegistry": {
                "image": "tensorflow/tensorflow:1.8.0-gpu"
            }
        }
    }
}
```

This configuration file specifies:
* `nodeCount` - number of nodes required by the job;
* `horovodSettings` - tells that the current job needs horovod and specifies path the training script.
* Horovod framework will be installed by job preparation command line;
* `stdOutErrPathPrefix` - path where Batch AI will create directories containing job's logs;
* `mountVolumes` - list of filesystem to be mounted during the job execution. In this case, we are mounting
two Azure File Shares `logs` and `scripts`. The filesystems are mounted under `AZ_BATCHAI_JOB_MOUNT_ROOT/<relativeMountPath>`;
* `<AZURE_BATCHAI_STORAGE_ACCOUNT>` tells that the storage account name will be specified during the job submission
via --storage-account-name parameter or `AZURE_BATCHAI_STORAGE_ACCOUNT` environment variable on your computer.
* The job will use official tensorflow docker container.

## Submit the Job in an Experiment

Use the following command to create a new experiment called ```horovod_experiment``` in the workspace:
```azurecli test
az batchai experiment create -g batchai.recipes -w recipe_workspace -n horovod_experiment
```

Use the following command to submit the job on the cluster:

```azurecli test
wget -O job.json https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/Horovod/Horovod-Tensorflow/job.json
az batchai job create -c nc6 -n horovod_tensorflow -g batchai.recipes -w recipe_workspace -e horovod_experiment -f job.json --storage-account-name <storage account name>
```

Example output:
```
{
  "caffe2Settings": null,
  "caffeSettings": null,
  "chainerSettings": null,
  "cluster": {
    "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/clusters/nc6",
    "resourceGroup": "batchai.recipes"
  },
  "cntkSettings": null,
  "constraints": {
    "maxWallClockTime": "7 days, 0:00:00"
  },
  "containerSettings": {
    "imageSourceRegistry": {
      "credentials": null,
      "image": "tensorflow/tensorflow:1.8.0-gpu",
      "serverUrl": null
    },
    "shmSize": null
  },
  "creationTime": "2018-06-15T21:43:10.435000+00:00",
  "customMpiSettings": null,
  "customToolkitSettings": null,
  "environmentVariables": null,
  "executionInfo": {
    "endTime": null,
    "errors": null,
    "exitCode": null,
    "startTime": "2018-06-15T21:43:12.424000+00:00"
  },
  "executionState": "running",
  "executionStateTransitionTime": "2018-06-15T21:43:12.424000+00:00",
  "horovodSettings": {
    "commandLineArgs": null,
    "processCount": 2,
    "pythonInterpreterPath": null,
    "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/horovod/tensorflow_mnist.py"
  },
  "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/experiments/horovod_experiment/jobs/horovod_tensorflow",
  "inputDirectories": null,
  "jobOutputDirectoryPathSegment": "1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/horovod_experiment/jobs/horovod_tensorflow/286a5edb-7970-4824-8828-af7725806238",
  "jobPreparation": {
    "commandLine": "apt update; apt install mpi-default-dev mpi-default-bin -y; pip install horovod"
  },
  "mountVolumes": {
    "azureBlobFileSystems": null,
    "azureFileShares": [
      {
        "accountName": "batchairecipestorage",
        "azureFileUrl": "https://batchairecipestorage.file.core.windows.net/logs",
        "credentials": {
          "accountKey": null,
          "accountKeySecretReference": null
        },
        "directoryMode": "0777",
        "fileMode": "0777",
        "relativeMountPath": "logs"
      },
      {
        "accountName": "batchairecipestorage",
        "azureFileUrl": "https://batchairecipestorage.file.core.windows.net/scripts",
        "credentials": {
          "accountKey": null,
          "accountKeySecretReference": null
        },
        "directoryMode": "0777",
        "fileMode": "0777",
        "relativeMountPath": "scripts"
      }
    ],
    "fileServers": null,
    "unmanagedFileSystems": null
  },
  "name": "horovod_tensorflow",
  "nodeCount": 2,
  "outputDirectories": [
    {
      "id": "MODEL",
      "pathPrefix": "$AZ_BATCHAI_MOUNT_ROOT/external",
      "pathSuffix": "Models"
    }
  ],
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2018-06-15T21:43:10.982000+00:00",
  "pyTorchSettings": null,
  "resourceGroup": "batchai.recipes",
  "schedulingPriority": "normal",
  "secrets": null,
  "stdOutErrPathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
  "tensorFlowSettings": null,
  "toolType": "horovod",
  "type": "Microsoft.BatchAI/workspaces/experiments/jobs"
}
```

# Monitor Job Execution

The training script is reporting the training progress in `stderr.txt` file inside the standard output directory. You
can monitor the progress using the following command:

```azurecli test
az batchai job file stream -j horovod_tensorflow -g batchai.recipes -w recipe_workspace -e horovod_experiment -f stderr.txt
```

Example output: 
```
File found with URL File found with URL File found with URL "https://batchairecipestorage.file.core.windows.net/logs/1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/horovod_experiment/jobs/horovod_tensorflow/763f90ec-5423-4755-ad8f-d5a3c9a11ad8/stdouterr/stderr.txt?sv=2016-05-31&sr=f&sig=h99pUIF5SaHaDV09uwmOqwgXytkzmb49m%2BN2tarR1PI%3D&se=2018-06-15T22%3A57%3A57Z&sp=rl". Start streaming
Warning: Permanently added '[10.0.0.4]:23' (ECDSA) to the list of known hosts.

...

INFO:tensorflow:Running local_init_op.
INFO:tensorflow:Done running local_init_op.
INFO:tensorflow:Running local_init_op.
INFO:tensorflow:Done running local_init_op.
INFO:tensorflow:loss = 2.3063743, step = 0
INFO:tensorflow:loss = 2.3266027, step = 0
[703fdf7724b749f28027a4f58028cba1000001:01206] 1 more process has sent help message help-mpi-btl-base.txt / btl:no-nics
[703fdf7724b749f28027a4f58028cba1000001:01206] Set MCA parameter "orte_base_help_aggregate" to 0 to see all help / error messages
INFO:tensorflow:loss = 2.311664, step = 10 (1.476 sec)
INFO:tensorflow:loss = 2.291174, step = 10 (1.476 sec)
INFO:tensorflow:loss = 2.2436697, step = 20 (1.232 sec)
INFO:tensorflow:loss = 2.239246, step = 20 (1.232 sec)
INFO:tensorflow:loss = 2.1557152, step = 30 (1.243 sec)
INFO:tensorflow:loss = 2.1417964, step = 30 (1.243 sec)
INFO:tensorflow:loss = 1.6510586, step = 40 (1.487 sec)
INFO:tensorflow:loss = 1.7157543, step = 40 (1.488 sec)
INFO:tensorflow:loss = 1.8626596, step = 50 (1.267 sec)
INFO:tensorflow:loss = 1.6565758, step = 50 (1.268 sec)
INFO:tensorflow:loss = 1.3022013, step = 60 (1.442 sec)
INFO:tensorflow:loss = 1.3969034, step = 60 (1.441 sec)
INFO:tensorflow:loss = 0.7551861, step = 70 (1.201 sec)
INFO:tensorflow:loss = 0.7433001, step = 70 (1.201 sec)
INFO:tensorflow:loss = 1.452353, step = 80 (1.253 sec)
INFO:tensorflow:loss = 1.5320896, step = 80 (1.253 sec)
INFO:tensorflow:loss = 0.41028553, step = 90 (1.611 sec)
INFO:tensorflow:loss = 0.4954698, step = 90 (1.612 sec)
```

The streaming is stopped when the job is completed.

Alternatively, you can use the Portal or Azure Storage Explorer to inspect the generated files. To distinguish output
from the different jobs, Batch AI creates an unique folder structure for each of them. You can find the path to the
folder containing the output using `jobOutputDirectoryPathSegment` attribute of the submitted job:

```azurecli test
az batchai job show -n horovod_tensorflow -g batchai.recipes -w recipe_workspace -e horovod_experiment --query jobOutputDirectoryPathSegment
```

Example output:
```
"00000000-0000-0000-0000-000000000000/batchai.recipes/workspaces/recipe_workspace/experiments/horovod_experiment/jobs/horovod_tensorflow/763f90ec-5423-4755-ad8f-d5a3c9a11ad8"
```

# Cleanup Resources

Delete the resource group and all allocated resources with the following command:

```azurecli
az group delete -n batchai.recipes -y
```
