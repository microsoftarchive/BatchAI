Please follow [instructions](/documentation/using-azure-cli-20.md) to install Azure CLI 2.0 and configure it for using with Batch AI.

### Create a Resource Group

Create a resource group ```batchaitests``` (or choose your own resource name) which will be used for resources creations:

```sh
az group create -n batchaitests -l eastus
```

### Create a Storage Account

Create a storage account with an unique name in the same region where you are going to use Batch AI:

```sh
az storage account create -n <storage account name> --sku Standard_LRS -l eastus -g batchaitests
```

To avoid typing storage account name in each command, we will set local environment variable `BAI_SAMPLE_STORAGE_ACCOUNT`:

For GNU/Linux:
```sh
export BAI_SAMPLE_STORAGE_ACCOUNT=<storage_account_name>
```

For Windows:
```
set BAI_SAMPLE_STORAGE_ACCOUNT=<storage account name>
```

### Create Cluster with Mounted File Systems

In this section we will create an auto-scale cluster with following parameters:

- location: eastus;
- resource group: batchaitests;
- name: nc6;
- size: Standard_NC6 (one GPU per node);
- min number of nodes: 0. In this case nodes will be deallocated after the job is completed;
- max number of nodes: 2. The job which we are going to run will require 2 nodes;
- image: UbuntuDSVM. This will allow you to run jobs both on nodes and in containers;
- mount volumes:
    - Azure File Share 'scriptsandoutputs' for job's scripts and output with relative mount path `scriptsandoutputs` (mounted at `$AZ_BATCHAI_MOUNT_ROOT/scriptsandoutputs`);
    - Azure Blob Container 'trainingdata' to store training data with relative mount path `data` (mounted at `$AZ_BATCHAI_MOUNT_ROOT/data`).
- admin user (Batch AI will create an admin user on each node to allow you to ssh into the nodes for debugging purposes):
    - on GNU/Linux - you current user name and ssh-key will be used
    - on Windows - you need to provide required user name and password (or ssh-key). For password provide `-p` option,
    for ssh key provide `-k` option.     
    
For GNU/Linux:

```sh
az storage share create --account-name $BAI_SAMPLE_STORAGE_ACCOUNT --name scriptsandoutputs
az storage container create --account-name $BAI_SAMPLE_STORAGE_ACCOUNT --name trainingdata
az batchai cluster create \
    -l eastus -g batchaitests -n nc6 \
    -i UbuntuDSVM -s Standard_NC6 \
    --min 0 --max 2 \
    --storage-account-name $BAI_SAMPLE_STORAGE_ACCOUNT \
    --afs-name scriptsandoutputs --afs-mount-path scriptsandoutputs \
    --container-name training_data --container-mount-path data \
    -u $USER -k ~/.ssh/id_rsa.pub
```

For Windows:

```sh
set ADMIN_ACCOUNT_NAME=<name for admin user>
set ADMIN_ACCOUNT_PASSWORD_OR_SSH_KEY=-p <password for admin user>
az storage share create --account-name %BAI_SAMPLE_STORAGE_ACCOUNT% --name scriptsandoutputs
az storage container create --account-name %BAI_SAMPLE_STORAGE_ACCOUNT% --name trainingdata
az batchai cluster create -u %ADMIN_ACCOUNT_NAME% %ADMIN_ACCOUNT_PASSWORD_OR_SSH_KEY% --storage-account-name %BAI_SAMPLE_STORAGE_ACCOUNT% -l eastus -g batchaitests -n nc6 -i UbuntuDSVM -s Standard_NC6 --min 0 --max 2 --storage-account-name <storage account name> --afs-name scriptsandoutputs --afs-mount-path scriptsandoutputs --container-name training_data -container-mount-path data
```

### Deploy Training Data

- Download and extract preprocessed [MNIST database](https://batchaisamples.blob.core.windows.net/samples/mnist_dataset_original.zip?st=2017-09-29T18%3A29%3A00Z&se=2099-12-31T08%3A00%3A00Z&sp=rl&sv=2016-05-31&sr=b&sig=Qc1RA3zsXIP4oeioXutkL1PXIrHJO0pHJlppS2rID3I%3D).

For GNU/Linux:

```sh
wget "https://batchaisamples.blob.core.windows.net/samples/mnist_dataset_original.zip?st=2017-09-29T18%3A29%3A00Z&se=2099-12-31T08%3A00%3A00Z&sp=rl&sv=2016-05-31&sr=b&sig=Qc1RA3zsXIP4oeioXutkL1PXIrHJO0pHJlppS2rID3I%3D" -O mnist_dataset_original.zip
unzip mnist_dataset_original.zip
```

For Windows, download and unzip [this archive](https://batchaisamples.blob.core.windows.net/samples/mnist_dataset_original.zip?st=2017-09-29T18%3A29%3A00Z&se=2099-12-31T08%3A00%3A00Z&sp=rl&sv=2016-05-31&sr=b&sig=Qc1RA3zsXIP4oeioXutkL1PXIrHJO0pHJlppS2rID3I%3D) manually into the current folder.

- Upload MNIST database into the container:

For GNU/Linux:
```sh
az storage blob upload --account-name $BAI_SAMPLE_STORAGE_ACCOUNT --container-name trainingdata --file t10k-images-idx3-ubyte.gz -n nmist_dataset/t10k-images-idx3-ubyte.gz
az storage blob upload --account-name $BAI_SAMPLE_STORAGE_ACCOUNT --container-name trainingdata --file t10k-labels-idx1-ubyte.gz -n nmist_dataset/t10k-labels-idx1-ubyte.gz
az storage blob upload --account-name $BAI_SAMPLE_STORAGE_ACCOUNT --container-name trainingdata --file train-images-idx3-ubyte.gz -n nmist_dataset/train-images-idx3-ubyte.gz
az storage blob upload --account-name $BAI_SAMPLE_STORAGE_ACCOUNT --container-name trainingdata --file train-labels-idx1-ubyte.gz -n nmist_dataset/train-labels-idx1-ubyte.gz
```

For Windows:
```
az storage blob upload --account-name %BAI_SAMPLE_STORAGE_ACCOUNT% --container-name trainingdata --file t10k-images-idx3-ubyte.gz -n nmist_dataset/t10k-images-idx3-ubyte.gz
az storage blob upload --account-name %BAI_SAMPLE_STORAGE_ACCOUNT% --container-name trainingdata --file t10k-labels-idx1-ubyte.gz -n nmist_dataset/t10k-labels-idx1-ubyte.gz
az storage blob upload --account-name %BAI_SAMPLE_STORAGE_ACCOUNT% --container-name trainingdata --file train-images-idx3-ubyte.gz -n nmist_dataset/train-images-idx3-ubyte.gz
az storage blob upload --account-name %BAI_SAMPLE_STORAGE_ACCOUNT% --container-name trainingdata --file train-labels-idx1-ubyte.gz -n nmist_dataset/train-labels-idx1-ubyte.gz

```

### Deploy scripts

- Download [mnist_replica.py](https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/TensorFlow/TensorFlow-GPU-Distributed/mnist_replica.py?token=AcZzrcpJGDHCUzsCyjlWiKVNfBuDdkqwks5Z4dPrwA%3D%3D) sample script into the current folder:

For GNU/Linux:

```sh
wget "https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/TensorFlow/TensorFlow-GPU-Distributed/mnist_replica.py?token=AcZzrcpJGDHCUzsCyjlWiKVNfBuDdkqwks5Z4dPrwA%3D%3D" -O mnist_replica.py
```

For Windows, download the file into the current folder.

- Upload training script into `batchai_distributed_tensorflow_example` folder in the file share:

For GNU/Linux:
```sh
az storage directory create --account-name $BAI_SAMPLE_STORAGE_ACCOUNT --share-name scriptsandoutputs --name bai_distributed_tensorflow_example
az storage file upload --account-name $BAI_SAMPLE_STORAGE_ACCOUNT --share-name scriptsandoutputs --source mnist_replica.py --path bai_distributed_tensorflow_example
```

For Windows:
```sh
az storage directory create --account-name %BAI_SAMPLE_STORAGE_ACCOUNT% --share-name scriptsandoutputs --name bai_distributed_tensorflow_example
az storage file upload --account-name %BAI_SAMPLE_STORAGE_ACCOUNT% --share-name scriptsandoutputs --source mnist_replica.py --path bai_distributed_tensorflow_example
```

### Submit Job

The job creation parameters are defined in [job.json](./job.json):

- Two input directories with IDs `SCRIPT` and `DATASET` to allow the job to find the sample script and MNIST Database via environment variables `$AZ_BATCHAI_INPUT_SCRIPT` and `$AZ_BATCHAI_INPUT_DATASET`;
- stdOutErrPathPrefix specifies that the job should use `outputs` folder on mounted file share for standard output and error streams;
- Output directory with ID `MODEL` tells BatchAI to create an output folder in `outputs` folder of mounted file share and make it available to the job via `$AZ_BATCHAI_OUTPUT_MODEL` environment variable;
- nodeCount defining how many nodes will be used for the job execution;
- path to mnist_replica.py and parameters for master, workers and parameter server;
- ```tensorflow/tensorflow:1.1.0-gpu``` docker image will be used for job execution.

Note, you can delete the docker image information to run the job directly on DSVM.

- Download [job.json](./job.json) into current directory.

For GNU/Linux:
```sh
wget https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/TensorFlow/TensorFlow-GPU-Distributed/job.json
```
For Windows, manually download the file.

- Submit the job using the following command:

```sh
az batchai job create -l eastus -g batchaitests -n distibuted_tensorflow -r nc6 -c job.json
```

Note, the job will start running when the cluster finished allocation and initialization of the node.

### Cleanup Resources

Delete `batchaitests` resource group to delete storage account, job and cluster.

```sh
az group delete -n batchaitests
```
### Next Steps

Azure CLI 2.0 Batch AI specific [documentation](/documentation/using-azure-cli-20.md) contains detailed information on
how to manage your clusters and jobs.

[CLI Quickstart](https://docs.microsoft.com/en-us/azure/batch-ai/quickstart-cli) contains an end-to-end example of using
Azure CLI 2.0 for Batch AI cluster creation, job submission and checking job's execution results.