Please follow [instructions](/recipes/Readme.md) to install Azure CLI 2.0, configure default location, create and configure default resource group and storage account.


### Script Deployment

- Create an Azure File Share with `horovod_samples` folder:
```sh
az storage share create --name batchaisample
az storage directory create --share-name batchaisample --name horovod_samples
```
Upload the job preparation script, that does the following tasks:
- Install essential packages for infiniband support
- Download benchmark scripts from https://github.com/alsrgv/benchmarks
- Install IntelMPI binary
- Install honovod framework
```sh
az storage file upload --share-name batchaisample --source jobprep_benchmark.sh --path horovod_samples
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

- An input directory with ID `SCRIPTS` to allow the job to find the job preparation script via environment variable `$AZ_BATCHAI_INPUT_SCRIPTS`;
- stdOutErrPathPrefix specifies that the job should use file share for standard output and error streams;
- nodeCount defines how many nodes will be used for the job execution;
- ```tensorflow/tensorflow:1.4.0-gpu``` standard tensorflow container will be used 
- ```Horovod``` framwork, intelMPI and horovod benchmark scripts will be downloaded/installed by job preparation script;
You can build and publish your own docker image containing tensorflow and Horovod instead;
- The benchmark script (```tf_cnn_benchmarks.py```) will be executed with custom toolkit;
- If you are insterested using TCP instead, please replace ```-env I_MPI_FABRICS=dapl -env I_MPI_DAPL_PROVIDER=ofa-v2-ib0 -env I_MPI_DYNAMIC_CONNECTION=0``` with ```-env I_MPI_FABRICS=tcp``` in the command line.

#### Job Creation Command

```sh
az batchai job create -n horovod_benchmark --cluster-name nc24r -c job.json
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
