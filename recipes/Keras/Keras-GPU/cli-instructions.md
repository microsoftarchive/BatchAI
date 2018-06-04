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

- Download mnist_cnn.py sample script into the current folder:

For GNU/Linux users:

```sh
wget "https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/Keras/Keras-DSVM/mnist_cnn.py?token=AcZzrU1mri0vNMxtUKL6GW6hSezGK7qBks5Z4ewWwA%3D%3D" -O mnist_cnn.py
```

- Create an Azure File Share with `keras_samples` folder and upload mnist_cnn.py
into it:

```sh
az storage share create --name batchaisample --account-name <storage account name>
az storage directory create --share-name batchaisample --name keras_samples
az storage file upload --share-name batchaisample --source mnist_cnn.py --path keras_samples
```

### Cluster

For this recipe we need one node GPU cluster (`min node = max node = 1`) of `Standard_NC6` size (one GPU) with Ubuntu DSVM (```UbuntuDSVM```) image and Azure File share `batchaisample` mounted at `$AZ_BATCHAI_MOUNT_ROOT/external`.

#### Cluster Creation Command

For GNU/Linux users:

```sh
az batchai cluster create -l eastus -g batchaitests --storage-account-name <storage account name> -n nc6 -s Standard_NC6 --min 1 --max 1 --afs-name batchaisample --afs-mount-path external -u $USER -k ~/.ssh/id_rsa.pub
```

For Windows users:

```sh
az batchai cluster create -l eastus -g batchaitests --storage-account-name <storage account name> -n nc6 -s Standard_NC6 --min 1 --max 1 --afs-name batchaisample --afs-mount-path external -u <user_name> -p <password>
```

### Job

The job creation parameters are in [job_cntk.json](./job_cntk.json) or [job_tensorflow.json](./job_tensorflow.json):

- An input directory with ID `SCRIPT` to allow the job to find the sample script via environment variable `$AZ_BATCHAI_INPUT_SCRIPT`;
- stdOutErrPathPrefix specifies that the job should use file share for standard output and error streams;
- nodeCount defining how many nodes will be used for the job execution;

If `'cntk'` backend is used:
- The job will use `microsoft/2.5.1-gpu-python2.7-cuda9.0-cudnn7.0` container.
- Keras framework has been preinstalled in the container
- The job needs to have `cntk_settings` to be configured.

If `'tensorflow'` backend is used:
- The job will use `tensorflow/tensorflow:1.8.0-gpu` container.
- Keras framework will be installed by job preparation command line.
- The job needs to have `tensor_flow_settings` to be configured.

#### Job Creation Command

If run Keras with CNTK backend:

```sh
az batchai job create -l eastus -g batchaitests -n keras -r nc6 -c job_cntk.json
```

or if run Keras with Tensorflow backend:

```sh
az batchai job create -l eastus -g batchaitests -n keras -r nc6 -c job_tensorflow.json
```

Note, the job will start running when the cluster finished allocation and initialization of the node.

### Next Steps

Azure CLI 2.0 Batch AI specific [documentation](/documentation/using-azure-cli-20.md) contains detailed information on
how to manage your clusters and jobs.

[CLI Quickstart](https://docs.microsoft.com/en-us/azure/batch-ai/quickstart-cli) contains an end-to-end example of using
Azure CLI 2.0 for Batch AI cluster creation, job submission and checking job's execution results.
