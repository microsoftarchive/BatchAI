# Introduction

Azure CLI 2.0 allows you to create and manage Batch AI resources - create/delete Batch AI file servers and clusters,
submit and monitor training jobs.

This recipe shows how to create a GPU cluster, run and monitor training job using Microsoft Cognitive Toolkit.

The training script [resnet50_trainer.py](https://raw.githubusercontent.com/caffe2/caffe2/v0.6.0/caffe2/python/examples/resnet50_trainer.py) is available at Official Caffe2 GitHub page. This script trains ResNet on MNIST database of handwritten digits.

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

An Azure resource group is a logical container for deploying and managing Azure resources. The following command will create a new resource group ```batchai.recipes``` in East US location:

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
az storage account create -n <storage account name> --sku Standard_LRS -g batchai.recipes -l eastus
```

If selected storage account name is not available, the above command will report corresponding error. In this case, choose
other name and retry.

# Data Deployment

## Download the Training Script

* Download [resnet50_trainer.py](https://raw.githubusercontent.com/caffe2/caffe2/v0.6.0/caffe2/python/examples/resnet50_trainer.py) example script into the current folder:

For GNU/Linux or Cloud Shell:

```azurecli test
wget https://raw.githubusercontent.com/caffe2/caffe2/v0.6.0/caffe2/python/examples/resnet50_trainer.py
```

## Create Azure File Share and Deploy the Training Script

The following commands will create Azure File Shares `scripts` and `logs` and will copy training script into `caffe2`
folder inside of `scripts` share:

```azurecli test
az storage share create -n scripts --account-name <storage account name>
az storage share create -n logs --account-name <storage account name>
az storage directory create -n caffe2 -s scripts --account-name <storage account name>
az storage file upload -s scripts --source resnet50_trainer.py --path caffe2 --account-name <storage account name> 
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
        "nodeCount": 2,
        "caffe2Settings": {
            "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/caffe2/resnet50_trainer.py",
            "commandLineArgs": "--num_shards 2 --shard_id $AZ_BATCHAI_TASK_INDEX --run_id 0 --epoch_size 2000 --num_epochs 5 --train_data $AZ_BATCHAI_JOB_MOUNT_ROOT/data/mnist_data/mnist_train_lmdb --file_store_path $AZ_BATCHAI_SHARED_JOB_TEMP"
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
                "image": "caffe2ai/caffe2"
            }
        }
    }
}
```

This configuration file specifies:
* `nodeCount` - number of nodes required by the job;
* `caffe2Settings` - tells that the current job needs caffe2 and specifies path the training script and command line arguments.
* `stdOutErrPathPrefix` - path where Batch AI will create directories containing job's logs;
* `mountVolumes` - list of filesystem to be mounted during the job execution. In this case, we are mounting
two Azure File Shares `logs` and `scripts`, and Azure Blob Container `data`. The filesystems are mounted under `AZ_BATCHAI_JOB_MOUNT_ROOT/<relativeMountPath>`;
* `<AZURE_BATCHAI_STORAGE_ACCOUNT>` tells that the storage account name will be specified during the job submission
via --storage-account-name parameter or `AZURE_BATCHAI_STORAGE_ACCOUNT` environment variable on your computer.
* Will use $AZ_BATCHAI_SHARED_JOB_TEMP shared directory created by Batch AI to coordinate execution between nodes.
* For demostration purpose, we will only run 5 epochs with epoch size as 2000.
* Will use official caffe2 docker image.

## Submit the Job in an Experiment

Use the following command to create a new experiment called ```caffe2_experiment``` in the workspace:
```azurecli test
az batchai experiment create -g batchai.recipes -w recipe_workspace -n caffe2_experiment
```

Use the following command to submit the job in the experiment on the cluster:

```azurecli test
wget -O job.json https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/Caffe2/Caffe2-GPU-Distributed/job.json
az batchai job create -n distributed_caffe2 -c nc6 -g batchai.recipes -w recipe_workspace -e caffe2_experiment -f job.json --storage-account-name <storage account name>
```

Example output:
```
{
  "caffe2Settings": {
    "commandLineArgs": "--num_shards 2 --shard_id $AZ_BATCHAI_TASK_INDEX --run_id 0 --epoch_size 2000 --num_epochs 5 --train_data $AZ_BATCHAI_JOB_MOUNT_ROOT/data/mnist_data/mnist_train_lmdb --file_store_path $AZ_BATCHAI_SHARED_JOB_TEMP",
    "pythonInterpreterPath": null,
    "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/caffe2/resnet50_trainer.py"
  },
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
      "image": "caffe2ai/caffe2",
      "serverUrl": null
    },
    "shmSize": null
  },
  "creationTime": "2018-06-12T21:54:23.511000+00:00",
  "customMpiSettings": null,
  "customToolkitSettings": null,
  "environmentVariables": null,
  "executionInfo": {
    "endTime": null,
    "errors": null,
    "exitCode": null,
    "startTime": "2018-06-12T21:54:32.990000+00:00"
  },
  "executionState": "running",
  "executionStateTransitionTime": "2018-06-12T21:54:32.990000+00:00",
  "horovodSettings": null,
  "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/experiments/caffe2_experiment/jobs/distributed_caffe2",
  "inputDirectories": null,
  "jobOutputDirectoryPathSegment": "1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/caffe2_experiment/jobs/distributed_caffe2/716df02b-799a-408f-bde8-17a95c7364a8",
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
  "name": "distributed_caffe2",
  "nodeCount": 2,
  "outputDirectories": null,
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2018-06-12T21:54:32.552000+00:00",
  "pyTorchSettings": null,
  "resourceGroup": "batchai.recipes",
  "schedulingPriority": "normal",
  "secrets": null,
  "stdOutErrPathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
  "tensorFlowSettings": null,
  "toolType": "caffe2",
  "type": "Microsoft.BatchAI/workspaces/experiments/jobs"
}
```

# Monitor Job Execution

The training script is reporting the training progress in `stdout-wk-0.txt` file inside the standard output directory. You
can monitor the progress using the following command:

```azurecli test
az batchai job file stream -j distributed_caffe2 -g batchai.recipes -w recipe_workspace -e caffe2_experiment -f stderr-0.txt
```

Example output: 
```
INFO:data_parallel_model:Parallelizing model for devices: [0]
INFO:data_parallel_model:Create input and model training operators
INFO:data_parallel_model:Model for GPU : 0
INFO:data_parallel_model:Adding gradient operators
INFO:data_parallel_model:Add gradient all-reduces for SyncSGD
WARNING:data_parallel_model:Distributed computed params all-reduce not implemented yet
INFO:data_parallel_model:Post-iteration operators for updating params
INFO:data_parallel_model:Add initial parameter sync
WARNING:data_parallel_model:------- DEPRECATED API, please use data_parallel_model.OptimizeGradientMemory() ----- 
WARNING:memonger:NOTE: Executing memonger to optimize gradient memory
INFO:memonger:Remapping 112 blobs, using 5 shared
INFO:memonger:Memonger memory optimization took 0.0214970111847 secs
INFO:resnet50_trainer:Start iteration 0/62 of epoch 0
INFO:resnet50_trainer:Start iteration 1/62 of epoch 0
INFO:resnet50_trainer:Start iteration 2/62 of epoch 0
INFO:resnet50_trainer:Start iteration 3/62 of epoch 0
...
INFO:resnet50_trainer:Start iteration 61/62 of epoch 4
```

The streaming is stopped when the job is completed.


Alternatively, you can use the Portal or Azure Storage Explorer to inspect the generated files. To distinguish output
from the different jobs, Batch AI creates an unique folder structure for each of them. You can find the path to the
folder containing the output using `jobOutputDirectoryPathSegment` attribute of the submitted job:

```azurecli
az batchai job show -n distributed_caffe2 -g batchai.recipes -g batchai.recipes -w recipe_workspace -e caffe2_experiment --query jobOutputDirectoryPathSegment
```

Example output:
```
"00000000-0000-0000-0000-000000000000/batchai.recipes/workspaces/recipe_workspace/experiments/caffe2_experiment/jobs/distributed_caffe2/724b9b3c-26fb-4d2c-8d68-d3938109d1d9"
```

# Cleanup Resources

Delete the resource group and all allocated resources with the following command:

```azurecli
az batchai group delete -n batchai.recipes -y
```