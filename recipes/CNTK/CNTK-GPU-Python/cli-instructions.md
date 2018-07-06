# Introduction

Azure CLI 2.0 allows you to create and manage Batch AI resources - create/delete Batch AI file servers and clusters,
submit and monitor training jobs.

This recipe shows how to create a GPU cluster, run and monitor training job using Microsoft Cognitive Toolkit.

The training script [ConvNet_MNIST.py](https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python/ConvNet_MNIST.py)
is available at Batch AI GitHub page. This script trains convolutional neural network on MNIST database of handwritten
digits.

We modified the official CNTK example to accept location of the training dataset and the output directory location via
command line arguments. 

## The Workflow

To train a model, you typically need to perform the following steps:

* Create a GPU or CPU Batch AI cluster to run the job;
* Make the training data and training scripts available on the cluster nodes;
* Submit the training job and obtain its logs and/or generated models;
* Delete the cluster or resize it to have zero node to not pay for compute resources when you are not using them.

In this recipe, we will:
* Create a single node GPU cluster (with `Standard_NC6` VM size) with name `nc6`;
* Create a new storage account, Azure File Share with two folders `logs` and `scripts` to store jobs output and training scripts, and Azure Blob Contaier `data` to store training data;
* Deploy the training script and the training data to the storage account before job submission;
* During the job submission we will instruct Batch AI to mount the Azure File Share and Azure Blob Container on the
cluster's node and make them available as regular file system at `$AZ_BATCHAI_JOB_MOUNT_ROOT/logs`, `$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts` and `$AZ_BATCHAI_JOB_MOUNT_ROOT/data`, where `AZ_BATCHAI_JOB_MOUNT_ROOT` is an environment
variable set by Batch AI for the job.
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

The following command will create a single node GPU cluster (VM size is Standard_NC6) using Ubuntu as the operation system image.

```azurecli test
az batchai cluster create -n nc6 -g batchai.recipes -w recipe_workspace -s Standard_NC6 -t 1 --generate-ssh-keys 
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
  "currentNodeCount": 1,
  "errors": null,
  "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/clusters/nc6",
  "name": "nc6",
  "nodeSetup": null,
  "nodeStateCounts": {
    "idleNodeCount": 1,
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
      "targetNodeCount": 1
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

* Download [ConvNet_MNIST.py](https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python/ConvNet_MNIST.py) example script into the current folder:

For GNU/Linux or Cloud Shell:

```azurecli test
wget https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python/ConvNet_MNIST.py
```

## Create Azure File Share and Deploy the Training Script

The following commands will create Azure File Shares `scripts` and `logs` and will copy training script into `cntk`
folder inside of `scripts` share:

```azurecli test
az storage share create -n scripts --account-name <storage account name>
az storage share create -n logs --account-name <storage account name>
az storage directory create -n cntk -s scripts --account-name <storage account name>
az storage file upload -s scripts --source ConvNet_MNIST.py --path cntk --account-name <storage account name> 
```

## Download the Training Data

* Download and extract preprocessed MNIST Database from this [location](https://batchaisamples.blob.core.windows.net/samples/mnist_dataset_full.zip?st=2018-03-04T00%3A21%3A00Z&se=2099-12-31T23%3A59%3A00Z&sp=rl&sv=2017-04-17&sr=b&sig=rrBgTFeIv3bjsyAfh87RoW5i0ay4mMyMEIh2RI45s%2B0%3D)
into the current folder.

For GNU/Linux or Cloud Shell:

```azurecli test
wget "https://batchaisamples.blob.core.windows.net/samples/mnist_dataset_full.zip?st=2018-03-04T00%3A21%3A00Z&se=2099-12-31T23%3A59%3A00Z&sp=rl&sv=2017-04-17&sr=b&sig=rrBgTFeIv3bjsyAfh87RoW5i0ay4mMyMEIh2RI45s%2B0%3D" -O mnist_dataset_full.zip
unzip -o mnist_dataset_full.zip -d mnist_data
```

## Create a Blob Container and Deploy Training Data

The following commands will create Azure Blob Container and will copy training data into `mnist_data` folder:
```azurecli test
az storage container create -n data --account-name <storage account name>
az storage blob upload-batch -s mnist_data --destination data --destination-path mnist_data --account-name <storage account name>
```

# Submit Training Job

## Prepare Job Configuration File

Create a training job configuration file `job.json` with the following content:
```json
{
    "$schema": "https://raw.githubusercontent.com/Azure/BatchAI/master/schemas/2018-05-01/job.json",
    "properties": {
        "nodeCount": 1,
        "cntkSettings": {
            "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/cntk/ConvNet_MNIST.py",
            "commandLineArgs": "$AZ_BATCHAI_JOB_MOUNT_ROOT/data/mnist_data $AZ_BATCHAI_OUTPUT_MODEL"
        },
        "stdOutErrPathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
        "outputDirectories": [{
            "id": "MODEL",
            "pathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs"
        }],
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
            ],
            "azureBlobFileSystems": [
                {
                    "accountName": "<AZURE_BATCHAI_STORAGE_ACCOUNT>",
                    "containerName": "data",
                    "relativeMountPath": "data"
                }
            ]
        },
        "containerSettings": {
            "imageSourceRegistry": {
                "image": "microsoft/cntk:2.5.1-gpu-python2.7-cuda9.0-cudnn7.0"
            }
        }
    }
}
```

This configuration file specifies:
* `nodeCount` - number of nodes required by the job;
* `cntkSettings` - tells that the current job needs CNTK and specifies path the training script and command line
arguments - path to training data and path to where the generated model will be saved. `AZ_BATCHAI_OUTPUT_MODEL`
is an environment variable set by Batch AI based on output directory configuration (see below);
* `stdOutErrPathPrefix` - path where Batch AI will create directories containing job's  logs;
* `outputDirectories` - collection of output directories which will be created by Batch AI. For each directory,
Batch AI will create an environment variable with name `AZ_BATCHAI_OUTPUT_<id>`, where `<id>` is the directory
identifier.
* `mountVolumes` - list of filesystem to be mounted during the job execution. In this case, we are mounting
two Azure File Shares `logs` and `scripts`, and Azure Blob Container `data`. The filesystems are mounted under
`AZ_BATCHAI_JOB_MOUNT_ROOT/<relativeMountPath>`;
* `<AZURE_BATCHAI_STORAGE_ACCOUNT>` tells that the storage account name will be specified during the job submission
via --storage-account-name parameter or `AZURE_BATCHAI_STORAGE_ACCOUNT` environment variable on your computer.
* Will use official CNTK docker image

## Submit the Job in an Experiment

Use the following command to create a new experiment called ```cntk_experiment``` in the workspace:
```azurecli test
az batchai experiment create -g batchai.recipes -w recipe_workspace -n cntk_experiment
```

Use the following command to submit the job on the cluster:

```azurecli test
wget -O job.json https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python/job.json
az batchai job create -c nc6 -n cntk_python -g batchai.recipes -w recipe_workspace -e cntk_experiment -f job.json --storage-account-name <storage account name>
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
  "cntkSettings": {
    "commandLineArgs": "$AZ_BATCHAI_JOB_MOUNT_ROOT/data/mnist_data $AZ_BATCHAI_OUTPUT_MODEL",
    "configFilePath": null,
    "languageType": "Python",
    "processCount": 1,
    "pythonInterpreterPath": null,
    "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/cntk/ConvNet_MNIST.py"
  },
  "constraints": {
    "maxWallClockTime": "7 days, 0:00:00"
  },
  "containerSettings": {
    "imageSourceRegistry": {
      "credentials": null,
      "image": "microsoft/cntk:2.5.1-gpu-python2.7-cuda9.0-cudnn7.0",
      "serverUrl": null
    },
    "shmSize": null
  },
  "creationTime": "2018-06-15T04:10:31.735000+00:00",
  "customMpiSettings": null,
  "customToolkitSettings": null,
  "environmentVariables": null,
  "executionInfo": {
    "endTime": null,
    "errors": null,
    "exitCode": null,
    "startTime": "2018-06-15T04:10:32.780000+00:00"
  },
  "executionState": "running",
  "executionStateTransitionTime": "2018-06-15T04:10:32.780000+00:00",
  "horovodSettings": null,
  "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/experiments/cntk_experiment/jobs/cntk_python",
  "inputDirectories": null,
  "jobOutputDirectoryPathSegment": "1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/cntk_experiment/jobs/cntk_python/f15f27d4-bd1c-4a27-905a-2d6a960c6dad",
  "jobPreparation": null,
  "mountVolumes": {
    "azureBlobFileSystems": [
      {
        "accountName": "batchairecipestorage",
        "containerName": "data",
        "credentials": {
          "accountKey": null,
          "accountKeySecretReference": null
        },
        "mountOptions": null,
        "relativeMountPath": "data"
      }
    ],
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
  "name": "cntk_python",
  "nodeCount": 1,
  "outputDirectories": [
    {
      "id": "MODEL",
      "pathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
      "pathSuffix": null
    }
  ],
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2018-06-15T04:10:32.503000+00:00",
  "pyTorchSettings": null,
  "resourceGroup": "batchai.recipes",
  "schedulingPriority": "normal",
  "secrets": null,
  "stdOutErrPathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
  "tensorFlowSettings": null,
  "toolType": "cntk",
  "type": "Microsoft.BatchAI/workspaces/experiments/jobs"
}
```

# Monitor Job Execution

The training script is reporting the training progress in `stderr.txt` file inside the standard output directory. You
can monitor the progress using the following command:

```azurecli test
az batchai job file stream -j cntk_python -g batchai.recipes -w recipe_workspace -e cntk_experiment -f stderr.txt
```

Example output: 
```
File found with URL "https://batchairecipes.file.core.windows.net/logs/1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/jobs/recipes4/0ac6f05f-82ef-4da5-98c8-7487e8c98cf1/stdouterr/stderr.txt?sv=2016-05-31&sr=f&sig=n86JK9YowV%2BPQ%2BkBzmqr0eud%2FlpRB%2FVu%2FFlcKZx192k%3D&se=2018-04-11T23%3A05%3A54Z&sp=rl". Start streaming
Selected GPU[0] Tesla K80 as the process wide default device.
-------------------------------------------------------------------
Build info: 

		Built time: Jan 31 2018 15:03:41
		Last modified date: Tue Jan 30 03:26:13 2018
		Build type: release
		Build target: GPU
		With 1bit-SGD: no
		With ASGD: yes
		Math lib: mkl
		CUDA version: 9.0.0
		CUDNN version: 7.0.4
		Build Branch: HEAD
		Build SHA1: a70455c7abe76596853f8e6a77a4d6de1e3ba76e
		MPI distribution: Open MPI
		MPI version: 1.10.7
-------------------------------------------------------------------
Training 98778 parameters in 10 parameter tensors.

Learning rate per 1 samples: 0.001
Momentum per 1 samples: 0.0
Finished Epoch[1 of 40]: [Training] loss = 0.405960 * 60000, metric = 13.01% * 60000 21.741s (2759.8 samples/s);
Finished Epoch[2 of 40]: [Training] loss = 0.106030 * 60000, metric = 3.09% * 60000 3.638s (16492.6 samples/s);
Finished Epoch[3 of 40]: [Training] loss = 0.078542 * 60000, metric = 2.32% * 60000 3.477s (17256.3 samples/s);
...
Final Results: Minibatch[1-11]: errs = 0.54% * 10000
```

The streaming is stopped when the job is completed.

# Inspect Generated Model Files

The job stores the generated model files in the output directory with id = `MODEL`, you can list this files and
get download URLs using the following command:

```azurecli
az batchai job file list -j cntk_python -g batchai.recipes -w recipe_workspace -e cntk_experiment -d MODEL
```

Example output:
```
[
  {
    "additionalProperties": {},
    "contentLength": 409456,
    "downloadUrl": "https://<YOUR STORAGE ACCOUNT>.file.core.windows.net/...",
    "isDirectory": false,
    "lastModified": "2018-04-11T22:05:51+00:00",
    "name": "ConvNet_MNIST_0.dnn"
  },
  {
    "additionalProperties": {},
    "contentLength": 409456,
    "downloadUrl": "https://<YOUR STORAGE ACCOUNT>.file.core.windows.net/...",
    "isDirectory": false,
    "lastModified": "2018-04-11T22:05:55+00:00",
    "name": "ConvNet_MNIST_1.dnn"
  },
...

```

Alternatively, you can use the Portal or Azure Storage Explorer to inspect the generated files. To distinguish output
from the different jobs, Batch AI creates an unique folder structure for each of them. You can find the path to the
folder containing the output using `jobOutputDirectoryPathSegment` attribute of the submitted job:

```azurecli test
az batchai job show -n cntk_python -g batchai.recipes -w recipe_workspace -e cntk_experiment --query jobOutputDirectoryPathSegment
```

Example output:
```
"00000000-0000-0000-0000-000000000000/batchai.recipes/jobs/cntk_python/40b3e701-b07a-4b73-b8ad-43fb2914bff8"
```

# Cleanup Resources

Delete the resource group and all allocated resources with the following command:

```azurecli
az group delete -n batchai.recipes -y
```