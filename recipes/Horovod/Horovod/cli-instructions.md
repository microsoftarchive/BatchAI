Please follow [instructions](/recipes/Readme.md) to install Azure CLI 2.0, configure default location, create and configure default resource group and storage account.


### Data Deployment

- Download tensorflow_mnist.py sample script into the current folder:

For GNU/Linux users:

```sh
wget https://raw.githubusercontent.com/uber/horovod/v0.9.10/examples/tensorflow_mnist.py
```

- Create an Azure File Share with `horovod_samples` folder and upload tensorflow_mnist.py into it:

```sh
az storage share create --name batchaisample
az storage directory create --share-name batchaisample --name horovod_samples
az storage file upload --share-name batchaisample --source tensorflow_mnist.py --path horovod_samples
```

### Cluster

For this recipe we will use a GPU cluster with two nodes (`min node = max node = 2`) of `Standard_NC6` size (one GPU) 
with Ubuntu DSVM (```UbuntuDSVM```) image and Azure File share `batchaisample` mounted at 
`$AZ_BATCHAI_MOUNT_ROOT/external`.

#### Cluster Creation Command

For GNU/Linux users:

```sh
az batchai cluster create -n nc6 -i UbuntuDSVM -s Standard_NC6 --min 2 --max 2 --afs-name batchaisample --afs-mount-path external -u $USER -k ~/.ssh/id_rsa.pub
```

For Windows users:

```sh
az batchai cluster create -n nc6 -i UbuntuDSVM -s Standard_NC6 --min 2 --max 2 --afs-name batchaisample --afs-mount-path external -u <user_name> -p <password>
```

### Job

The job creation parameters are in [job.json](./job.json):

- An input directory with ID `SCRIPTS` to allow the job to find the sample script via environment variable `$AZ_BATCHAI_INPUT_SCRIPTS`;
- stdOutErrPathPrefix specifies that the job should use file share for standard output and error streams;
- nodeCount defines how many nodes will be used for the job execution;
- ```tensorflow/tensorflow:1.1.0-gpu``` standard tensorflow container will be used and ```Horovod``` will be installed by job preparation command line.
Note, you can build your own docker image containing tensorflow and Horovod instead;
- The ```tensorflow_mnist.py``` example will be executed with custom toolkit. Note, Batch AI will create a hostfile for 
the job, it can be found via ```$AZ_BATCHAI_MPI_HOST_FILE``` environment variable.

#### Job Creation Command

```sh
az batchai job create -n keras --cluster-name nc6 -c job.json
```

Note, the job will start running when the cluster finished allocation and initialization of the nodes.