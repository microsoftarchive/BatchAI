# Getting Started with the Recipes

## Prerequisites

 1. Azure subscription. This can be a free trial subscription, MSDN, or the one you use for other work.
 2. Azure Python SDK and azure-mgmt-batchai, if you like to run recipes using Python Jupyter notebook. See How to install [Azure SDK](https://docs.microsoft.com/en-us/python/azure/python-sdk-azure-install?view=azure-python). 
 3. Azure CLI 2.0, if you like to run recipes using Azure CLI - See [Install Azure CLI 2.0](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest#install-on-windows) for instructions.
 4. Azure Storage Account in East US (required for all recipes). See [How to create Azure storage accounts](https://docs.microsoft.com/en-us/azure/storage/common/storage-create-storage-account?toc=%2fazure%2fstorage%2ffiles%2ftoc.json)
 
## Make a Local Copy of Repo

To start, please Clone or download this [repo](https://github.com/Azure/BatchAI)

## Recipe Instructions

Use the following links for a quick navigation:

1. [Run Recipes Using Python Jupyter notebook](#jupyternotebook)
2. [Run Recipes Using Azure CLI 2.0](#azurecli)

## <a name="jupyternotebook"></a> Run Recipes Using Python Jupyter notebook

### Create Credentials for Service Principal Authentication
Jupyter notebook recipes require you to use service principal authentication rather than providing your account credentials.
There are several ways to create a Service Principal as described in following sections:

#### Using Azure CLI2.0
1. Log in into Azure CLI 2.0
2. Execute the following command
```sh
$ az ad sp create-for-rbac
```
Example output:
```
{
  "appId": "...",
  "displayName": "azure-cli-2017-10-27-18-45-51",
  "name": "http://azure-cli-2017-10-27-18-45-51",
  "password": "...",
  "tenant": "..."
}
```
Use appId value as aad_client_id, password as aad_secret and tenant as aad_tenant during configuration file creation later.

#### Using Portal
1.	Log in to your Azure Account through the [Azure portal](https://portal.azure.com/).
2.	Select *Azure Active Directory*.
3.	To get the AAD tenant ID, select *Properties* and copy the *Directory ID*.  This value is your **AAD tenant ID**.
4.	Go back to *Azure Active Directory* and select *App registrations*.
5.	Select *New application registration*.
6.	Provide a name and URL for the application. After setting the values, select *Create*.
7.	From *App registrations* in *Azure Active Directory*, select your application.
8.	Copy the *Application ID* and this is your **AAD Client ID**.
9.	To generate an authentication key, select you application, go to *Settings* and select *Keys*.
10.	Provide a description and a duration for the key. When done, select *Save*. After saving the key, the value of the key is displayed. Copy this value because you are not able to retrieve the key later. This is your **AAD Secret**.
11.	To assign the just created application, select the subscription you are going to use for Azure Batch AI. (You can find it from *More Services* -> *Subscriptions*)
12.	Select *Acess control (IAM)*
13.	Select *Add*
14.	Select *Contributor* as the *role*
15.	Search for your application and select it.
16.	Select *Save* to finish assigning the role. You see your application in the list of users assigned to a role for that scope.

For a more detailed walk-through, please see [this link](https://docs.microsoft.com/en-us/azure/azure-resource-manager/resource-group-create-service-principal-portal).

### Register BatchAI Resource Providers
1.	Log in to your Azure Account through the [Azure portal](https://portal.azure.com/).
2.	Select the subscription you are going to use for Azure Batch AI. (You can find it from *More Services* -> *Subscriptions*)
3.  Select *Resource providers*
4.  Register with **Microsoft.BatchAI** and **Microsoft.Batch providers**. 
  
Note, a provider registration can take up to 15 minutes.

### Grant Batch AI Network Contributor Role on Your Subscription
You can use two different approaches:

#### Uzing Azure CLI 2.0
```sh
az role assignment create --scope /subscriptions/<your subscription id> --role "Network Contributor" --assignee 9fcb3732-5f52-4135-8c08-9d4bbaf203ea
```
, here `9fcb3732-5f52-4135-8c08-9d4bbaf203ea` is a service principal of Microsoft Azure BatchAI.

#### Using Portal
1.	Select the subscription you are going to use for Azure Batch AI. (You can find it from *More Services* -> *Subscriptions*)
2.	Select *Acess control (IAM)*
3.	Select *Add*
4.	Select *Network Contributor* as the *role*
5.	Search for 'Microsoft Azure BatchAI' application and select it.
6.	Select *Save* to finish assigning the role.

### Create Configuration File for All Recipes 

- Rename [configuration.json.template](/recipes/configuration.json.template) to configuration.json.
- Fill in your subscription Id and your AAD application information as obtained in the above step. 
- Leave the "base_url" filed as empty. 
- You need to specify the name of your resource group. Our recipe will automatically create resource group if it does not exist.  
- Specify your Azure Storage account name and key, Please see [this page](https://docs.microsoft.com/en-us/azure/storage/common/storage-create-storage-account?toc=%2fazure%2fstorage%2ffiles%2ftoc.json).
- Batch AI creates administrator user account on every compute node and enables ssh. You need to specify user name and at least a password or ssh public key for this account.
 
### Helper functions in utilities.py

For your convenience, we provide a collection of helper functions in [utilities.py](./utilities.py) used for each recipes:

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
