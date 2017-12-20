Please follow [instructions](/recipes/Readme.md) to install Azure CLI 2.0, configure default location, create and configure default resource group and storage account.


### Data Deployment

- Download ConvNet_CIFAR10_DataAug_Distributed.py, ConvNet_CIFAR10_DataAug.py and CIFA-10_data_prepare.sh into the current folder:

For GNU/Linux users:

```sh
wget "https://raw.githubusercontent.com/Microsoft/CNTK/v2.3/Examples/Image/Classification/ResNet/Python/resnet_models.py" -O resnet_models.py
wget "https://raw.githubusercontent.com/Microsoft/CNTK/v2.3/Examples/Image/Classification/ResNet/Python/TrainResNet_CIFAR10_Distributed.py" -O TrainResNet_CIFAR10_Distributed.py
wget "https://raw.githubusercontent.com/Microsoft/CNTK/v2.3/Examples/Image/Classification/ResNet/Python/TrainResNet_CIFAR10.py" -O TrainResNet_CIFAR10.py
```

Create an Azure File Share with `cntk_sample` folder and upload the scripts into it:

```sh
az storage share create --name batchaisample
az storage directory create --share-name batchaisample --name cntk_samples
az storage file upload --share-name batchaisample --source TrainResNet_CIFAR10_Distributed.py --path cntk_samples
az storage file upload --share-name batchaisample --source TrainResNet_CIFAR10.py --path cntk_samples
az storage file upload --share-name batchaisample --source resnet_models.py --path cntk_samples
```

Upload the job preparation script, that does the following tasks:
- Download CIFAR-10 data set on all GPU nodes (under ```$AZ_BATCHAI_JOB_TEMP``` directory)
- Install IntelMPI binary

```sh
az storage file upload --share-name batchaisample --source jobprep_cntk_distributed_ib.sh --path horovod_samples
```


### Cluster

By default, for this recipe we will use a GPU cluster with two nodes (`min node = max node = 2`) of `Standard_NC24r` size (four GPU with infiniband)
with latest Ubuntu 16.04-LTS image. 

Azure File share `batchaisample` mounted at `$AZ_BATCHAI_MOUNT_ROOT/external`.

#### Cluster Creation Command

For GNU/Linux users:

```sh
az batchai cluster create -n nc24r -s Standard_NC24r --min 2 --max 2 --afs-name batchaisample --afs-mount-path external -u $USER -k ~/.ssh/id_rsa.pub
```

For Windows users:

```sh
az batchai cluster create -n nc24r -s Standard_NC24r --min 2 --max 2 --afs-name batchaisample --afs-mount-path external -u <user_name> -p <password>
```

### Job

The job creation parameters are in [job.json](./job.json):

- The job will use `batchaitraining/cntk:2.3-gpu-1bitsgd-py36-cuda8-cudnn6-intelmpi` container that is built based on [dockerfile](./dockerfile)
- Will use job preparation task to execute job prreparation script (jobprep_cntk_distributed_ib.sh). The CIFA-10 dataset will be downloaded and processed on compute nodes locally (under ```$AZ_BATCHAI_JOB_TEMP``` directory);
- Will use configured previously input and output directories;
- Will run TrainResNet_CIFAR10_Distributed.py providing CIFAR-10 Dataset path as the first parameter and desired mode output as the second one. 
- Will set ```processCount``` to 8, so that all 8 GPUs from 2 NC24r nodes will be used;
- An input directory with IDs `SCRIPT` to allow the job to find the sample scripts via environment variable `$AZ_BATCHAI_INPUT_SCRIPT`;
- stdOutErrPathPrefix specifies that the job should use file share for standard output and input;
- An output directory with ID `MODEL` to allow job to find the output directory for the model via `$AZ_BATCHAI_OUTPUT_MODEL` environment variable;
- For illustration purpose, we will train a ResNet 110 and only run 5 epoches


#### Job Creation Command

```sh
az batchai job create -n distributed_cntk_ib --cluster-name nc24r -c job.json
```

Note, the job will start running when the cluster finished allocation and initialization of the nodes.

### Get Help

The Azure CLI has built-in help documentation, which you can run from the command line:

```sh
az [command-group [command]] -h
```

For example, to get information about all Azure Batch AI categories, use:

```sh
az batchai -h
```

To get help with the command to create a cluster, use:

```sh
az batchai cluster create -h
```

You can use [CLI Quickstart](https://docs.microsoft.com/en-us/azure/batch-ai/quickstart-cli) as end-to-end example of CLI usage.
