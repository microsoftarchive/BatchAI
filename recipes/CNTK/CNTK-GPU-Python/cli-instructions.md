Please follow [instructions](/recipes/Readme.md) to install Azure CLI 2.0, configure default location, create and configure default resource group and storage account.


### Data Deployment

- Download and extract preprocessed MNIST Database from this [location](https://batchaisamples.blob.core.windows.net/samples/mnist_dataset.zip?st=2017-09-29T18%3A29%3A00Z&se=2099-12-31T08%3A00%3A00Z&sp=rl&sv=2016-05-31&sr=c&sig=PmhL%2BYnYAyNTZr1DM2JySvrI12e%2F4wZNIwCtf7TRI%2BM%3D) into the current folder.

For GNU/Linux users:

```sh
wget "https://batchaisamples.blob.core.windows.net/samples/mnist_dataset.zip?st=2017-09-29T18%3A29%3A00Z&se=2099-12-31T08%3A00%3A00Z&sp=rl&sv=2016-05-31&sr=c&sig=PmhL%2BYnYAyNTZr1DM2JySvrI12e%2F4wZNIwCtf7TRI%2BM%3D" -O mnist_dataset.zip
unzip mnist_dataset.zip
```

- Download ConvNet_MNIST.py example script into the current folder:

For GNU/Linux users:

```sh
wget "https://raw.githubusercontent.com/Azure/BatchAI/master/recipes/CNTK/CNTK-GPU-Python/ConvNet_MNIST.py?token=AcZzrejaokHC2Nj5ehsoMFe4t3LqFcThks5Z4bmEwA%3D%3D" -O ConvNet_MNIST.py
```

- Create an Azure File Share with `nmist_database` and `cntk_sample` folders and upload MNIST database and ConvNet_MNIST.py script:

```sh
az storage share create --name batchaisample
az storage directory create --share-name batchaisample --name mnist_database
az storage file upload --share-name batchaisample --source Train-28x28_cntk_text.txt --path mnist_database
az storage file upload --share-name batchaisample --source Test-28x28_cntk_text.txt --path mnist_database
az storage directory create --share-name batchaisample --name cntk_samples
az storage file upload --share-name batchaisample --source ConvNet_MNIST.py --path cntk_samples
```

### Cluster

For this recipe we need one node GPU cluster (`min node = max node = 1`) of `Standard_NC6` size (one GPU) with standard Ubuntu LTS (`UbuntuLTS`) or Ubuntu DSVM (```UbuntuDSVM```) image and Azure File share `batchaisample` mounted at `$AZ_BATCHAI_MOUNT_ROOT/external`.

#### Cluster Creation Command

For GNU/Linux users:

```sh
az batchai cluster create -n nc6 -i UbuntuDSVM -s Standard_NC6 --min 1 --max 1 --afs-name batchaisample --afs-mount-path external -u $USER -k ~/.ssh/id_rsa.pub
```

For Windows users:

```sh
az batchai cluster create -n nc6 -i UbuntuDSVM -s Standard_NC6 --min 1 --max 1 --afs-name batchaisample --afs-mount-path external -u <user_name> -p <password>
```

### Job

The job creation parameters are in [job.json](./job.json):

- Two input directories with IDs `SCRIPT` and `DATASET` to allow the job to find the sample script and MNIST Database via environment variables `$AZ_BATCHAI_INPUT_SCRIPT` and `$AZ_BATCHAI_INPUT_DATASET`;
- stdOutErrPathPrefix specifies that the job should use file share for standard output and input;
- An output directory with ID `MODEL` to allow job to find the output directory for the model via `$AZ_BATCHAI_OUTPUT_MODEL` environment variable;
- node_count defining how many nodes will be used for the job execution;
- path and parameters for running ConvNet_MNIST.py;
- ```microsoft/cntk:2.1-gpu-python3.5-cuda8.0-cudnn6.0``` docker image will be used for job execution.

Note, you can remove docker image information to run the job directly on DSVM.

#### Job Creation Command

```sh
az batchai job create -n cntk_python --cluster-name nc6 -c job.json
```

Note, the job will start running when the cluster finished allocation and initialization of the node.
