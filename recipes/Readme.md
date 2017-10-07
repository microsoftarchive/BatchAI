# Getting Started with the Recipes

## Prerequisites

 1. Azure subscription. This can be a free trial subscription, MSDN, or the one you use for other work.
 2. Azure Python SDK, if you like to run recipes using Python Jupyter notebook. See How to install [Azure SDK](https://docs.microsoft.com/en-us/python/azure/python-sdk-azure-install?view=azure-python)
 3. Azure CLI 2.0, if you like to run recipes using Azure CLI - See [Install Azure CLI 2.0](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest#install-on-windows) for instructions.
 4. Azure Storage Account in East US (required for all recipes). See [How to create Azure storage accounts](https://docs.microsoft.com/en-us/azure/storage/common/storage-create-storage-account?toc=%2fazure%2fstorage%2ffiles%2ftoc.json)

## Make a Local Copy of Repo

To start, please Clone or download this [repo](https://github.com/Azure/BatchAI)

## Run Recipes Using Python Jupyter notebook

### Create Configuration File for All Recipes 

- Rename [configuration.json.template](/recipes/configuration.json.template) to configuration.json.
- Populate it with your Batch AI credentials. Please see [this page](https://github.com/Azure/azure-sdk-for-python/wiki/Contributing-to-the-tests#getting-azure-credentials) on how to get your Azure AD credentials.
- Leave as "base_url" filed as empty. 
- Our recipe will automatically create resource group if not exist. You need to specify the name of your resource group to create. 
- Specify your Azure Storage account name and key, Please see [this page](https://docs.microsoft.com/en-us/azure/storage/common/storage-create-storage-account?toc=%2fazure%2fstorage%2ffiles%2ftoc.json).
- Batch AI creates administrator user account on every compute node and enables ssh. You need to specify user name and at least a password or ssh public key for this account.
 
### Install Jupyter Notebook

If you are going to use Jupyter version of recipes, please install Jupyter Notebook from https://jupyter.org/ or run

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


## Run Recipes Using Azure CLI 2.0

### Install Azure CLI 2.0

The easiest way to start using Azure CLI 2.0 is to launch Shell Console as described in these [instructions](https://docs.microsoft.com/en-us/cli/azure/get-started-with-azure-cli?view=azure-cli-latest).

If you prefer to install Azure CLI 2.0 on your computer, please follow these [instructions](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest) to install or update Azure CLI 2.0 to the latest version.

### Login and Select Subscription

If you are using Cloud Shell you are already logged in Azure. Otherwise, please execute ```az login``` command and follow instructions.

If you have multiple subscriptions, select Batch AI enabled subscription as default one by running the following command:

```sh
az account set -s <your subscription>
```

### Configure Default Location

Creation of Clusters, Jobs, File Servers and other resources requires you to specify location where they should be created, the location can be provided via ```--location``` parameter or can be added into default Azure CLI 2.0 configuration. To reduce the length of commands the recipes expect you to setup default location using the following command:

```sh
az configure --defaults location=eastus
```

### Create a Default Resource Group

Clusters, Jobs and File Servers are created under a resource group. It's recommended to create a dedicated resource group for running recipes because it will simplify resource management for you.

Create a resource group ```batchaitests``` (or choose your own resource name) and make it default for Azure CLI 2.0 using the following commands:

```sh
az group create --name batchaitests --location eastus
az configure --defaults group=batchaitests
```

### Create and Configure Default Storage Account

Each recipe requires you to have a storage account in a region where Batch AI enabled (currently, ```eastus```). Please you the following commands to create a new storage account and make it default for Azure CLI 2.0:

For GNU/Linux users:

```sh
az storage account create --name <unique storage account name> --sku Standard_LRS
export AZURE_STORAGE_ACCOUNT=mystorageaccount
export AZURE_STORAGE_KEY=$(az storage account keys list --account-name <unique storage account name> -o tsv --query [0].value)
export AZURE_BATCHAI_STORAGE_ACCOUNT=mystorageaccount
export AZURE_BATCHAI_STORAGE_KEY=$(az storage account keys list --account-name <unique storage account name> -o tsv --query [0].value)
```

For Windows users:

```sh
az storage account create --name <unique storage account name> --sku Standard_LRS
az storage account keys list --account-name mystorageaccount -o tsv --query [0].value > temp.txt
set /p AZURE_STORAGE_KEY=< temp.txt
set AZURE_BATCHAI_STORAGE_ACCOUNT=mystorageaccount
set /p AZURE_BATCHAI_STORAGE_KEY=< temp.txt
del temp.txt
```

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
