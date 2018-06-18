Please follow [instructions](/documentation/using-azure-cli-20.md) to install Azure CLI 2.0 and configure it for using with Batch AI.

### Create a Resource Group

Create a resource group ```batchaitests``` (or choose your own resource name) which will be used for resources creations:

```sh
az group create -n batchai.recipes -l eastus
```

### Create a Storage Account

Create a storage account with an unique name in the same region where you are going to use Batch AI:

```sh
az storage account create -n <storage account name> --sku Standard_LRS -l eastus -g batchai.recipes
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
az storage container create --name data --account-name <storage account name>
az storage blob upload --container-name data --file inception_v3.ckpt --name pretained_models/inception_v3.ckpt --account-name <storage account name>
az storage blob upload --container-name data --file imagenet_slim_labels.txt --name pretained_models/imagenet_slim_labels.txt --account-name <storage account name> 
az storage blob upload-batch --destination data/unlabeled_images --source samples --account-name <storage account name>
```

- Create an Azure File Share with `classification_samples` folder and upload the job script [batch_image_label.py](./batch_image_label.py) into it:

The following commands will create Azure File Shares `scripts` and `logs` and will copy training script into `chainer`
folder inside of `scripts` share:

```azurecli test
az storage share create -n scripts --account-name <storage account name>
az storage share create -n logs --account-name <storage account name>
az storage directory create --share-name scripts --name classification_samples --account-name <storage account name>
az storage file upload --share-name scripts --source batch_image_label.py --path classification_samples --account-name <storage account name>
```

# Create a Batch AI Workspace

The following command will create a new workspace ```recipe_workspace``` in East US location:

```azurecli test
az batchai workspace create -g batchai.recipes -n recipe_workspace -l eastus
```

# Create GPU cluster

The following command will create a single node GPU cluster (VM size is Standard_NC6) using Ubuntu as the operation system image.

```azurecli test
az batchai cluster create -n nc6 -g batchai.recipes -w recipe_workspace -s Standard_NC6 -t 2 --generate-ssh-keys 
```

`--generate-ssh-keys` option tells Azure CLI to generate private and public ssh keys if you have not them already, so
you can ssh to cluster nodes using the ssh key and you current user name. Note. You need to backup ~/.ssh folder to
some permanent storage if you are using Cloud Shell.

### Job

The job creation parameters are in [job.json](./job.json):

- The job will use `tensorflow/tensorflow:1.7.0-gpu` container.
- Will install job preparation task to install OpenMPI binary.
- Will use custom toolkit to launch MPI processes.
- We will mount file share at folder with name `afs`. Full path of this folder on a computer node will be `$AZ_BATCHAI_JOB_MOUNT_ROOT/afs`
- We will mount Azure Blob Container at folder with name `bfs`. Full path of this folder on a computer node will be `$AZ_BATCHAI_JOB_MOUNT_ROOT/bfs`
- In [batch_image_label.py](./batch_image_label.py), the input images for evaluation will be partitioned by the MPI rank, so that each MPI worker will evaluate part of the whole image set independently. 
- stdOutErrPathPrefix specifies that the job should use file share for standard output and error streams;
- Three input directories with IDs `SCRIPT`, `IMAGES` and `MODEL` to allow the job to find the sample script, unlabeled images and pretrained model via environment variables `$AZ_BATCHAI_INPUT_SCRIPT`, `$AZ_BATCHAI_INPUT_IMAGES` and `$AZ_BATCHAI_INPUT_MODEL`;
- An output directory with ID `LABEL` to allow job to find the output directory for the model via `$AZ_BATCHAI_OUTPUT_LABEL` environment variable;

## Submit the Job in an Experiment

Use the following command to create a new experiment called ```batch_scoring_experiment``` in the workspace:
```azurecli test
az batchai experiment create -g batchai.recipes -w recipe_workspace -n batch_scoring_experiment
```

Use the following command to submit the job on the cluster:

```azurecli test
az batchai job create -n batch_scoring -c nc6 -g batchai.recipes -w recipe_workspace -e batch_scoring_experiment -f job.json --storage-account-name <storage account name>
```
Note, the job will start running when the cluster finished allocation and initialization of the node.

## Inspect Generated Model Files

The job stores the generated label files in the output directory with id = `LABEL`, you can list this files and
get download URLs using the following command:

```azurecli
az batchai job file list -j batch_scoring -g batchai.recipes -w recipe_workspace -e batch_scoring_experiment -g batchai.recipes -d LABEL
```
Example Output:
```
[
  {
    "contentLength": 7798,
    "downloadUrl": "https://batchairecipestorage.file.core.windows.net/logs/1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/batch_scoring_experiment/jobs/batch_scoring/be18d8e1-df69-499e-a4e2-58d9228e34cd/outputs/result-labels-0.txt?sv=2016-05-31&sr=f&sig=7OUAI2x96DFxeZ2shZtKqdMrV0i3kyTrv6hSjiYd%2FnA%3D&se=2018-06-18T23%3A39%3A03Z&sp=rl",
    "fileType": "file",
    "lastModified": "2018-06-18T22:39:03+00:00",
    "name": "result-labels-0.txt"
  },
  {
    "contentLength": 5118,
    "downloadUrl": "https://batchairecipestorage.file.core.windows.net/logs/1cba1da6-5a83-45e1-a88e-8b397eb84356/batchai.recipes/workspaces/recipe_workspace/experiments/batch_scoring_experiment/jobs/batch_scoring/be18d8e1-df69-499e-a4e2-58d9228e34cd/outputs/result-labels-1.txt?sv=2016-05-31&sr=f&sig=uFjF6JZf7sbp18p29lj4F1UakwS9mLaLQeKRMDhZl%2F0%3D&se=2018-06-18T23%3A39%3A03Z&sp=rl",
    "fileType": "file",
    "lastModified": "2018-06-18T22:39:03+00:00",
    "name": "result-labels-1.txt"
  }
]
```

The expected scoring output should be text files with the following content:
```sh
ILSVRC2012_val_00000102.JPEG: Rhodesian ridgeback
ILSVRC2012_val_00000103.JPEG: tripod
ILSVRC2012_val_00000104.JPEG: typewriter keyboard
ILSVRC2012_val_00000105.JPEG: silky terrier
ILSVRC2012_val_00000106.JPEG: Windsor tie
ILSVRC2012_val_00000107.JPEG: harvestman
ILSVRC2012_val_00000108.JPEG: violin
ILSVRC2012_val_00000109.JPEG: loudspeaker
ILSVRC2012_val_00000110.JPEG: apron
ILSVRC2012_val_00000111.JPEG: American lobster

...

```
## Clean Up

Delete the resource group and all allocated resources with the following command:

```azurecli
az batchai group delete -n batchai.recipes -y
```