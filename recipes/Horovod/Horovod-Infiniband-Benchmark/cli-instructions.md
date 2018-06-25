# Introduction

Azure CLI 2.0 allows you to create and manage Batch AI resources - create/delete Batch AI file servers and clusters,
submit and monitor training jobs.

This recipe shows how to create a GPU cluster, run and monitor training job using Microsoft Cognitive Toolkit.

This recipe shows how to reproduce [Horovod distributed training benchmarks](https://github.com/uber/horovod/blob/master/docs/benchmarks.md) using Azure Batch AI. Official Horovod Benchmark [scripts](https://github.com/alsrgv/benchmarks/tree/master/scripts/tf_cnn_benchmarks) will be used.

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

```azurecli
az storage account create -n <storage account name> --sku Standard_LRS -g batchai.recipes
```

If selected storage account name is not available, the above command will report corresponding error. In this case, choose
other name and retry.

# Data Deployment

## Download the Training Script

* The job preparation script [jobprep_benchmark.sh](https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/Horovod/Horovod-Infiniband-Benchmark/jobprep_benchmark.sh) does the following tasks:
    - Install essential packages for infiniband support
    - Download benchmark sample
    - Install IntelMPI binary
    - Install honovod framework

* Download the script into the current folder:

For GNU/Linux or Cloud Shell:

```azurecli test
wget https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/Horovod/Horovod-Infiniband-Benchmark/jobprep_benchmark.sh
```

## Create Azure File Share and Deploy the Training Script

The following commands will create Azure File Shares `scripts` and `logs` and will copy training script into `horovod`
folder inside of `scripts` share:

```azurecli test
az storage share create -n scripts --account-name <storage account name>
az storage share create -n logs --account-name <storage account name>
az storage directory create -n horovod -s scripts --account-name <storage account name>
az storage file upload -s scripts --source jobprep_benchmark.sh --path horovod --account-name <storage account name> 
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
            "pythonScriptFilePath": "$AZ_BATCHAI_JOB_TEMP/benchmarks/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py",
            "commandLineArgs": "--model resnet101 --batch_size 64 --variable_update horovod"
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
            "commandLine": "bash $AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/horovod/jobprep_benchmark.sh"
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
two Azure File Shares `logs` and `scripts`, and Azure Blob Container `data`. The filesystems are mounted under `AZ_BATCHAI_JOB_MOUNT_ROOT/<relativeMountPath>`;
* `outputDirectories` - collection of output directories which will be created by Batch AI. For each directory, Batch AI will create an environment variable with name `AZ_BATCHAI_OUTPUT_<id>`, where `<id>` is the directory
identifier.
* `<AZURE_BATCHAI_STORAGE_ACCOUNT>` tells that the storage account name will be specified during the job submission
via --storage-account-name parameter or `AZURE_BATCHAI_STORAGE_ACCOUNT` environment variable on your computer.
The job will use official tensorflow docker container.

## Submit the Job in an Experiment

Use the following command to create a new experiment called ```horovod_experiment``` in the workspace:
```azurecli test
az batchai experiment create -g batchai.recipes -w recipe_workspace -n horovod_experiment
```

Use the following command to submit the job on the cluster:

```azurecli test
wget -O job.json https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/Horovod/Horovod-Infiniband-Benchmark/job.json
az batchai job create -c nc24r -n horovod_benchmark -g batchai.recipes -w recipe_workspace -e horovod_experiment -f job.json --storage-account-name <storage account name>
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
  "creationTime": "2018-06-18T08:04:05.046000+00:00",
  "customMpiSettings": null,
  "customToolkitSettings": null,
  "environmentVariables": null,
  "executionInfo": {
    "endTime": null,
    "errors": null,
    "exitCode": null,
    "startTime": "2018-06-18T08:04:06.754000+00:00"
  },
  "executionState": "running",
  "executionStateTransitionTime": "2018-06-18T08:04:06.754000+00:00",
  "horovodSettings": {
    "commandLineArgs": "--model resnet101 --batch_size 64 --variable_update horovod",
    "processCount": 8,
    "pythonInterpreterPath": null,
    "pythonScriptFilePath": "$AZ_BATCHAI_JOB_TEMP/benchmarks/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py"
  },
  "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/experiments/horovod_experiment/jobs/horovod_benchmark",
  "inputDirectories": null,
  "jobOutputDirectoryPathSegment": "1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/horovod_experiment/jobs/horovod_benchmark/2604ec33-d8f0-415b-9ceb-deffa146b496",
  "jobPreparation": {
    "commandLine": "bash $AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/horovod/jobprep_benchmark.sh"
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
  "name": "horovod_benchmark",
  "nodeCount": 2,
  "outputDirectories": null,
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2018-06-18T08:04:05.593000+00:00",
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

The training script is reporting the training progress in `stdout.txt` file inside the standard output directory. You
can monitor the progress using the following command:

```azurecli test
az batchai job file stream -j horovod_benchmark -g batchai.recipes -w recipe_workspace -e horovod_experiment -f stdout.txt
```

Example output: 
```
The file "stdout.txt" not found. Waiting for the job to generate it.
File found with URL File found with URL "https://batchairecipestorage.file.core.windows.net/logs/1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/horovod_experiment/jobs/horovod_benchmark/d4e1a9da-1a63-40aa-b5f0-84678b9b774a/stdouterr/stdout.txt?sv=2016-05-31&sr=f&sig=fd63rsOx0rLLsGJTikVkjZtYylIa80YE4hMDdkFVV%2Bg%3D&se=2018-06-18T09%3A14%3A09Z&sp=rl". Start streaming
TensorFlow:  1.8
TensorFlow:  1.8
Model:       resnet101
Dataset:     imagenet (synthetic)
Model:       resnet101
Dataset:     imagenet (synthetic)
Mode:        training
SingleSess:  False
Batch size:  512 global
             64 per device
Mode:        training
SingleSess:  False
Batch size:  512 global
             64 per device
Num batches: 100Num batches: 100
Num epochs:  0.04
Devices:     ['horovod/gpu:0', 'horovod/gpu:1', 'horovod/gpu:2', 'horovod/gpu:3', 'horovod/gpu:4', 'horovod/gpu:5', 'horovod/gpu:6', 'horovod/gpu:7']
Data format: NCHW
Layout optimizer: False
Num epochs:  0.04
Devices:     ['horovod/gpu:0', 'horovod/gpu:1', 'horovod/gpu:2', 'horovod/gpu:3', 'horovod/gpu:4', 'horovod/gpu:5', 'horovod/gpu:6', 'horovod/gpu:7']
Data format: NCHW
Layout optimizer: False
Optimizer:   sgd
Optimizer:   sgd
Variables:   horovod
==========

...

Step    Img/sec total_loss
1       images/sec: 28.2 +/- 0.0 (jitter = 0.0) 10.050
1       images/sec: 28.2 +/- 0.0 (jitter = 0.0) 10.050
1       images/sec: 28.2 +/- 0.0 (jitter = 0.0) 10.050
1       images/sec: 28.2 +/- 0.0 (jitter = 0.0) 10.050
1       images/sec: 28.2 +/- 0.0 (jitter = 0.0) 10.050
1       images/sec: 28.2 +/- 0.0 (jitter = 0.0) 10.050
1       images/sec: 28.2 +/- 0.0 (jitter = 0.0) 10.050
1       images/sec: 28.2 +/- 0.0 (jitter = 0.0) 10.050
10      images/sec: 28.3 +/- 0.0 (jitter = 0.1) 9.433
10      images/sec: 28.3 +/- 0.0 (jitter = 0.1) 9.433

...

----------------------------------------------------------------
100     images/sec: 28.1 +/- 0.0 (jitter = 0.2) 8.923
----------------------------------------------------------------
total images/sec: 224.96
----------------------------------------------------------------
```

The streaming is stopped when the job is completed.

Alternatively, you can use the Portal or Azure Storage Explorer to inspect the generated files. To distinguish output
from the different jobs, Batch AI creates an unique folder structure for each of them. You can find the path to the
folder containing the output using `jobOutputDirectoryPathSegment` attribute of the submitted job:

```azurecli
az batchai job show -n horovod_benchmark -g batchai.recipes -w recipe_workspace -e horovod_experiment --query jobOutputDirectoryPathSegment
```

Example output:
```
"00000000-0000-0000-0000-000000000000/batchai.recipes/workspaces/recipe_workspace/experiments/horovod_experiment/jobs/horovod_benchmark/d4e1a9da-1a63-40aa-b5f0-84678b9b774a"
```

![Model files in Storage Explorer](./files.png)
# Cleanup Resources

Delete the resource group and all allocated resources with the following command:

```azurecli
az batchai group delete -n batchai.recipes -y
```