# Getting Started with the Recipes

## Prerequisites

 1. Azure subscription. This can be a free trial subscription, MSDN, or the one you use for other work.
 2. Azure Python SDK, if you like to run recipes using Python Jupyter notebook. See How to install [Azure SDK](https://docs.microsoft.com/en-us/python/azure/python-sdk-azure-install?view=azure-python)
 3. Azure CLI 2.0, if you like to run recipes using Azure CLI - See [Install Azure CLI 2.0](https://docs.microsoft.com/en-us/azure/storage/common/storage-create-storage-account?toc=%2fazure%2fstorage%2ffiles%2ftoc.json) for instructions.
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

Under construction...


## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
