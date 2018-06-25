# Introduction

Azure CLI 2.0 allows you to create and manage Batch AI resources - create/delete Batch AI file servers and clusters,
submit and monitor training jobs.

This recipe shows how to create a GPU cluster, run and monitor training job using Microsoft Cognitive Toolkit.

The training script [ConvNet_CIFAR10_DataAug_Distributed.py](https://github.com/Azure/BatchAI/blob/master/recipes/CNTK/CNTK-GPU-Python-Distributed/ConvNet_CIFAR10_DataAug_Distributed.py)
is available at Batch AI GitHub page. This script trains CNN on CIFAR-10 database.


## The Workflow

To train a model, you typically need to perform the following steps:

* Create a GPU or CPU Batch AI cluster to run the job;
* Make the training data and training scripts available on the cluster nodes;
* Submit the training job and obtain its logs and/or generated models;
* Delete the cluster or resize it to have zero node to not pay for compute resources when you are not using them.

In this recipe, we will:
* Create a two node GPU cluster (with `Standard_NC6` VM size) with name `nc6`;
* Create a new storage account, Azure File Share with two folders `logs` and `scripts` to store jobs output and training scripts;
* Deploy the training script to the storage account before job submission;
* During the job submission we will instruct Batch AI to mount the Azure File Share and Azure Blob Container on the
cluster's node and make them available as regular file system at `$AZ_BATCHAI_JOB_MOUNT_ROOT/logs`, `$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts`, where `AZ_BATCHAI_JOB_MOUNT_ROOT` is an environment
variable set by Batch AI for the job.
* Will use job preparation task to execute CIFAR-10 data preparation script (CIFAR-10_data_prepare.sh). The data set will be downloaded and processed on compute nodes locally (under AZ_BATCHAI_JOB_TEMP directory);
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

```azurecli
az storage account create -n <storage account name> --sku Standard_LRS -g batchai.recipes
```

If selected storage account name is not available, the above command will report corresponding error. In this case, choose
other name and retry.

# Data Deployment

## Download the Training and Job Preparation Scripts

* Download [ConvNet_CIFAR10_DataAug_Distributed.py](https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python-Distributed/ConvNet_CIFAR10_DataAug_Distributed.py) and [CIFAR-10_data_prepare.sh](https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python-Distributed/CIFAR-10_data_prepare.sh) scripts into the current folder:

For GNU/Linux or Cloud Shell:

```azurecli test
wget https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python-Distributed/ConvNet_CIFAR10_DataAug_Distributed.py
wget https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python-Distributed/CIFAR-10_data_prepare.sh
```

## Create Azure File Share and Deploy the Training Script

The following commands will create Azure File Shares `scripts` and `logs` and will copy training script into `cntk`
folder inside of `scripts` share:

```azurecli test
az storage share create -n scripts --account-name <storage account name>
az storage share create -n logs --account-name <storage account name>
az storage directory create -n cntk -s scripts --account-name <storage account name>
az storage file upload -s scripts --source CIFAR-10_data_prepare.sh --path cntk --account-name <storage account name> 
az storage file upload -s scripts --source ConvNet_CIFAR10_DataAug_Distributed.py --path cntk --account-name <storage account name> 
```

# Submit Training Job

## Prepare Job Configuration File

Create a training job configuration file `job.json` with the following content:
```json
{
    "$schema": "https://raw.githubusercontent.com/Azure/BatchAI/master/schemas/2018-05-01/job.json",
    "properties": {
        "nodeCount": 2,
        "cntkSettings": {
            "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/cntk/ConvNet_CIFAR10_DataAug_Distributed.py",
            "commandLineArgs": "--datadir $AZ_BATCHAI_JOB_TEMP --outputdir $AZ_BATCHAI_OUTPUT_MODEL -n 5",
            "processCount": 2
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
            ]
        },
        "jobPreparation": {
            "commandLine": "bash $AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/cntk/CIFAR-10_data_prepare.sh"
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
two Azure File Shares `logs` and `scripts`. The filesystems are mounted under
`AZ_BATCHAI_JOB_MOUNT_ROOT/<relativeMountPath>`;
* `<AZURE_BATCHAI_STORAGE_ACCOUNT>` tells that the storage account name will be specified during the job submission via --storage-account-name parameter or `AZURE_BATCHAI_STORAGE_ACCOUNT` environment variable on your computer.
* Will use official CNTK docker image

## Submit the Job in an Experiment

Use the following command to create a new experiment called ```cntk_experiment``` in the workspace:
```azurecli test
az batchai experiment create -g batchai.recipes -w recipe_workspace -n cntk_experiment
```

Use the following command to submit the job on the cluster:

```azurecli test
wget -O job.json https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python-Distributed/job.json
az batchai job create -c nc6 -n distributed_cntk_python -g batchai.recipes -w recipe_workspace -e cntk_experiment -f job.json --storage-account-name <storage account name>
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
    "commandLineArgs": "--datadir $AZ_BATCHAI_JOB_TEMP --outputdir $AZ_BATCHAI_OUTPUT_MODEL -n 5",
    "configFilePath": null,
    "languageType": "Python",
    "processCount": 2,
    "pythonInterpreterPath": null,
    "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/cntk/ConvNet_CIFAR10_DataAug_Distributed.py"
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
  "creationTime": "2018-06-15T05:22:37.672000+00:00",
  "customMpiSettings": null,
  "customToolkitSettings": null,
  "environmentVariables": null,
  "executionInfo": {
    "endTime": null,
    "errors": null,
    "exitCode": null,
    "startTime": "2018-06-15T05:22:39.093000+00:00"
  },
  "executionState": "running",
  "executionStateTransitionTime": "2018-06-15T05:22:39.093000+00:00",
  "horovodSettings": null,
  "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/experiments/cntk_experiment/jobs/distributed_cntk_python",
  "inputDirectories": null,
  "jobOutputDirectoryPathSegment": "1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/cntk_experiment/jobs/distributed_cntk_python/85e59cef-7e07-4fb3-a708-d9ca6a82982d",
  "jobPreparation": {
    "commandLine": "bash $AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/cntk/CIFAR-10_data_prepare.sh"
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
  "name": "distributed_cntk_python",
  "nodeCount": 2,
  "outputDirectories": [
    {
      "id": "MODEL",
      "pathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
      "pathSuffix": null
    }
  ],
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2018-06-15T05:22:38.858000+00:00",
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

The training script is reporting the training progress in `stdout.txt` file inside the standard output directory. You
can monitor the progress using the following command:

```azurecli test
az batchai job file stream -j distributed_cntk_python -g batchai.recipes -w recipe_workspace -e cntk_experiment -f stdout.txt
```

Example output: 
```
File found with URL "https://batchairecipestorage.file.core.windows.net/logs/1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/cntk_experiment/jobs/distributed_cntk_python/922e7018-4879-4123-930c-5efa89055474/stdouterr/stdout.txt?sv=2016-05-31&sr=f&sig=uoPcHUmSpp7uEsVUEMsRcOpHjENNJ4UHK54LQeEFejI%3D&se=2018-06-15T06%3A40%3A36Z&sp=rl". Start streaming
************************************************************
Welcome to Microsoft Cognitive Toolkit (CNTK) v. 2.5

Activating CNTK environment...

(Use command below to activate manually when needed)

  source "/cntk/activate-cntk"

************************************************************
CNTK is activated.

Please checkout tutorials and examples here:
  /cntk/Tutorials
  /cntk/Examples

To deactivate the environment run

  source /root/anaconda3/bin/deactivate

************************************************************
...
Training 1195594 parameters in 14 parameter tensors.

Training 1195594 parameters in 14 parameter tensors.

PROGRESS: 0.00%
PROGRESS: 0.00%
 Minibatch[   1- 100]: loss = 2.263843 * 6400, metric = 86.41% * 6400;
 Minibatch[   1- 100]: loss = 2.263843 * 6400, metric = 86.41% * 6400;
 Minibatch[ 101- 200]: loss = 2.164102 * 6400, metric = 80.17% * 6400;
 Minibatch[ 101- 200]: loss = 2.164102 * 6400, metric = 80.17% * 6400;
PROGRESS: 0.00%
PROGRESS: 0.00%
 ...
Finished Evaluation [1]: Minibatch[1-157]: metric = 38.14% * 10000;
```

The streaming is stopped when the job is completed.

# Inspect Generated Model Files

The job stores the generated model files in the output directory with id = `MODEL`, you can list this files and
get download URLs using the following command:

```azurecli
az batchai job file list -j distributed_cntk_python -g batchai.recipes -w recipe_workspace -e cntk_experiment -d MODEL
```

Example output:
```
[
  {
    "contentLength": 4807606,
    "downloadUrl": "https://batchairecipestorage.file.core.windows.net/logs/1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/cntk_experiment/jobs/distributed_cntk_python/922e7018-4879-4123-930c-5efa89055474/outputs/ConvNet_CIFAR10_DataAug?sv=2016-05-31&sr=f&sig=yTs221RjmIKA%2FK3b4Trtfvd%2FyWhiFZ8ZdGrUVX%2FtBp4%3D&se=2018-06-15T06%3A49%3A42Z&sp=rl",
    "fileType": "file",
    "lastModified": "2018-06-15T05:41:44+00:00",
    "name": "ConvNet_CIFAR10_DataAug"
  },
  {
    "contentLength": 4785567,
    "downloadUrl": "https://batchairecipestorage.file.core.windows.net/logs/1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/cntk_experiment/jobs/distributed_cntk_python/922e7018-4879-4123-930c-5efa89055474/outputs/ConvNet_CIFAR10_DataAug.ckp?sv=2016-05-31&sr=f&sig=fs9chd9kmtE8e40PCNYU2%2F7FV5qbW6wMftgUBJlSIuk%3D&se=2018-06-15T06%3A49%3A42Z&sp=rl",
    "fileType": "file",
    "lastModified": "2018-06-15T05:41:44+00:00",
    "name": "ConvNet_CIFAR10_DataAug.ckp"
  }
]

```

Alternatively, you can use the Portal or Azure Storage Explorer to inspect the generated files. To distinguish output
from the different jobs, Batch AI creates an unique folder structure for each of them. You can find the path to the
folder containing the output using `jobOutputDirectoryPathSegment` attribute of the submitted job:

```azurecli
az batchai job show -n distributed_cntk_python -g batchai.recipes -w recipe_workspace -e cntk_experiment --query jobOutputDirectoryPathSegment
```

Example output:
```
"00000000-0000-0000-0000-000000000000//batchai.recipes/workspaces/recipe_workspace/experiments/cntk_experiment/jobs/distributed_cntk_python/922e7018-4879-4123-930c-5efa89055474"
```

# Cleanup Resources

Delete the resource group and all allocated resources with the following command:

```azurecli
az batchai group delete -n batchai.recipes -y
```







