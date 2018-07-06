# Introduction

Azure CLI 2.0 allows you to create and manage Batch AI resources - create/delete Batch AI file servers and clusters,
submit and monitor training jobs.

This recipe shows how to create a GPU cluster with Infiniband enabled, run and monitor training job using Microsoft Cognitive Toolkit.

The training script [TrainResNet_CIFAR10_Distributed.py](https://github.com/Microsoft/CNTK/blob/master/Examples/Image/Classification/ResNet/Python/TrainResNet_CIFAR10_Distributed.py) is available at Official CNTK GitHub page. This script trains ResNet on CIFAR-10 database.

## The Workflow

To train a model, you typically need to perform the following steps:

* Create a GPU or CPU Batch AI cluster to run the job;
* Make the training data and training scripts available on the cluster nodes;
* Submit the training job and obtain its logs and/or generated models;
* Delete the cluster or resize it to have zero node to not pay for compute resources when you are not using them.

In this recipe, we will:
* Create a two node GPU cluster (with `Standard_NC24R` VM size) with name `nc24r`;
* Create a new storage account, Azure File Share with two folders `logs` and `scripts` to store jobs output and training scripts;
* Deploy the training script to the storage account before job submission;
* During the job submission we will instruct Batch AI to mount the Azure File Share and Azure Blob Container on the
cluster's node and make them available as regular file system at `$AZ_BATCHAI_JOB_MOUNT_ROOT/logs`, `$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts`, where `AZ_BATCHAI_JOB_MOUNT_ROOT` is an environment
variable set by Batch AI for the job.
* Will use job preparation task to execute CIFAR-10 data preparation and Intel MPI installation script (jobprep_cntk_distributed_ib.sh). The data set will be downloaded and processed on compute nodes locally (under AZ_BATCHAI_JOB_TEMP directory);
* Job preparation will install IntelMPI binary to enable Infiniband job
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

The following command will create a two node GPU cluster (VM size is `Standard_NC24R`) as the operation system image. Please be sure you have enough core quota to create at least two `STANDARD_NC24r` nodes. If you like to conduct performance comparasion with TCP network, you can create the cluster with VM size `STANDARD_NC24` that does not support Infiniband.

```azurecli test
az batchai cluster create -n nc24r -g batchai.recipes -w recipe_workspace -s Standard_NC24R -t 2 --generate-ssh-keys 
```

`--generate-ssh-keys` option tells Azure CLI to generate private and public ssh keys if you have not them already, so
you can ssh to cluster nodes using the ssh key and you current user name. Note. You need to backup ~/.ssh folder to
some permanent storage if you are using Cloud Shell.

Example output:
```json
{
  "allocationState": "resizing",
  "allocationStateTransitionTime": "2018-06-16T01:24:13.629000+00:00",
  "creationTime": "2018-06-16T01:24:13.629000+00:00",
  "currentNodeCount": 0,
  "errors": null,
  "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/clusters/nc24r",
  "name": "nc24r",
  "nodeSetup": null,
  "nodeStateCounts": {
    "idleNodeCount": 0,
    "leavingNodeCount": 0,
    "preparingNodeCount": 0,
    "runningNodeCount": 0,
    "unusableNodeCount": 0
  },
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2018-06-16T01:24:29.948000+00:00",
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
    "adminUserName": "llii",
    "adminUserPassword": null,
    "adminUserSshPublicKey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCxvLtmTxGnZ588ynEondYfm2l1G8pHmrHzNuZcE9OxUvB7xO4bEML0NR4FKenqW8LBaRcIM6IU3NS33SRZ0KPXiEHQcmu9tM9ORSLh9p0qM1yzhsLzR6FR7VpeMM+wJcFnEtca/IXkUxIYNMkCKXWaqGKRcjS/PwqkRwVLs5wgwLQMjUNQnDnpY26Mq30x412eei0XOESK4HVh7O6ulxMQr9yv8hW1EplrGb44BkYbJmDtYVWx43UmtNyIdsqBl+Ng5ZSYcVQzcPtmLdVc5CAm1D0tbvC1GgVmobj0z/AfaK9YrffhFKuHM/Uf3/JPXF1k0yZcE4lqTitvRvYpsPLP"
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
  "vmSize": "STANDARD_NC24r"
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

## Download the Training and Job Preparation Scripts

* Download [TrainResNet_CIFAR10_Distributed.py](https://github.com/Microsoft/CNTK/blob/master/Examples/Image/Classification/ResNet/Python/TrainResNet_CIFAR10_Distributed.py) and its dependencies as well as the job preparation script [jobprep_cntk_distributed_ib.sh](https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python-Distributed-Infiniband/jobprep_cntk_distributed_ib.sh) scripts into the current folder:

For GNU/Linux or Cloud Shell:

```azurecli test
wget https://raw.githubusercontent.com/Microsoft/CNTK/v2.3/Examples/Image/Classification/ResNet/Python/resnet_models.py
wget https://raw.githubusercontent.com/Microsoft/CNTK/v2.3/Examples/Image/Classification/ResNet/Python/TrainResNet_CIFAR10_Distributed.py
wget https://raw.githubusercontent.com/Microsoft/CNTK/v2.3/Examples/Image/Classification/ResNet/Python/TrainResNet_CIFAR10.py
wget https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python-Distributed-Infiniband/jobprep_cntk_distributed_ib.sh
```

## Create Azure File Share and Deploy the Training Script

The following commands will create Azure File Shares `scripts` and `logs` and will copy training script into `cntk`
folder inside of `scripts` share:

```azurecli test
az storage share create -n scripts --account-name <storage account name>
az storage share create -n logs --account-name <storage account name>
az storage directory create -n cntk -s scripts --account-name <storage account name>
az storage file upload -s scripts --source jobprep_cntk_distributed_ib.sh --path cntk --account-name <storage account name> 
az storage file upload -s scripts --source TrainResNet_CIFAR10.py --path cntk --account-name <storage account name> 
az storage file upload -s scripts --source TrainResNet_CIFAR10_Distributed.py --path cntk --account-name <storage account name> 
az storage file upload -s scripts --source resnet_models.py --path cntk --account-name <storage account name> 
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
            "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/cntk/TrainResNet_CIFAR10_Distributed.py",
            "commandLineArgs": "--datadir $AZ_BATCHAI_JOB_TEMP -outputdir $AZ_BATCHAI_OUTPUT_MODEL -n resnet110 -e 5",
            "processCount": 8
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
            "commandLine": "bash $AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/cntk/jobprep_cntk_distributed_ib.sh"
        },
        "containerSettings": {
            "imageSourceRegistry": {
                "image": "batchaitraining/cntk:2.3-gpu-1bitsgd-py36-cuda8-cudnn6-intelmpi"
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
* Will use CNTK docker image `batchaitraining/cntk:2.3-gpu-1bitsgd-py36-cuda8-cudnn6-intelmpi` based on [Dockerfile](https://github.com/Azure/BatchAI/blob/master/recipes/CNTK/CNTK-GPU-Python-Distributed-Infiniband/dockerfile).

## Submit the Job in an Experiment

Use the following command to create a new experiment called ```cntk_experiment``` in the workspace:
```azurecli test
az batchai experiment create -g batchai.recipes -w recipe_workspace -n cntk_experiment
```

Use the following command to submit the job on the cluster:

```azurecli test
wget -O job.json https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python-Distributed-Infiniband/job.json
az batchai job create -c nc24r -n distributed_cntk_python_ib -g batchai.recipes -w recipe_workspace -e cntk_experiment -f job.json --storage-account-name <storage account name>
```

Example output:
```
{
  "caffe2Settings": null,
  "caffeSettings": null,
  "chainerSettings": null,
  "cluster": {
    "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/clusters/nc24r",
    "resourceGroup": "batchai.recipes"
  },
  "cntkSettings": {
    "commandLineArgs": "--datadir $AZ_BATCHAI_JOB_TEMP -outputdir $AZ_BATCHAI_OUTPUT_MODEL -n resnet110 -e 5",
    "configFilePath": null,
    "languageType": "Python",
    "processCount": 8,
    "pythonInterpreterPath": null,
    "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/cntk/TrainResNet_CIFAR10_Distributed.py"
  },
  "constraints": {
    "maxWallClockTime": "7 days, 0:00:00"
  },
  "containerSettings": {
    "imageSourceRegistry": {
      "credentials": null,
      "image": "batchaitraining/cntk:2.3-gpu-1bitsgd-py36-cuda8-cudnn6-intelmpi",
      "serverUrl": null
    },
    "shmSize": null
  },
  "creationTime": "2018-06-18T07:40:23.750000+00:00",
  "customMpiSettings": null,
  "customToolkitSettings": null,
  "environmentVariables": null,
  "executionInfo": {
    "endTime": null,
    "errors": null,
    "exitCode": null,
    "startTime": "2018-06-18T07:40:28.744000+00:00"
  },
  "executionState": "running",
  "executionStateTransitionTime": "2018-06-18T07:40:28.744000+00:00",
  "horovodSettings": null,
  "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/experiments/cntk_experiment/jobs/distributed_cntk_python_ib",
  "inputDirectories": null,
  "jobOutputDirectoryPathSegment": "1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/cntk_experiment/jobs/distributed_cntk_python_ib/10b9f268-5281-4212-9546-7dcb47f7e7bb",
  "jobPreparation": {
    "commandLine": "bash $AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/cntk/jobprep_cntk_distributed_ib.sh"
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
  "name": "distributed_cntk_python_ib",
  "nodeCount": 2,
  "outputDirectories": [
    {
      "id": "MODEL",
      "pathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
      "pathSuffix": null
    }
  ],
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2018-06-18T07:40:24.359000+00:00",
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
az batchai job file stream -j distributed_cntk_python_ib -g batchai.recipes -w recipe_workspace -e cntk_experiment -f stdout.txt
```

Example output: 
```
File found with URL The file "stdout.txt" not found. Waiting for the job to generate it.
File found with URL "https://batchairecipestorage.file.core.windows.net/logs/1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/cntk_experiment/jobs/distributed_cntk_python_ib/10b9f268-5281-4212-9546-7dcb47f7e7bb/stdouterr/stdout.txt?sv=2016-05-31&sr=f&sig=tZ7bDrrI4N4vH9SXt9MwWHo62yV0HCQ2agOZkrrpwvw%3D&se=2018-06-18T08%3A48%3A18Z&sp=rl". Start streaming
Start training: quantize_bit = 32, epochs = 5, distributed_after = 0
Start training: quantize_bit = 32, epochs = 5, distributed_after = 0
Start training: quantize_bit = 32, epochs = 5, distributed_after = 0
Start training: quantize_bit = 32, epochs = 5, distributed_after = 0
Start training: quantize_bit = 32, epochs = 5, distributed_after = 0
Start training: quantize_bit = 32, epochs = 5, distributed_after = 0
Start training: quantize_bit = 32, epochs = 5, distributed_after = 0
Start training: quantize_bit = 32, epochs = 5, distributed_after = 0
Finished Epoch[1 of 5]: [Training] loss = 3.069416 * 50176, metric = 88.99% * 50176 35.819s (1400.8 samples/s);
Finished Epoch[1 of 5]: [Training] loss = 3.069416 * 50176, metric = 88.99% * 50176 35.319s (1420.7 samples/s);
Finished Epoch[1 of 5]: [Training] loss = 3.069416 * 50176, metric = 88.99% * 50176 33.819s (1483.7 samples/s);
Finished Epoch[1 of 5]: [Training] loss = 3.069416 * 50176, metric = 88.99% * 50176 34.819s (1441.1 samples/s);
Finished Epoch[1 of 5]: [Training] loss = 3.069416 * 50176, metric = 88.99% * 50176 32.819s (1528.9 samples/s);
 ...
Finished Evaluation [1]: Minibatch[1-10]: metric = 81.40% * 10000;
```

The streaming is stopped when the job is completed.

You can use the Portal or Azure Storage Explorer to inspect the generated files. To distinguish output
from the different jobs, Batch AI creates an unique folder structure for each of them. You can find the path to the
folder containing the output using `jobOutputDirectoryPathSegment` attribute of the submitted job:

```azurecli test
az batchai job show -n distributed_cntk_python_ib -g batchai.recipes -w recipe_workspace -e cntk_experiment --query jobOutputDirectoryPathSegment
```

Example output:
```
"00000000-0000-0000-0000-000000000000/batchai.recipes/workspaces/recipe_workspace/experiments/cntk_experiment/jobs/distributed_cntk_python_ib/f5f250d8-ec62-4cd3-a080-638b47549a00"
```

# Cleanup Resources

Delete the resource group and all allocated resources with the following command:

```azurecli
az group delete -n batchai.recipes -y
```







