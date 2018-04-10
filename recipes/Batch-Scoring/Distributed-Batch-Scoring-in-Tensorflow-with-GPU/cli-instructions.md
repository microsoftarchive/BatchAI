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

- Download and extract unlabeled images from imagenet dataset into the current folder:

For GNU/Linux users:

```sh
wget "https://batchaisamples.blob.core.windows.net/samples/imagenet_samples.zip?st=2017-09-29T18%3A29%3A00Z&se=2099-12-31T08%3A00%3A00Z&sp=rl&sv=2016-05-31&sr=c&sig=PmhL%2BYnYAyNTZr1DM2JySvrI12e%2F4wZNIwCtf7TRI%2BM%3D" -O imagenet_samples.zip
unzip imagenet_samples.zip
```

- Download pretrained InceptionV3 model file into the current folder:

For GNU/Linux users:

```sh
wget "http://download.tensorflow.org/models/inception_v3_2016_08_28.tar.gz" -O inception_v3_2016_08_28.tar.gz
tar -xvf inception_v3_2016_08_28.tar.gz
```

- Create an Azure Blob Container with `pretained_models` and `unlabeled_images` folders and upload the pretrained model file and images into them:

```sh
az storage container create --name batchaisample --account-name <storage account name>
az storage blob upload --container-name batchaisample --file inception_v3.ckpt --name pretained_models/inception_v3.ckpt --account-name <storage account name>
az storage blob upload --container-name batchaisample --file imagenet_slim_labels.txt --name pretained_models/imagenet_slim_labels.txt --account-name <storage account name> 
az storage blob upload-batch --destination batchaisample/unlabeled_images --source samples --account-name <storage account name>
```

- Create an Azure File Share with `classification_samples` folder and upload the job script [batch_image_label.py](./batch_image_label.py) into it:

```sh
az storage share create --name batchaisample --account-name <storage account name>
az storage directory create --share-name batchaisample --name classification_samples --account-name <storage account name>
az storage file upload --share-name batchaisample --source batch_image_label.py --path classification_samples --account-name <storage account name>
```

### Cluster

For this recipe we need two nodes GPU cluster (`min node = max node = 2`) of `Standard_NC6` size (one GPU) with standard Ubuntu LTS image. The Azure Blob Container and Azure File Share created in the previous step will be mounted at `$AZ_BATCHAI_MOUNT_ROOT/bfs` and `$AZ_BATCHAI_MOUNT_ROOT/afs` respectively.

#### Cluster Creation Command

For GNU/Linux users:

```sh
az batchai cluster create -l eastus -g batchaitests --storage-account-name <storage account name> -n nc6 -s Standard_NC6 --min 2 --max 2 --afs-name batchaisample --afs-mount-path afs --container-name batchaisample --container-mount-path bfs -u $USER -k ~/.ssh/id_rsa.pub
```

For Windows users:

```sh
az batchai cluster create -l eastus -g batchaitests --storage-account-name <storage account name> -n nc6 -s Standard_NC6 --min 2 --max 2 --afs-name batchaisample --afs-mount-path afs --container-name batchaisample --container-mount-path bfs -u <user_name> -p <password>
```

### Job

The job creation parameters are in [job.json](./job.json):

- The job will use `tensorflow/tensorflow:1.7.0-gpu` container.
- Will install job preparation task to install OpenMPI binary.
- Will use custom toolkit to launch MPI processes.
- In [batch_image_label.py](./batch_image_label.py), the input images for evaluation will be partitioned by the MPI rank, so that each MPI worker will evaluate part of the whole image set independently. 
- stdOutErrPathPrefix specifies that the job should use file share for standard output and error streams;
- Three input directories with IDs `SCRIPT`, `IMAGES` and `MODEL` to allow the job to find the sample script, unlabeled images and pretrained model via environment variables `$AZ_BATCHAI_INPUT_SCRIPT`, `$AZ_BATCHAI_INPUT_IMAGES` and `$AZ_BATCHAI_INPUT_MODEL`;
- An output directory with ID `LABEL` to allow job to find the output directory for the model via `$AZ_BATCHAI_OUTPUT_LABEL` environment variable;


#### Job Creation Command

```sh
az batchai job create -l eastus -g batchaitests -n classify_distributed -r nc6 -c job.json
```

Note, the job will start running when the cluster finished allocation and initialization of the node.

### Next Steps

Azure CLI 2.0 Batch AI specific [documentation](/documentation/using-azure-cli-20.md) contains detailed information on
how to manage your clusters and jobs.

[CLI Quickstart](https://docs.microsoft.com/en-us/azure/batch-ai/quickstart-cli) contains an end-to-end example of using
Azure CLI 2.0 for Batch AI cluster creation, job submission and checking job's execution results.