# Introduction

Azure CLI 2.0 allows you to create and manage Batch AI resources - create/delete Batch AI file servers and clusters,
submit and monitor training jobs.

This recipe shows how to create a GPU cluster, run and monitor training job using Microsoft Cognitive Toolkit.

The training script [mnist_trainer.py](https://github.com/Azure/BatchAI/blob/master/recipes/PyTorch/PyTorch-GPU-Distributed-Gloo/mnist_trainer.py)
is available at Batch AI page. This script trains convolutional neural network on MNIST database of handwritten digits.

The script is modified from Official Distributed PyTorch [sample](https://github.com/pytorch/examples/blob/master/imagenet/main.py), which is originally implemented for ImageNet dataset.

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
cluster's node and make them available as regular file system at `$AZ_BATCHAI_JOB_MOUNT_ROOT/logs`, `$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts` where `AZ_BATCHAI_JOB_MOUNT_ROOT` is an environment
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

```azurecli
az storage account create -n <storage account name> --sku Standard_LRS -g batchai.recipes
```

If selected storage account name is not available, the above command will report corresponding error. In this case, choose
other name and retry.

# Data Deployment

## Download the Training Script

* Download [mnist_trainer.py](https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/PyTorch/PyTorch-GPU-Distributed-Gloo/mnist_trainer.py) example script into the current folder:

For GNU/Linux or Cloud Shell:

```azurecli test
wget https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/PyTorch/PyTorch-GPU-Distributed-Gloo/mnist_trainer.py
```

## Create Azure File Share and Deploy the Training Script

The following commands will create Azure File Shares `scripts` and `logs` and will copy training script into `pytorch`
folder inside of `scripts` share:

```azurecli test
az storage share create -n scripts --account-name <storage account name>
az storage share create -n logs --account-name <storage account name>
az storage directory create -n pytorch -s scripts --account-name <storage account name>
az storage file upload -s scripts --source mnist_trainer.py --path pytorch --account-name <storage account name> 
```

# Submit Training Job

## Prepare Job Configuration File

Create a training job configuration file `job.json` with the following content:
```json
{
    "$schema": "https://raw.githubusercontent.com/Azure/BatchAI/master/schemas/2018-05-01/job.json",
    "properties": {
        "nodeCount": 2,
        "pyTorchSettings": {
            "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/pytorch/mnist_trainer.py",
            "commandLineArgs": "--epochs 10 --world-size 2 --dist-backend $AZ_BATCHAI_PYTORCH_BACKEND --dist-url $AZ_BATCHAI_PYTORCH_INIT_METHOD --rank $AZ_BATCHAI_TASK_INDEX",
            "communicationBackend": "gloo" 
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
                "image": "pytorch/pytorch:0.4_cuda9_cudnn7"
            }
        }
    }
}
```

This configuration file specifies:
* `nodeCount` - number of nodes required by the job;
* `pyTorchSettings` - tells that the current job needs PyTorch and specifies path the training script and command line arguments.
* `stdOutErrPathPrefix` - path where Batch AI will create directories containing job's logs;
* `mountVolumes` - list of filesystem to be mounted during the job execution. In this case, we are mounting
two Azure File Shares `logs` and `scripts`, and Azure Blob Container `data`. The filesystems are mounted under `AZ_BATCHAI_JOB_MOUNT_ROOT/<relativeMountPath>`;
* `<AZURE_BATCHAI_STORAGE_ACCOUNT>` tells that the storage account name will be specified during the job submission
via --storage-account-name parameter or `AZURE_BATCHAI_STORAGE_ACCOUNT` environment variable on your computer.
* Will use `'Gloo'` as PyTorch distribution backend, and use Batch AI generated `AZ_BATCHAI_PYTORCH_INIT_METHOD` for shared file-system initialization.
* Will use official PyTorch docker image

## Submit the Job in an Experiment

Use the following command to create a new experiment called ```pytorch_experiment``` in the workspace:
```azurecli test
az batchai experiment create -g batchai.recipes -w recipe_workspace -n pytorch_experiment
```

Use the following command to submit the job on the cluster:

```azurecli test
wget -O job.json https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/PyTorch/PyTorch-GPU-Distributed-Gloo/job.json
az batchai job create -c nc6 -n distributed_pytorch -g batchai.recipes -w recipe_workspace -e pytorch_experiment -f job.json --storage-account-name <storage account name>
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
      "image": "pytorch/pytorch:0.4_cuda9_cudnn7",
      "serverUrl": null
    },
    "shmSize": null
  },
  "creationTime": "2018-06-15T18:23:51.413000+00:00",
  "customMpiSettings": null,
  "customToolkitSettings": null,
  "environmentVariables": null,
  "executionInfo": {
    "endTime": null,
    "errors": null,
    "exitCode": null,
    "startTime": "2018-06-15T18:23:54.554000+00:00"
  },
  "executionState": "running",
  "executionStateTransitionTime": "2018-06-15T18:23:54.554000+00:00",
  "horovodSettings": null,
  "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/experiments/pytorch_experiment/jobs/distributed_pytorch",
  "inputDirectories": null,
  "jobOutputDirectoryPathSegment": "1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/pytorch_experiment/jobs/distributed_pytorch/a1c18330-d0ea-4a81-b669-f8bcabfcfdd4",
  "jobPreparation": null,
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
  "name": "distributed_pytorch",
  "nodeCount": 2,
  "outputDirectories": null,
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2018-06-15T18:23:52.106000+00:00",
  "pyTorchSettings": {
    "commandLineArgs": "--epochs 10 --world-size 2 --dist-backend $AZ_BATCHAI_PYTORCH_BACKEND --dist-url $AZ_BATCHAI_PYTORCH_INIT_METHOD --rank $AZ_BATCHAI_TASK_INDEX",
    "communicationBackend": "gloo",
    "processCount": 2,
    "pythonInterpreterPath": null,
    "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/pytorch/mnist_trainer.py"
  },
  "resourceGroup": "batchai.recipes",
  "schedulingPriority": "normal",
  "secrets": null,
  "stdOutErrPathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
  "tensorFlowSettings": null,
  "toolType": "pytorch",
  "type": "Microsoft.BatchAI/workspaces/experiments/jobs"
}
```

# Monitor Job Execution

The training script is reporting the training progress in `stdout-0.txt` file inside the standard output directory. You
can monitor the progress using the following command:

```azurecli test
az batchai job file stream -j distributed_pytorch -g batchai.recipes -w recipe_workspace -e pytorch_experiment -f stdout-0.txt
```

Example output: 
```
Downloading http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz
Downloading http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz
Downloading http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz
Downloading http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz
Processing...
Done!
Epoch: [1][0/469]	Time 0.268 (0.268)	Data 0.210 (0.210)	Loss 2.3154 (2.3154)	Prec@1 14.062 (14.062)	Prec@5 43.750 (43.750)
Epoch: [1][10/469]	Time 0.005 (0.031)	Data 0.000 (0.020)	Loss 2.2998 (2.2987)	Prec@1 9.375 (11.222)	Prec@5 53.125 (53.409)
Epoch: [1][20/469]	Time 0.005 (0.020)	Data 0.000 (0.011)	Loss 2.2641 (2.2900)	Prec@1 14.062 (12.202)	Prec@5 54.688 (54.390)
Epoch: [1][30/469]	Time 0.006 (0.015)	Data 0.000 (0.007)	Loss 2.2345 (2.2768)	Prec@1 17.188 (13.710)	Prec@5 67.188 (57.913)
Epoch: [1][40/469]	Time 0.006 (0.013)	Data 0.000 (0.005)	Loss 2.1721 (2.2640)	Prec@1 21.875 (15.434)	Prec@5 75.000 (59.985)
Epoch: [1][50/469]	Time 0.005 (0.012)	Data 0.000 (0.004)	Loss 2.1794 (2.2491)	Prec@1 23.438 (16.942)	Prec@5 75.000 (62.071)
Epoch: [1][60/469]	Time 0.009 (0.011)	Data 0.000 (0.004)	Loss 2.1391 (2.2300)	Prec@1 21.875 (18.750)	Prec@5 73.438 (63.627)

...
Epoch: [10][450/469]	Time 0.005 (0.007)	Data 0.000 (0.001)	Loss 0.3062 (0.2085)	Prec@1 90.625 (93.805)	Prec@5 100.000 (99.782)
Epoch: [10][460/469]	Time 0.016 (0.007)	Data 0.008 (0.001)	Loss 0.2144 (0.2090)	Prec@1 95.312 (93.804)	Prec@5 100.000 (99.780)
```

The streaming is stopped when the job is completed.

**Note** Execution may take several minutes to complete. Due to a known bug in PyTorch Gloo backend, the job may fail with the following error as [reported](https://github.com/pytorch/pytorch/issues/2530):
```
terminate called after throwing an instance of 'gloo::EnforceNotMet'
  what():  [enforce fail at /pytorch/torch/lib/gloo/gloo/cuda.cu:249] error == cudaSuccess. 29 vs 0. Error at: /pytorch/torch/lib/gloo/gloo/cuda.cu:249: driver shutting down
```


You can also use the Portal or Azure Storage Explorer to inspect the generated files. To distinguish output
from the different jobs, Batch AI creates an unique folder structure for each of them. You can find the path to the
folder containing the output using `jobOutputDirectoryPathSegment` attribute of the submitted job:

```azurecli
az batchai job show -n distributed_pytorch -g batchai.recipes -w recipe_workspace -e pytorch_experiment --query jobOutputDirectoryPathSegment
```

Example output:
```
"00000000-0000-0000-0000-000000000000/batchai.recipes/workspaces/recipe_workspace/experiments/pytorch_experiment/jobs/distributed_pytorch/a1c18330-d0ea-4a81-b669-f8bcabfcfdd4"
```

# Cleanup Resources

Delete the resource group and all allocated resources with the following command:

```azurecli
az batchai group delete -n batchai.recipes -y
```
