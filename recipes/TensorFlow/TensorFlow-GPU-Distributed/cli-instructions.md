# Introduction

Azure CLI 2.0 allows you to create and manage Batch AI resources - create/delete Batch AI file servers and clusters,
submit and monitor training jobs.

This recipe shows how to create a GPU cluster, run and monitor training job using Microsoft Cognitive Toolkit.

This script trains convolutional neural network on MNIST database of handwritten digits.The training script [mnist_replica.py](https://raw.githubusercontent.com/tensorflow/tensorflow/v1.8.0/tensorflow/tools/dist_test/python/mnist_replica.py)
is modified to generate model checkpoints and tensorboard event output files. 

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

* Download [mnist_replica.py](https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/TensorFlow/TensorFlow-GPU-Distributed/mnist_replica.py) example script into the current folder:

For GNU/Linux or Cloud Shell:

```azurecli test
wget https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/TensorFlow/TensorFlow-GPU-Distributed/mnist_replica.py
```

## Create Azure File Share and Deploy the Training Script

The following commands will create Azure File Shares `scripts` and `logs` and will copy training script into `tensorflow`
folder inside of `scripts` share:

```azurecli test
az storage share create -n scripts --account-name <storage account name>
az storage share create -n logs --account-name <storage account name>
az storage directory create -n tensorflow -s scripts --account-name <storage account name>
az storage file upload -s scripts --source mnist_replica.py --path tensorflow --account-name <storage account name> 
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
        "tensorFlowSettings": {
            "parameterServerCount": 1,
            "workerCount": 2,
            "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/tensorflow/mnist_replica.py",
            "masterCommandLineArgs": "--job_name=worker --num_gpus=1 --ps_hosts=$AZ_BATCHAI_PS_HOSTS --worker_hosts=$AZ_BATCHAI_WORKER_HOSTS --train_steps 10000 --checkpoint_dir=$AZ_BATCHAI_OUTPUT_MODEL --log_dir=$AZ_BATCHAI_OUTPUT_TENSORBOARD --task_index=$AZ_BATCHAI_TASK_INDEX --data_dir=$AZ_BATCHAI_INPUT_DATASET",
            "workerCommandLineArgs": "--job_name=worker --num_gpus=1 --ps_hosts=$AZ_BATCHAI_PS_HOSTS --worker_hosts=$AZ_BATCHAI_WORKER_HOSTS --train_steps 10000 --checkpoint_dir=$AZ_BATCHAI_OUTPUT_MODEL --log_dir=$AZ_BATCHAI_OUTPUT_TENSORBOARD --task_index=$AZ_BATCHAI_TASK_INDEX --data_dir=$AZ_BATCHAI_INPUT_DATASET",
            "parameterServerCommandLineArgs": "--job_name=ps --num_gpus=0 --ps_hosts=$AZ_BATCHAI_PS_HOSTS --worker_hosts=$AZ_BATCHAI_WORKER_HOSTS --task_index=$AZ_BATCHAI_TASK_INDEX --data_dir=$AZ_BATCHAI_JOB_MOUNT_ROOT/data/mnist_data"
        },
        "stdOutErrPathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
        "outputDirectories": [
            {
                "id": "MODEL",
                "pathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
                "pathSuffix": "Models"
            },
            {
                "id": "TENSORBOARD",
                "pathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
                "pathSuffix": "Logs"
            },
        ],
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
                "image": "tensorflow/tensorflow:1.8.0-gpu"
            }
        }
    }
}
```

This configuration file specifies:
* `nodeCount` - number of nodes required by the job;
* `tensorFlowSettings` - tells that the current job needs Tensoeflow and specifies path the training script and command line arguments.
* `stdOutErrPathPrefix` - path where Batch AI will create directories containing job's logs;
* `outputDirectories` - collection of output directories which will be created by Batch AI. For each directory,
Batch AI will create an environment variable with name `AZ_BATCHAI_OUTPUT_<id>`, where `<id>` is the directory
* `mountVolumes` - list of filesystem to be mounted during the job execution. In this case, we are mounting
two Azure File Shares `logs` and `scripts`, and Azure Blob Container `data`. The filesystems are mounted under `AZ_BATCHAI_JOB_MOUNT_ROOT/<relativeMountPath>`;
* `<AZURE_BATCHAI_STORAGE_ACCOUNT>` tells that the storage account name will be specified during the job submission
via --storage-account-name parameter or `AZURE_BATCHAI_STORAGE_ACCOUNT` environment variable on your computer.
* Will use official Tensorflow docker image

## Submit the Job in an Experiment

Use the following command to create a new experiment called ```tensorflow_experiment``` in the workspace:
```azurecli test
az batchai experiment create -g batchai.recipes -w recipe_workspace -n tensorflow_experiment
```

Use the following command to submit the job on the cluster:

```azurecli test
wget -O job.json https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/TensorFlow/TensorFlow-GPU-Distributed/job.json
az batchai job create -c nc6 -n distributed_tensorflow -g batchai.recipes -w recipe_workspace -e tensorflow_experiment -f job.json --storage-account-name <storage account name>
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
  "creationTime": "2018-06-15T06:27:49.692000+00:00",
  "customMpiSettings": null,
  "customToolkitSettings": null,
  "environmentVariables": null,
  "executionInfo": {
    "endTime": null,
    "errors": null,
    "exitCode": null,
    "startTime": "2018-06-15T06:27:52.821000+00:00"
  },
  "executionState": "running",
  "executionStateTransitionTime": "2018-06-15T06:27:52.821000+00:00",
  "horovodSettings": null,
  "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/batchai.recipes/providers/Microsoft.BatchAI/workspaces/recipe_workspace/experiments/tensorflow_experiment/jobs/distributed_tensorflow",
  "inputDirectories": null,
  "jobOutputDirectoryPathSegment": "1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/tensorflow_experiment/jobs/distributed_tensorflow/991b4f26-5411-4a43-a735-c2905f2be29a",
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
  "name": "distributed_tensorflow",
  "nodeCount": 2,
  "outputDirectories": [
      {
          "id": "MODEL",
          "pathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
          "pathSuffix": "Models"
      },
      {
          "id": "TENSORBOARD",
          "pathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
          "pathSuffix": "Logs"
      },
  ],
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2018-06-15T06:27:50.661000+00:00",
  "pyTorchSettings": null,
  "resourceGroup": "batchai.recipes",
  "schedulingPriority": "normal",
  "secrets": null,
  "stdOutErrPathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
  "tensorFlowSettings": {
    "masterCommandLineArgs": "--job_name=worker --num_gpus=1 --ps_hosts=$AZ_BATCHAI_PS_HOSTS --worker_hosts=$AZ_BATCHAI_WORKER_HOSTS --train_steps 10000 --checkpoint_dir=$AZ_BATCHAI_OUTPUT_MODEL --log_dir=$AZ_BATCHAI_OUTPUT_TENSORBOARD --task_index=$AZ_BATCHAI_TASK_INDEX --data_dir=$AZ_BATCHAI_INPUT_DATASET",
    "workerCommandLineArgs": "--job_name=worker --num_gpus=1 --ps_hosts=$AZ_BATCHAI_PS_HOSTS --worker_hosts=$AZ_BATCHAI_WORKER_HOSTS --train_steps 10000 --checkpoint_dir=$AZ_BATCHAI_OUTPUT_MODEL --log_dir=$AZ_BATCHAI_OUTPUT_TENSORBOARD --task_index=$AZ_BATCHAI_TASK_INDEX --data_dir=$AZ_BATCHAI_INPUT_DATASET",
    "parameterServerCommandLineArgs": "--job_name=ps --num_gpus=0 --ps_hosts=$AZ_BATCHAI_PS_HOSTS --worker_hosts=$AZ_BATCHAI_WORKER_HOSTS --task_index=$AZ_BATCHAI_TASK_INDEX --data_dir=$AZ_BATCHAI_JOB_MOUNT_ROOT/data/mnist_data"
    "parameterServerCount": 1,
    "pythonInterpreterPath": null,
    "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/tensorflow/mnist_replica.py",
    "workerCount": 2
  },
  "toolType": "tensorflow",
  "type": "Microsoft.BatchAI/workspaces/experiments/jobs"
}
```

# Monitor Job Execution

The training script is reporting the training progress in `stdout-wk-0.txt` file inside the standard output directory. You
can monitor the progress using the following command:

```azurecli test
az batchai job file stream -j distributed_tensorflow -g batchai.recipes -w recipe_workspace -e tensorflow_experiment -f stdout-wk-0.txt
```

Example output: 
```
The file "stdout-wk-0.txt" not found. Waiting for the job to generate it.
File found with URL "https://batchairecipestorage.file.core.windows.net/logs/1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/tensorflow_experiment/jobs/distributed_tensorflow/991b4f26-5411-4a43-a735-c2905f2be29a/stdouterr/stdout-wk-0.txt?sv=2016-05-31&sr=f&sig=uBfUfE071t9ZfzuvsWnxC%2BUS0ek6cfrT9pWiFKgpVgw%3D&se=2018-06-15T07%3A29%3A46Z&sp=rl". Start streaming
Successfully downloaded train-images-idx3-ubyte.gz 9912422 bytes.
Extracting train-images-idx3-ubyte.gz
Successfully downloaded train-labels-idx1-ubyte.gz 28881 bytes.
Extracting train-labels-idx1-ubyte.gz
Successfully downloaded t10k-images-idx3-ubyte.gz 1648877 bytes.
Extracting t10k-images-idx3-ubyte.gz
Successfully downloaded t10k-labels-idx1-ubyte.gz 4542 bytes.
Extracting t10k-labels-idx1-ubyte.gz
job name = worker
task index = 0
Worker 0: Initializing session...
Worker 0: Session initialization complete.
Training begins @ 1529044193.429204
1529044193.720650: Worker 0: training step 1 done (global step: 0)
1529044193.724921: Worker 0: training step 2 done (global step: 1)
1529044193.728340: Worker 0: training step 3 done (global step: 2)
1529044193.732600: Worker 0: training step 4 done (global step: 3)
1529044193.737079: Worker 0: training step 5 done (global step: 4)
1529044193.740693: Worker 0: training step 6 done (global step: 5)
1529044193.744786: Worker 0: training step 7 done (global step: 6)
1529044193.748403: Worker 0: training step 8 done (global step: 7)
...
1529044194.317815: Worker 0: training step 146 done (global step: 199)
1529044194.321525: Worker 0: training step 147 done (global step: 201)
Training ends @ 1529044194.321580
Training elapsed time: 0.892376 s
After 200 training step(s), validation cross entropy = 1367.12
```

The streaming is stopped when the job is completed.

Inspect Generated Model Files

The job stores the generated model files in the output directory with id = `MODEL`, you can list this files and get download URLs using the following command:

```azurecli
az batchai job file list -j distributed_tensorflow -g batchai.recipes -w recipe_workspace -e cntk_experiment -d MODEL
```

You can view the output tensorboard log file via the same way but with output directory id = `TENSORBOARD`

```azurecli
az batchai job file list -j distributed_tensorflow -g batchai.recipes -w recipe_workspace -e cntk_experiment -d TENSORBOARD
```

Alternatively, you can use the Portal or Azure Storage Explorer to inspect the generated files. To distinguish output
from the different jobs, Batch AI creates an unique folder structure for each of them. You can find the path to the
folder containing the output using `jobOutputDirectoryPathSegment` attribute of the submitted job:

```azurecli test
az batchai job show -n distributed_tensorflow -g batchai.recipes -w recipe_workspace -e tensorflow_experiment --query jobOutputDirectoryPathSegment
```

Example output:
```
"00000000-0000-0000-0000-000000000000/batchai.recipes/workspaces/recipe_workspace/experiments/tensorflow_experiment/jobs/distributed_tensorflow/991b4f26-5411-4a43-a735-c2905f2be29a"
```

# Cleanup Resources

Delete the resource group and all allocated resources with the following command:

```azurecli
az group delete -n batchai.recipes -y
```
