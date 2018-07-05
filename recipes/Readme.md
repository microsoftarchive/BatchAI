# Getting Started with the Recipes

## Prerequisites

 1. Azure subscription. This can be a free trial subscription, MSDN, or the one you use for other work.
 2. Azure Python SDK and azure-mgmt-batchai, if you like to run recipes using Python Jupyter notebook. See How to install [Azure SDK](https://docs.microsoft.com/en-us/python/azure/python-sdk-azure-install?view=azure-python). 
 3. Azure CLI 2.0, if you like to run recipes using Azure CLI - See [Install Azure CLI 2.0](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest#install-on-windows) for instructions.
 4. Azure Storage Account in East US (required for all recipes). See [How to create Azure storage accounts](https://docs.microsoft.com/en-us/azure/storage/common/storage-create-storage-account?toc=%2fazure%2fstorage%2ffiles%2ftoc.json)
 
## Preparation

### Make a Local Copy of Repo.

To start, please Clone or download this [repo](https://github.com/Azure/BatchAI)

### Install Azure CLI 2.0 and Configure Azure CLI 2.0

Please follow Azure CLI 2.0 Batch AI specific [documentation](/documentation/using-azure-cli-20.md) to install and
configure Azure CLI 2.0 for using with Batch AI.

### Run Setup Wizard Script to Enable Batch AI

We provide setup wizard scripts of [setup.ps1](./setup.ps1) for Windows users and [setup.sh](./setup.sh) for Linux users. Please execute the script from you cloned recipe directory `<your clone root>/BatchAI/recipes`.

Note that `Azure CLI 2.0` is required for the setup scripts. Please follow [documentation](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest) to install and configure Azure CLI 2.0. For Linux Users, [jq](https://stedolan.github.io/jq/download/) package is also required to process json data.

### Manual Preparation Setup

Alternative to use setup wizard scripts. You can also configure Batch AI manually. Please follow [Preparation.md](./Preparation.md) for instructions.

## Recipe Instructions

Use the following links for a quick navigation:

1. [Run Recipes Using Python Jupyter notebook](#jupyternotebook)
2. [Run Recipes Using Azure CLI 2.0](#azurecli)

## <a name="jupyternotebook"></a> Run Recipes Using Python Jupyter notebook

### Helper functions in utilities

For your convenience, we provide a collection of helper functions in [BatchAI/utilities](../utilities) used for each recipes:

- Read parameters from configuration file
- Create python client object (BatchAIManagementClient) to access Azure Batch AI service
- Create/Update resource group
- Download file with given shared access signature (SAS)
- Print Job/Cluster status
- File Streaming 

### Install Azure Batch AI Management Client

Install Batch AI management client using the following command:
 
 ```sh
 pip install azure-mgmt-batchai
 ```

### Install Azure Python SDK

Since all recipes utlize APIs from other Azure products (e.g, Azure storage, credentials), it is also required to install the full package of Azure Python SDK:
 ```sh
 pip install azure
 ```

### Install Jupyter Notebook

Please install Jupyter Notebook from https://jupyter.org/ or run

```sh
python -m pip install jupyter
```

### Start to Run Recipes

- Route into the root your cloned recipe directory 
```sh
cd <your clone root>/BatchAI/recipes
```

- Launch the Jupyter Notebook by
```sh
jupyter notebook
```
- In the prompted brower brower, navigate into the recipe of interest, and start the *.ipynb file.


## <a name="azurecli"></a> Run Recipes Using Azure CLI 2.0

### Install Azure CLI 2.0 and Configure Azure CLI 2.0

Please follow Azure CLI 2.0 Batch AI specific [documentation](/documentation/using-azure-cli-20.md) to install and
configure Azure CLI 2.0 for using with Batch AI.

### Generate Authentication Key for SSH (for Cloud Shell and GNU/Linux Users)

During Cluster and File Server creation you will need to specify a name and authentication method for administrator account which will be created on each compute node (you can use this account to ssh to the node).

You can provide a password and/or ssh public key as authentication method via --password (-p) and --ssh-public-key (-k) parameters.

GNU/Linux users (including Cloud Shell users) can generate authentication key for ssh using ```ssh-keygen``` command.

Note, GNU/Linux part of recipes expects you to have a public ssh key at ~/.ssh/id_rsa.pub, if you prefer to use different ssh key, please update -k parameter value.

### Install unzip package (for GNU/Linux Users)

Training data used in recipes is compressed in ```zip``` archives and requires ```unzip``` utility to be installed on the host, please install it using your distribution package manager.

Cloud Shell has ```unzip``` already installed.

### Run Recipes

Each recipe contains ```cli-instructions.md``` file which describes input data, cluster and job configuration and provides instructions for cluster and job creation.

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.