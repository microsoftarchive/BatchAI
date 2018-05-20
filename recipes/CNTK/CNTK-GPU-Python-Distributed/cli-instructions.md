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

### Data Deployment

- Download ConvNet_CIFAR10_DataAug_Distributed.py and CIFAR-10_data_prepare.sh into the current folder:

For GNU/Linux users:

```sh
wget "https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python-Distributed/ConvNet_CIFAR10_DataAug_Distributed.py?token=AcZzrbN1I34RrKn8MPnn5_dfy86I-XEIks5Z4cfswA%3D%3D" -O ConvNet_CIFAR10_DataAug_Distributed.py
wget "https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python-Distributed/CIFAR-10_data_prepare.sh?token=AcZzrdr1tTQK_Gr7EdVXvg-sUarpWMqnks5Z4chYwA%3D%3D" -O CIFAR-10_data_prepare.sh
```

- Create an Azure File Share with `cntk_sample` folder and upload the scripts into it:

```sh
az storage share create --name batchaisample --account-name <storage account name>
az storage directory create --share-name batchaisample --name cntk_samples
az storage file upload --share-name batchaisample --source ConvNet_CIFAR10_DataAug_Distributed.py --path cntk_samples
az storage file upload --share-name batchaisample --source CIFAR-10_data_prepare.sh --path cntk_samples
```

### Cluster

For this recipe we need two nodes GPU cluster (`min node = max node = 2`) of `Standard_NC6` size (one GPU) with standard Ubuntu LTS (`UbuntuLTS`) or Ubuntu DSVM (```UbuntuDSVM```) image and Azure File share `batchaisample` mounted at `$AZ_BATCHAI_MOUNT_ROOT/external`.

#### Cluster Creation Command

For GNU/Linux users:

```sh
az batchai cluster create -l eastus -g batchaitests --storage-account-name <storage account name> -n nc6 -i UbuntuDSVM -s Standard_NC6 --min 2 --max 2 --afs-name batchaisample --afs-mount-path external -u $USER -k ~/.ssh/id_rsa.pub
```

For Windows users:

```sh
az batchai cluster create -l eastus -g batchaitests --storage-account-name <storage account name> -n nc6 -i UbuntuDSVM -s Standard_NC6 --min 2 --max 2 --afs-name batchaisample --afs-mount-path external -u <user_name> -p <password>
```

### Job

The job creation parameters are in [job.json](./job.json):

- An input directory with IDs `SCRIPT` to allow the job to find the sample scripts via environment variable `$AZ_BATCHAI_INPUT_SCRIPT`;
- stdOutErrPathPrefix specifies that the job should use file share for standard output and input;
- An output directory with ID `MODEL` to allow job to find the output directory for the model via `$AZ_BATCHAI_OUTPUT_MODEL` environment variable;
- node_count defining how many nodes will be used for the job execution;
- job preparation task will execute CIFAR-10_data_prepare.sh script to download and preprocess CIFAR-10 dataset on local SSD (at $AZ_BATCHAI_JOB_TEMP);
- path and parameters for running ConvNet_CIFAR10_DataAug_Distributed.py;
- ```microsoft/cntk:2.1-gpu-python3.5-cuda8.0-cudnn6.0``` docker image will be used for job execution.

Note, you can delete the docker image information to run the job directly on DSVM.

For documentation on the environment variables, please refer to [using-batchai-environment-variables.md](/documentation/using-batchai-environment-variables.md).

#### Job Creation Command

```sh
az batchai job create -l eastus -g batchaitests -n distributed_cntk_python -r nc6 -c job.json
```

Note, the job will start running when the cluster finished allocation and initialization of the nodes.

To visualize the result of the job:

```sh
az batchai job file stream -n distributed_cntk_python -g batchaitests -f stdout.txt
```

### Next Steps

Azure CLI 2.0 Batch AI specific [documentation](/documentation/using-azure-cli-20.md) contains detailed information on
how to manage your clusters and jobs.

[CLI Quickstart](https://docs.microsoft.com/en-us/azure/batch-ai/quickstart-cli) contains an end-to-end example of using
Azure CLI 2.0 for Batch AI cluster creation, job submission and checking job's execution results.
