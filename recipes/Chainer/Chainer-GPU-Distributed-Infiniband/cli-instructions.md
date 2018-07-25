# Introduction

Azure CLI 2.0 allows you to create and manage Batch AI resources - create/delete Batch AI file servers and clusters,
submit and monitor training jobs.

This recipe shows how to create a GPU cluster, run and monitor training job using Microsoft Cognitive Toolkit.

The training script [train_mnist.py](https://raw.githubusercontent.com/chainer/chainermn/v1.3.0/examples/mnist/train_mnist.py) is available at Official Chainer GitHub page. This script trains convolutional neural network on MNIST database of handwritten digits.

## The Workflow

To train a model, you typically need to perform the following steps:

* Create a GPU or CPU Batch AI cluster to run the job;
* Make the training data and training scripts available on the cluster nodes;
* Submit the training job and obtain its logs and/or generated models;
* Delete the cluster or resize it to have zero node to not pay for compute resources when you are not using them.

In this recipe, we will:
* Create a two node GPU cluster (with `Standard_NC24r` VM size) with name `nc6r`;
* Create a new storage account, Azure File Share with two folders `logs` and `scripts` to store jobs output and training scripts;
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

# Create GPU cluster with Infiniband

The following command will create a two node GPU cluster (VM size is `Standard_NC24R`) as the operation system image. Please be sure you have enough core quota to create at least two `STANDARD_NC24r` nodes. If you like to conduct performance comparasion with TCP network, you can create the cluster with VM size `STANDARD_NC24` that does not support Infiniband.

```azurecli test
az batchai cluster create -n nc24r -g batchai.recipes -w recipe_workspace -s Standard_NC24r -t 2 --generate-ssh-keys 
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
az storage account create -n <storage account name> --sku Standard_LRS -g batchai.recipes -l eastus
```

If selected storage account name is not available, the above command will report corresponding error. In this case, choose
other name and retry.

# Data Deployment

## Download the Training Script and Job Preparation Scripts

* Download [train_mnist.py](https://raw.githubusercontent.com/chainer/chainermn/v1.3.0/examples/mnist/train_mnist.py) example script as the job preparation script [jobprep.sh](https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/Chainer/Chainer-GPU-Distributed-Infiniband/jobprep.sh) scripts into the current folder:

For GNU/Linux or Cloud Shell:

```azurecli test
wget https://raw.githubusercontent.com/chainer/chainermn/v1.3.0/examples/mnist/train_mnist.py
wget https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/Chainer/Chainer-GPU-Distributed-Infiniband/jobprep.sh
```

## Create Azure File Share and Deploy the Scripts

The following commands will create Azure File Shares `scripts` and `logs` and will copy training script into `chainer`
folder inside of `scripts` share:

```azurecli test
az storage share create -n scripts --account-name <storage account name>
az storage share create -n logs --account-name <storage account name>
az storage directory create -n chainer -s scripts --account-name <storage account name>
az storage file upload -s scripts --source train_mnist.py --path chainer --account-name <storage account name> 
az storage file upload -s scripts --source jobprep.sh --path chainer --account-name <storage account name> 
```
# Submit Training Job

## Prepare Job Configuration File

Create a training job configuration file `job.json` with the following content:
```json
{
    "$schema": "https://raw.githubusercontent.com/Azure/BatchAI/master/schemas/2018-05-01/job.json",
    "properties": {
        "nodeCount": 2,
        "chainerSettings": {
            "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/chainer/train_mnist.py",
            "commandLineArgs": "-g --communicator non_cuda_aware -o $AZ_BATCHAI_OUTPUT_MODEL",
             "processCount": 8
        },
        "jobPreparation": {
            "commandLine": "bash $AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/chainer/jobprep.sh"
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
        "outputDirectories": [{
            "id": "MODEL",
            "pathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs"
        }],
        "containerSettings": {
            "imageSourceRegistry": {
                "image": "batchaitraining/chainermn:IntelMPI"
            }
        }
    }
}
```

This configuration file specifies:
* `nodeCount` - number of nodes required by the job;
* `chainerSettings` - tells that the current job needs Chainer and specifies path the training script and command line arguments.
* `stdOutErrPathPrefix` - path where Batch AI will create directories containing job's logs;
* `mountVolumes` - list of filesystem to be mounted during the job execution. In this case, we are mounting
two Azure File Shares `logs` and `scripts`. The filesystems are mounted under `AZ_BATCHAI_JOB_MOUNT_ROOT/<relativeMountPath>`;
* `outputDirectories` - collection of output directories which will be created by Batch AI. For each directory, Batch AI will create an environment variable with name `AZ_BATCHAI_OUTPUT_<id>`, where `<id>` is the directory
identifier.
* `<AZURE_BATCHAI_STORAGE_ACCOUNT>` tells that the storage account name will be specified during the job submission
via --storage-account-name parameter or `AZURE_BATCHAI_STORAGE_ACCOUNT` environment variable on your computer.
* Will use chainer docker image `batchaitraining/chainermn:IntelMPI` that is build based on [dockerfile](https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/Chainer/Chainer-GPU-Distributed-Infiniband/dockerfile).

## Submit the Job in an Experiment

Use the following command to create a new experiment called ```chainer_experiment``` in the workspace:
```azurecli test
az batchai experiment create -g batchai.recipes -w recipe_workspace -n chainer_experiment
```
Use the following command to submit the job on the cluster:

```azurecli test
wget -O job.json https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/Chainer/Chainer-GPU-Distributed-Infiniband/job.json
az batchai job create -n distributed_chainer_ib -c nc24r -g batchai.recipes -w recipe_workspace -e chainer_experiment -f job.json --storage-account-name <storage account name>
```

Example output:
```
{
  "caffe2Settings": null,
  "caffeSettings": null,
  "chainerSettings": {
    "commandLineArgs": "-g --communicator non_cuda_aware -o $AZ_BATCHAI_OUTPUT_MODEL",
    "processCount": 8,
    "pythonInterpreterPath": null,
    "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/chainer/train_mnist.py"
  },
  "cluster": {
    "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/clusters/nc24r",
    "resourceGroup": "batchai.recipes"
  },
  "cntkSettings": null,
  "constraints": {
    "maxWallClockTime": "7 days, 0:00:00"
  },
  "containerSettings": {
    "imageSourceRegistry": {
      "credentials": null,
      "image": "batchaitraining/chainermn:IntelMPI",
      "serverUrl": null
    },
    "shmSize": null
  },
  "creationTime": "2018-07-25T22:34:40.276000+00:00",
  "customMpiSettings": null,
  "customToolkitSettings": null,
  "environmentVariables": null,
  "executionInfo": {
    "endTime": null,
    "errors": null,
    "exitCode": null,
    "startTime": "2018-07-25T22:34:42.376000+00:00"
  },
  "executionState": "running",
  "executionStateTransitionTime": "2018-07-25T22:34:42.376000+00:00",
  "horovodSettings": null,
  "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/experiments/chainer_experiment/jobs/distributed_chainer_ib",
  "inputDirectories": null,
  "jobOutputDirectoryPathSegment": "1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/chainer_experiment/jobs/distributed_chainer_ib/a724b55b-734b-4e77-8525-0be2e0e7917f",
  "jobPreparation": {
    "commandLine": "bash $AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/chainer/jobprep.sh"
  },
  "mountVolumes": {
    "azureBlobFileSystems": null,
    "azureFileShares": [
      {
        "accountName": "stgtest725",
        "azureFileUrl": "https://stgtest725.file.core.windows.net/logs",
        "credentials": {
          "accountKey": null,
          "accountKeySecretReference": null
        },
        "directoryMode": "0777",
        "fileMode": "0777",
        "relativeMountPath": "logs"
      },
      {
        "accountName": "stgtest725",
        "azureFileUrl": "https://stgtest725.file.core.windows.net/scripts",
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
  "name": "distributed_chainer_ib",
  "nodeCount": 2,
  "outputDirectories": [
    {
      "id": "MODEL",
      "pathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
      "pathSuffix": null
    }
  ],
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2018-07-25T22:34:41.183000+00:00",
  "pyTorchSettings": null,
  "resourceGroup": "batchai.recipes",
  "schedulingPriority": "normal",
  "secrets": null,
  "stdOutErrPathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
  "tensorFlowSettings": null,
  "toolType": "chainer",
  "type": "Microsoft.BatchAI/workspaces/experiments/jobs"
}
```

# Monitor Job Execution

The training script is reporting the training progress in `stdout.txt` file inside the standard output directory. You
can monitor the progress using the following command:

```azurecli test
az batchai job file stream -j distributed_chainer_ib -g batchai.recipes -w recipe_workspace -e chainer_experiment  -f stdout.txt
```

Example output: 
```
==========================================
Num process (COMM_WORLD): 8
Using GPUs
Using non_cuda_aware communicator
Num unit: 1000
Num Minibatch-size: 100
Num epoch: 20
==========================================
epoch       main/loss   validation/main/loss  main/accuracy  validation/main/accuracy  elapsed_time
1           0.386137    0.152809              0.8932         0.953269                  9.24535
2           0.120125    0.102408              0.961867       0.968558                  10.8825
3           0.0727884   0.0761316             0.979467       0.976442                  12.5349
4           0.0492472   0.0752163             0.984534       0.977885                  14.2147
5           0.0340649   0.0659149             0.9888         0.979231                  15.9121
6           0.0225881   0.0595835             0.992933       0.980673                  17.6099
7           0.0152206   0.0601706             0.9952         0.982404                  19.3009
8           0.0090835   0.0636856             0.998133       0.981923                  21.0552
9           0.00588576  0.0594042             0.9992         0.98375                   22.8301
10          0.00626196  0.0597588             0.998267       0.982404                  24.6368
11          0.00344498  0.0695266             0.999333       0.981058                  26.3752
12          0.00267228  0.0626356             0.999733       0.982788                  28.0243
13          0.00241359  0.0644145             0.9996         0.983173                  29.7124
14          0.00109171  0.0611127             0.999867       0.984135                  31.4842
15          0.000508859  0.0630337             1              0.984135                  33.218
16          0.000391975  0.063621              1              0.984038                  34.942
17          0.000279589  0.064658              1              0.984038                  36.7087
18          0.000284265  0.0657457             1              0.983942                  38.9672
19          0.000230257  0.0662985             1              0.983558                  40.7048
20          0.000203201  0.0668609             1              0.983942                  42.4551
```

The streaming is stopped when the job is completed.

# Inspect Generated Model Files

The job stores the generated model files in the output directory with id = `MODEL`, you can list this files and
get download URLs using the following command:

```azurecli
az batchai job file list -j distributed_chainer -g batchai.recipes -w recipe_workspace -e chainer_experiment  -g batchai.recipes -d MODEL
```

Example output:
```
[
  {
    "contentLength": 2575,
    "downloadUrl": "https://stgtest725.file.core.windows.net/logs/1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/chainer_experiment/jobs/distributed_chainer_ib/a724b55b-734b-4e77-8525-0be2e0e7917f/outputs/cg.dot?sv=2016-05-31&sr=f&sig=GHUvSgOf1FdqB6Qf9ae%2BMQSN32UGsUTVREKQi%2Foy9xw%3D&se=2018-07-25T23%3A42%3A34Z&sp=rl",
    "fileType": "file",
    "lastModified": "2018-07-25T22:39:12+00:00",
    "name": "cg.dot"
  },
  {
    "contentLength": 5902,
    "downloadUrl": "https://stgtest725.file.core.windows.net/logs/1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/chainer_experiment/jobs/distributed_chainer_ib/a724b55b-734b-4e77-8525-0be2e0e7917f/outputs/log?sv=2016-05-31&sr=f&sig=NuMUKxfujmOIWrycTCYmq0LgtbLhxy4IlH02BWEVphg%3D&se=2018-07-25T23%3A42%3A34Z&sp=rl",
    "fileType": "file",
    "lastModified": "2018-07-25T22:39:48+00:00",
    "name": "log"
  }
]
```

Alternatively, you can use the Portal or Azure Storage Explorer to inspect the generated files. To distinguish output
from the different jobs, Batch AI creates an unique folder structure for each of them. You can find the path to the
folder containing the output using `jobOutputDirectoryPathSegment` attribute of the submitted job:

```azurecli test
az batchai job show -n distributed_chainer_ib -g batchai.recipes -w recipe_workspace -e chainer_experiment --query jobOutputDirectoryPathSegment
```

Example output:
```
"00000000-0000-0000-0000-000000000000/batchai.recipes/workspaces/recipe_workspace/experiments/chainer_experiment/jobs/distributed_chainer_ib/b64115e9-1e02-4006-b812-eec14cd08b92"
```

Delete the resource group and all allocated resources with the following command:

```azurecli
az group delete -n batchai.recipes -y
```