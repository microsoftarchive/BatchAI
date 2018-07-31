# Introduction

Azure CLI 2.0 has a command line module for managing Batch AI clusters, single node NFS and jobs.

This document covers Azure CLI 2.0 setup and usage.

# Setup

- The easiest way to start using Azure CLI 2.0 is to launch it from Shell Console in Azure Portal as described in
[Quickstart for Bash in Azure Cloud Shell tutorial](https://docs.microsoft.com/en-us/azure/cloud-shell/quickstart).

- Azure Data Science VM has Azure CLI 2.0 pre-installed but you may need to update it using [these instructions](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest) to get access to the latest
features.

- If you prefer to setup Azure CLI 2.0 on your computer, please follow [these instructions](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest).

- You can get access to the latest not published version of Azure CLI 2.0 by following [these instructions](https://github.com/Azure/azure-cli#edge-builds).

# Get Started

The Azure CLI 2.0 has built-in help documentation, which you can access from the command line:

```bash
$ az [command-group [command]] -h
```

For example, to get information about all Azure Batch AI categories, use:

```bash
$ az batchai -h
```

To get help with the command to create a cluster, use:

```bash
$ az batchai cluster create -h
```

# Know You Azure CLI 2.0 Version

If you have a question or want to report a problem related to Azure CLI 2.0, please specify Azure CLI 2.0 and modules
versions.

```bash
$ az --version
```

Example of the output:

```
azure-cli (2.0.38)

...
batchai (0.3.0)
...
```

*Important*! This document covers Azure CLI with version not less than 2.0.38. This version allows you to work with the
latest Batch AI API version - 2018-05-01. Batch AI resources created with this version will not be accessible with older
version of Azure CLI. 

# Configuration

To work with Batch AI using Azure CLI 2.0 you need to perform the following steps:

- Login
```bash
$ az login
```

- Select account (if you have more than one subscription)

You can list all your accounts using the following command:
```bash
$ az account list -o table
```

Example output:

```
Name                         CloudName    SubscriptionId                        State    IsDefault
---------------------------  -----------  ------------------------------------  -------  -----------
Visual Studio Enterprise     AzureCloud   00000000-0000-0000-0000-000000000000  Enabled  True
Demo                         AzureCloud   00000000-0000-0000-0000-000000000000  Enabled
```

To select an account to be used with Azure CLI 2.0 run:

```bash
$ az account set -s "Visual Studio Enterprise"
```

- Register Microsoft.Batch and Microsoft.BatchAI providers
```bash
$ az provider register -n Microsoft.Batch
$ az provider register -n Microsoft.BatchAI
```

- Give Batch AI AD Network Contributor role on your subscription
```bash
$ az role assignment create --scope /subscriptions/<your subscription id> --role "Network Contributor" --assignee 9fcb3732-5f52-4135-8c08-9d4bbaf203ea
```
, here `9fcb3732-5f52-4135-8c08-9d4bbaf203ea` is the service principal of `Microsoft Azure BatchAI` in public cloud.

# Batch AI Resources Overview

## Resource Group

Azure Resource Group is a logical container for deploying and managing Azure resources. All Batch AI resources belong to
some Azure Resource group.

You need to create at least one Azure Resource Group to be able to work with Batch AI. To create a new resource group,
use the following az command replacing `eastus` and `demoGroup` with required location and resource group name.

```bash
$ az group create -l eastus -n demoGroup
```

Deletion of a resource group triggers deletion of all Azure resources associated with it. You can delete a resource
group running the following command:

```bash
$ as group delete -n demoGroup
```

## Batch AI Workspace

Batch AI Workspace is a logical container for deploying and managing Batch AI resources - clusters, file servers and
experiments. You can have up to 800 workspaces under a single resource group.

## Batch AI Cluster

Batch AI cluster is a compute cluster which can be used to run training jobs. All nodes in the cluster have same VM
size and OS image. Clusters are children resources of Batch AI workspace. Deletion of a parent workspace will trigger
deletion of all children clusters.

## Batch AI File Server   

Batch AI File Server is a single node NFS, which can be automatically mounted on cluster nodes. Same File Server can be
mounted by multiple Batch AI clusters. File Servers are children resources of Batch AI workspace. Deletion of a parent
workspace will trigger deletion of all children File Servers.

## Batch AI Experiment

Batch AI experiment is a logical container for deploying and managing training jobs. Experiments may contain any
training jobs running on different Batch AI clusters. Experiments are children resources of Batch AI workspace. Deletion
of a parent workspace will trigger deletion of all children experiments. Deletion of experiments triggers deletion of
all jobs created under the experiment.

There is no a limit on number of experiments created under a single workspace.

## Batch AI Job

Batch AI job represents a training job which will be run on a particular Batch AI cluster. Each Batch AI job has a
framework type associated with it - TensorFlow, Horovod, CNTK, Caffe, Caffe2, pyTorch, Chainer, custom mpi and custom.
Batch AI service takes cares about setting up required infrastructure and managing processes for running the job with
specified framework type. 

# Workspaces management

Azure CLI 2.0 allows you to create, delete and get information about workspaces.

## Creation

To create a Batch AI workspace you need to run `az batchai workspace` command providing location, parent resource group
and workspace name. All children resources under a workspace will be allocated in the same region as the workspace.

Example:
```bash
$ az batchai workspace create -l eastus -g demoGroup -n demoWorkspace
``` 

## Finding Information About Existing Workspaces

You can find all existing workspaces under the current subscription using the following command:

```bash
$ az batchai workspace list -o table
```

To find workspaces belonging to a particular resource group use the following command:

```bash
$ az batchai workspace list -g demoGroup -o table
```

To get detailed information about a workspace use the following command (replacing `demoGroup` and `demoWorkspace` with
required group and workspace name):

```bash
$ az batchai workspace show -g demoGroup -n demoWorkspace
```

# Deletion

To delete a workspace with all children clusters, file servers and experiment run the following command (replacing
`demoGroup` and `demoWorkspace` with required group and workspace name) and acknowledge the deletion:

```bash
$ az batchai workspace delete -g demoGroup -n demoWorkspace
```

To delete a workspace in non-interactive scenario (e.g. from a script), provide `-y` option to the command.

# Clusters Management

Azure CLI 2.0 allows you to create, resize, delete and get information about clusters.

## Creation

Please get familiar with `az batchai cluster create` command:

```bash
$ az batchai cluster create -h

```

output:

```text
Command
    az batchai cluster create: Create a cluster.

Arguments
    --name -n           [Required]: Name of cluster.
    --resource-group -g [Required]: Name of resource group. You can configure the default group
                                    using `az configure --defaults group=<name>`.
    --workspace -w      [Required]: Name of workspace.

Admin Account Arguments
    --generate-ssh-keys           : Generate SSH public and private key files in ~/.ssh directory
                                    (if missing).
    --password -p                 : Optional password for the admin user account to be created on
                                    each compute node.
    --ssh-key -k                  : Optional SSH public key value or path. If omitted and no
                                    password specified, default SSH key (~/.ssh/id_rsa.pub) will be
                                    used.
    --user-name -u                : Name of admin user account to be created on each compute node.
                                    If the value is not provided and no user configuration is
                                    provided in the config file, current user's name will be used.

Advanced Arguments
    --config-file -f              : A path to a json file containing cluster create parameters (json
                                    representation of
                                    azure.mgmt.batchai.models.ClusterCreateParameters).

Auto Storage Arguments
    --use-auto-storage            : If provided, the command will create a storage account in a new
                                    or existing resource group named "batchaiautostorage". It will
                                    also create Azure File Share with name "batchaishare", Azure
                                    Blob Container with name "batchaicontainer". The File Share and
                                    Blob Container will be mounted on each cluster node at
                                    $AZ_BATCHAI_MOUNT_ROOT/autoafs and
                                    $AZ_BATCHAI_MOUNT_ROOT/autobfs. If the resource group already
                                    exists and contains an approapriate storage account belonging to
                                    the same region as cluster, this command will reuse existing
                                    storage account.

Azure Storage Mount Arguments
    --afs-mount-path              : Relative mount path for Azure File share. The file share will be
                                    available at $AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path>
                                    folder.  Default: afs.
    --afs-name                    : Name of Azure File Share to be mounted on each cluster node.
                                    Must be used in conjunction with --storage-account-name.
                                    Multiple shares can be mounted using configuration file (see
                                    --config-file option).
    --bfs-mount-path              : Relative mount path for Azure Storage container. The container
                                    will be available at
                                    $AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path> folder.  Default:
                                    bfs.
    --bfs-name                    : Name of Azure Storage container to be mounted on each cluster
                                    node. Must be used in conjunction with --storage-account-name.
                                    Multiple containers can be mounted using configuration file (see
                                    --config-file option).
    --storage-account-key         : Storage account key. Required if the storage account belongs to
                                    a different subscription. Can be specified using
                                    AZURE_BATCHAI_STORAGE_KEY environment variable.
    --storage-account-name        : Storage account name for Azure File Shares and/or Azure Storage
                                    Containers to be mounted on each cluster node. Can be specified
                                    using AZURE_BATCHAI_STORAGE_ACCOUNT environment variable.

File Server Mount Arguments
    --nfs                         : Name or ARM ID of a file server to be mounted on each cluster
                                    node. You need to provide full ARM ID if the file server belongs
                                    to a different workspace. Multiple NFS can be mounted using
                                    configuration file (see --config-file option).
    --nfs-mount-path              : Relative mount path for NFS. The NFS will be available at
                                    $AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path> folder.  Default:
                                    nfs.

Nodes Arguments
    --custom-image                : ARM ID of a virtual machine image to be used for nodes creation.
                                    Note, you need to provide --image containing information about
                                    the base image used for this image creation.
    --image -i                    : Operation system image for cluster nodes. The value may contain
                                    an alias (UbuntuLTS, UbuntuDSVM) or specify image details in the
                                    form "publisher:offer:sku:version". If image configuration is
                                    not provided via command line or configuration file, Batch AI
                                    will choose default OS image.
    --max                         : Max nodes count for the auto-scale cluster.
    --min                         : Min nodes count for the auto-scale cluster.
    --target -t                   : Number of nodes which should be allocated immediately after
                                    cluster creation. If the cluster is in auto-scale mode, BatchAI
                                    can change the number of nodes later based on number of running
                                    and queued jobs.
    --vm-priority                 : VM priority.  Allowed values: dedicated, lowpriority.
    --vm-size -s                  : VM size for cluster nodes (e.g. Standard_NC6 for 1 GPU node).

Setup Task Arguments
    --setup-task                  : A command line which should be executed on each compute node
                                    when it's got allocated or rebooted. The task is executed in
                                    a bash subshell under root account.
    --setup-task-output           : Directory path to store where setup-task's logs. Note, Batch AI
                                    will create several helper directories under this path. The
                                    created directories are reported as stdOutErrPathSuffix by 'az
                                    cluster show' command.

Virtual Network Arguments
    --subnet                      : ARM ID of a virtual network subnet to put the cluster in.

Global Arguments
    --debug                       : Increase logging verbosity to show all debug logs.
    --help -h                     : Show this help message and exit.
    --output -o                   : Output format.  Allowed values: json, jsonc, table, tsv.
                                    Default: json.
    --query                       : JMESPath query string. See http://jmespath.org/ for more
                                    information and examples.
    --subscription                : Name or ID of subscription. You can configure the default
                                    subscription using `az account set -s NAME_OR_ID`".
    --verbose                     : Increase logging verbosity. Use --debug for full debug logs.

Examples
    Create a single node GPU cluster with default image and auto-storage account.
        az batchai cluster create -g MyResourceGroup -w MyWorkspace -n MyCluster \
            -s Standard_NC6 -t 1 --use-auto-storage --generate-ssh-keys


    Create a cluster with a setup command which installs unzip on every node, the command output
    will be stored on auto storage account Azure File Share.
        az batchai cluster create -g MyResourceGroup -w MyWorkspace -n MyCluster \
            --use-auto-storage \
            -s Standard_NC6 -t 1 -k id_rsa.pub \
            --setup-task 'sudo apt update; sudo apt install unzip' \
            --setup-task-output '$AZ_BATCHAI_MOUNT_ROOT/autoafs'


    Create a cluster providing all parameters manually.
        az batchai cluster create -g MyResourceGroup -w MyWorkspace -n MyCluster \
            -i UbuntuLTS -s Standard_NC6 --vm-priority lowpriority \
            --min 0 --target 1 --max 10 \
            --storage-account-name MyStorageAccount \
            --nfs-name MyNfsToMount --afs-name MyAzureFileShareToMount \
            --bfs-name MyBlobContainerNameToMount \
            -u AdminUserName -k id_rsa.pub -p ImpossibleToGuessPassword


    Create a cluster using a configuration file.
        az batchai cluster create -g MyResourceGroup -w MyWorkspace -n MyCluster -f cluster.json
```

### Create Clusters Using Command Line Arguments

In most cases, it's possible to create a new cluster using command line arguments without any configuration file.

In simplest case, to create a cluster you need to specify resource group name, workspace name, cluster name, VM size of
the cluster nodes (all nodes in the cluster have the same VM size), OS image to be used on cluster nodes (all nodes in
the cluster have the same OS image)  and size of the cluster. For example the following command will create a cluster
with 2 Ubuntu LTS nodes with size Standard_NC6 (6 CPU and one GPU), Batch AI will create an admin user on each node
using your current user name and generated ssh key (if you already have a default ssh key pair at ~/.ssh/id_rsa and
~/.ssh/id_rsa.pub, it will be used instead):

```bash
$ az batchai cluster create -g demoGroup -w demoWorkspace -n demoCluster -t 2 -s Standard_NC6 -i UbuntuLTS --generate-ssh-keys
```

The following sections will describe other options available during cluster creation.

#### Admin User Account

Batch AI creates an admin user account on each compute node allowing you to perform SSH access to the nodes.

You can specify the name for the account using `-u` option. If this option is not provided, Azure CLI will use your
current user name.

The admin user account requires you to provide a password and/or SSH public key which you will be able to use to SSH to
the node. If none has been provided, the Azure CLI will use your default SSH public key from ~/.ssh/id_rsa.pub. If you
have no default SSH key pair, you can generate one providing `--generate-ssh-keys` option.

You can specify admin account password using `-p` option.

You can specify a value or a path to SSH public key using `-k` option.

#### VM Size

You need to specify VM size for compute nodes in the cluster using `-s` option (e.g. `-i Standard_NC6` for one GPU VM).
You can find the list of available VM sizes in particular region using `az vm list-sizes -l eastus  -o table` command by
replacing `eastus` to required region name. Batch AI service supports all Azure VM sizes available in a region except
`STANDARD_A0` and those with premium storage (`STANDARD_GS`, `STANDARD_DS`, and `STANDARD_DSV2` series).

#### VM Priority

Batch AI support cluster of dedicated and low-priority nodes. Dedicated VM remain in cluster until its deleted or
scaled-down. Low-priority VMs provides a cheap alternative but can be preempted at any moment. But default, Batch AI
creates cluster with dedicated VMs. You can create a cluster of low-priority VMs by specifying `---vm-priority lowpriority`
option.

Note, you have independent quota for dedicated and low-priority cores.

#### OS Image

You can either specify one of preconfigured OS images or specify image configuration manually using `-i` option.

Preconfigured OS images are UbuntuLTS (for the latest supported Ubuntu LTS image) and UbuntuDSVM (for the latest
supported Data Science Ubuntu VM).

To specify OS image manually, provide `-i` option with "publisher:offer:sku:version" value, for example 
`-i "Canonical:UbuntuServer:16.04_LTS:latest"`. Note, at this point Batch AI supports only Ubuntu based OS images.

You can use Ubuntu derived custom image with Batch AI service. You need to create a snapshot of an image and provide its
ARM resource ID via `--custom-image` parameter. In addition, you need to provide `-i` option describing the base image
you used to create the snapshot from. Note, its highly recommended to create custom image using the same VM size as you
are going to use in clusters. 

 
#### Cluster Size

Batch AI supports manual and auto-scale clusters. You can change the type of the existing cluster at any moment.

##### Manual Scale Cluster

You can use specify the number of nodes in manual scale cluster using `-t` option. Batch AI will try to allocate the
requested number of nodes during cluster creation.

You can change the number of nodes in an existing cluster using `az batchai cluster resize` command.

*Note*, the number of nodes in a cluster can actually be less than the requested value if you reached your cores quota
limit.

##### Auto-Scale Cluster

Batch AI can automatically change the number of nodes in the cluster based on the load - number of nodes required by 
running and queued jobs. To enable auto-scale, you need to provide the minimum and maximum number of nodes for cluster
using `--min` and `--max` options. Batch AI will not scale the cluster below or above of these values.

*Note*, the number of nodes in a cluster can actually be less than --min option if you reached your cores quota limit.

You can use `-t` option to specify the initial number of nodes in the cluster - Batch AI will try to allocated requested
number of nodes during cluster creation.

#### Mounting Azure File Share and Storage Container

You can configure a cluster to automatically mount Azure File Share and/or Storage Container on each node during cluster
creation. This allows jobs to access training data stored on Azure Storage and to store its output (logs and models)
on Azure Storage.

To use this option you need to create a storage account, file share and/or container and provide their information
during cluster creation.

For example, the following commands will create a new resource group `demoGroup`, new storage account `demobatchaicli`,
file share with name `demoafs` and container with name `democontainer` in EastUS and will create a cluster with Azure
File Share mounted at $AZ_BATCHAI_MOUNT_ROOT/azurefileshare and the container mounted at 
$AZ_BATCHAI_MOUNT_ROOT/azurecontainer:

```bash
$ az group create -l eastus -n demoGroup
$ az storage account create -l eastus -g demoGroup -n demobatchaicli
$ az storage share create -n demoafs --account-name demobatchaicli
$ az storage container create -n democontainer --account-name batchaiclidemo
$ az batchai cluster create -g demoGroup -w demoWorkspace -n demoCluster --storage-account-name demobatchaicli --afs-name demoafs --afs-mount-path azurefileshare --bfs-name democontainer --bfs-mount-path azurecontainer -s Standard_NC6 -i UbuntuLTS -t 1 --generate-ssh-keys
```

Note, storage account name must have an unique value, otherwise storage account creation command will fail with 
`The storage account named demobatchaicli is already taken.` error message.

`AZ_BATCHAI_MOUNT_ROOT` is an environment variable set by Batch AI for each job, its value depends on the image
used for nodes creation. For example, on Ubuntu based images it's equal to `/mnt/batch/tasks/shared/LS_root/mounts`.

If you want to use Azure File Share or Azure Container belonging to a storage account created in a different subscription,
provide `--storage-account-key` argument containing a key for that storage account. Optionally, you can provide storage
account name and key using `AZURE_BATCHAI_STORAGE_ACCOUNT` and `AZURE_BATCHAI_STORAGE_KEY` environment variables.

You can provide only one Azure File Share and/or Azure Container via command line arguments. Please use Cluster
Configuration File if you need to mount more file systems.

Note, Azure Container specified with `--container-name` argument will be mounted with the following mount options:
```text
--use-https=true -o big_writes -o max_read=131072 -o max_write=131072 -o attr_timeout=240 -o fsname=blobfuse -o kernel_cache -o entry_timeout=240 -o negative_timeout=120 -o allow_other
```

You need to use Cluster Configuration File (described below) to use different mount options.

##### Auto-Storage Account

Azure CLI provides a shortcut for mounting the same storage account in all clusters in a region by using `--use-auto-storage`
option. If this option provided, Azure CLI will create (or use existing) `batchaiautostorage` resource group with a storage
account for each region you used it. Each storage account will have `batchaishare` Azure File Share and `batchaicontainer`
blob storage container. Those share and container will be mounted on each node at `$AZ_BATCHAI_MOUNT_ROOT/autoafs` and
`$AZ_BATCHAI_MOUNT_ROOT/autobfs`. 

#### Mounting NFS

Azure File Shares and Azure Containers provide a convenient and cheap way to store input and output data for jobs.
Another storage option available in Batch AI is a single node NFS (Batch AI File Server). This option is more expensive
as you need to pay both for compute resources used by NFS and for storage disks, but it can give a better performance
in some situations (depending on data access patterns).

To use this option you need to create a single node NFS using `az batchai file-server create` command as described in
[File Server](#single-node-nfs) section below and provide it's name via `--nfs` command line argument during cluster creation.

If Batch AI File Server and Batch AI Cluster belong to the same workspace, it's enough to provide File Server name,
otherwise you need to specify ARM resource ID of the File Server.

For example, the following code will create a single node NFS `demoNFS` with 2 disks (1024Gb each) and a single node GPU 
cluster `demoCluster` with NFS mounted at `$AZ_BATCHAI_MOUNT_ROOT/nfs`:

```bash
$ az batchai file-server create -g demoGroup -w demoWorkspace -n demoNFS --disk-count 4 --disk-size 1024 -s Standard_DS14 --generate-ssh-keys
$ az batchai cluster create -g demoGroup -w demoWorkspace -n demoCluster --nfs demoNFS --nfs-mount-path nfs -s Standard_NC6 -i UbuntuLTS -t 1
```

*Important*. Each Batch AI File Server resides within a Azure virtual network. If `--nfs` option is provided, the cluster
will be created in the same subnet as the File Server and will be a subject to the NSG rules configured on the subnet.
Another circumstances of mounting a File Server is that all clusters mounting the same File Server are created in the
same virtual network and subnet. You can use `--subnet` option to specify a virtual network and subnet for the cluster
explicitly. Batch AI will still require clusters and File Servers to be in the same vnet.

#### Subnet

You can specify virtual network to put the cluster in using providing `--subnet` option with ARM ID of the subnet. For
example:

```text
-subnet /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/demoGroup/providers/Microsoft.Network/virtualNetworks/demoVnet/subnets/demoSubnet
```

It's important to plan your network configuration if you are going to use multiple File Servers or Unmanaged File Systems
with the same cluster. It can be a good idea to put all File Servers and clusters in the same vnet even if you are not
going to mount File Servers during cluster creation because it will allow you to mount File Servers during job creation. 

#### Setup Task

Batch AI can automatically execute a specified command line on each cluster node when it's been allocated or rebooted.
Such command line can be used to install additional packages, start daemons or download commonly used data on each node.

You can specify the command line to be executed using `--setup-task` argument. The command will be executed under a bash
subshell under root account.

The standard and error output of the startup task will stored at location specified by `--setup-task-output` option,
which is required if `--setup-task` option provided.

For example, the following command will create a cluster with mounted auto-storage account and make each node to install
`unzip` package using setup task, the output of the setup tasks will be stored on auto-storage Azure File Share:

```bash
$ az batchai cluster create -g demoGroup -w demoWorkspace -n demoCluster -t 2 -s Standard_NC6 -i UbuntuLTS \
  --generate-ssh-keys --use-auto-storage \
  --setup-task 'apt install unzip -y' --setup-task-output '$AZ_BATCHAI_MOUNT_ROOT/autoafs'
```

Note, the Batch AI will create several helper folders to separate output files from different clusters, the created
folders will be reported in cluster creation output of in `az batchai cluster show` output in
`nodeSetup.setupTask.stdOutErrPathSuffix` attribute, e.g.: 

```json
{
  "comment": "some other params",
  "nodeSetup": {
    "comment": "some other params",
    "setupTask": {                                                                                                                                                                                                 
      "commandLine": "apt install unzip -y",                                                                                                                                      
      "environmentVariables": null,                                                                                                                                                                                
      "secrets": null,                                                                                                                                                                                             
      "stdOutErrPathPrefix": "$AZ_BATCHAI_MOUNT_ROOT/autoafs",                                                                                                                                                         
      "stdOutErrPathSuffix": "<your subscription id>/demoGroup/workspaces/demoWorkspace/clusters/demoCluster/<UUID>"                                                                
    }
  },
  "comment2": "the rest of params"
}
```

You can use combination of `stdOutErrPathPrefix` and `stdOutErrPathSuffix` to find the generated files on the node or in
the storage.

Alternatively, you can list the files (and download URLs) generated by setup task using `az batchai cluster file list`
command, e.g:

```bash
$ az batchai cluster file list -o table -g demoGroup -w demoWorkspace -c demoCluster
```

### Using Cluster Configuration File

There are several scenarios (described below) which require you to use Cluster Configuration File for cluster creation.

Cluster Configuration File is a json file containing ClusterCreateParameters object as defined by swagger specification
available at [Azure/azure-rest-api-specs github](https://github.com/Azure/azure-rest-api-specs/blob/current/specification/batchai/resource-manager/Microsoft.BatchAI/2018-05-01/BatchAI.json).

To create a cluster using using Cluster Configuration File use `az batchai cluster create` command with `-f` option.
Note, the command line arguments provided on command line (e.g. VM size, image, scaling options and admin account) will
overwrite the corresponding options defined in the configuration file.

Batch AI GitHub contains json validation schema `https://raw.githubusercontent.com/Azure/BatchAI/master/schemas/2018-05-01/cluster.json`
which can be used for cluster configuration validation and enabling auto-completion support in editors having this
feature (e.g. VS Code, pyCharm, etc). If you are using VS Code it's enough to add "$schema" attribute into the json file,
e.g.

```json
{
    "$schema": "https://raw.githubusercontent.com/Azure/BatchAI/master/schemas/2018-05-01/cluster.json",
    "properties": {
      "comment": "cluster creation parameters"
    }
}
```

See documentation for your editor of choice to check how to enable JSON schema validation in it.

The following sessions describe how to use Cluster Configuration File for different scenarios.

#### Provide Environment Variables and Secrets for Setup Task

You can specify a list of environment variables for the cluster setup using a configuration file like this:

```json
{
    "$schema": "https://raw.githubusercontent.com/Azure/BatchAI/master/schemas/2018-05-01/cluster.json",
    "properties": {
        "nodeSetup": {
            "setupTask": {
                "commandLine": "$AZ_BATCHAI_MOUNT_ROOT/afs/setup_script.sh",
                "stdOutErrPathPrefix": "$AZ_BATCHAI_MOUNT_ROOT/afs",
                "environmentVariables": [
                    {
                        "name": "VARIABLE1", "value": "Value 1"
                    },
                    {
                        "name": "VARIABLE2", "value": "Value 2"
                    }
                ],
                "secrets": [
                    {
                        "name": "VARIABLE3", "value": "Value 3"
                    },
                    {
                        "name": "VARIABLE4",
                        "valueSecretReference": {
                            "sourceVault": {
                                "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/demoGroup/providers/Microsoft.KeyVault/vaults/demokeyvault"
                            },
                            "secretUrl": "https://demokeyvault.vault.azure.net/secrets/nameofsecter"
                        }
                    }
                ]
            }
        }
    }
}
```

This configuration file specifies the setup task (`setup_script.sh` located on mounted Azure File Share), the output
directory for setup task and set of environment variables and secrets which will be available to the setup task during
execution via environment variables `$VARIABLE1`-`$VARIABLE4`.

Secrets are environment variable those values will not be reported by server in cluster get requests and which allows
you to provide values directly via `value` attribute or via Azure KeyVault secrets. For information about storing secrets
in Azure KeyVault please refer to [Using KeyVault for Storing Secrets](#using-keyvault-for-storing-secrets) section of
this document.

The following command shows usage of this configuration file (`cluster.json`) to create a cluster:
 
```bash
$ az cluster create -g demoGroup -w demoWorkspace -n demoCluster -t 1 -s Standard_NC6 --storage-account-name demobatchaicli --afs-name demoafs --afs-mount-path afs --generate-ssh-keys -f cluster.json
```

#### Mounting Multiple File Systems

You can mount multiple file system using the configuration file like this:

```json
{
    "$schema": "https://raw.githubusercontent.com/Azure/BatchAI/master/schemas/2018-05-01/cluster.json",
    "properties": {
        "nodeSetup": {
            "mountVolumes": {
                "azureFileShares": [
                    {
                        "accountName": "<AZURE_BATCHAI_STORAGE_ACCOUNT>",
                        "azureFileUrl": "https://<AZURE_BATCHAI_STORAGE_ACCOUNT>.file.core.windows.net/dataset1",
                        "credentials": {
                            "accountKey": "<AZURE_BATCHAI_STORAGE_KEY>"
                        },
                        "directoryMode": "0777",
                        "fileMode": "0777",
                        "relativeMountPath": "afs1"
                    },
                    {
                        "accountName": "<AZURE_BATCHAI_STORAGE_ACCOUNT>",
                        "azureFileUrl": "https://<AZURE_BATCHAI_STORAGE_ACCOUNT>.file.core.windows.net/dataset2",
                        "credentials": {
                            "accountKey": "<AZURE_BATCHAI_STORAGE_KEY>"
                        },
                        "directoryMode": "0777",
                        "fileMode": "0777",
                        "relativeMountPath": "afs2"
                    }
                ],
                "azureBlobFileSystems": [
                    {
                        "containerName": "dataset1",
                        "relativeMountPath": "bfs1",
                        "accountName": "<AZURE_BATCHAI_STORAGE_ACCOUNT>",
                        "mountOptions": "",
                        "credentials": {
                            "accountKey": "<AZURE_BATCHAI_STORAGE_KEY>"
                        }
                    },
                    {
                        "containerName": "dataset2",
                        "relativeMountPath": "bfs2",
                        "accountName": "<AZURE_BATCHAI_STORAGE_ACCOUNT>",
                        "mountOptions": "",
                        "credentials": {
                            "accountKey": "<AZURE_BATCHAI_STORAGE_KEY>"
                        }
                    }
                ],
                "fileServers": [
                    {
                        "fileServer": {
                            "id": "<ARM ID of Batch AI File Server>"
                        },
                        "relativeMountPath": "nfs1",
                        "mountOptions": "rw"
                    },
                    {
                        "fileServer": {
                            "id": "<ARM ID of another Batch AI file Server>"
                        },
                        "relativeMountPath": "nfs2",
                        "mountOptions": "rw"
                    }
                ],
                "unmanagedFileSystems": [
                    {
                        "mountCommand": "mount -t glusterfs 10.0.0.4:/gv0",
                        "relativeMountPath": "glusterfs"
                    }
                ]
            }
        }
    }
}
```

You can provide values for `accountName` and `accountKey` directly in the file, or use `<AZURE_BATCHAI_STORAGE_ACCOUNT>`
and `<AZURE_BATCHAI_STORAGE_KEY>` placeholders which will be replaced by `az` with storage account information provided 
via `--storage-account-name` and (optionally) `--storage-account-key` command line arguments.

Note, if no mount options are provided for Azure Blob File System (Azure Containers), the following default options will
be used (same options are used if Azure Container is specified via `--bfs-name` argument):

```bash
--use-https=true -o big_writes -o max_read=131072 -o max_write=131072 -o attr_timeout=240 -o fsname=blobfuse -o kernel_cache -o entry_timeout=240 -o negative_timeout=120 -o allow_other
```

You can find more information about the recommended options at
[Azure/azure-storage-fuse](https://github.com/Azure/azure-storage-fuse) github page.

Instead of providing storage account key via environment variables or in the config file, you may prefer to share it
with Batch AI using KeyVault as described in [Using KeyVault for Storing Secrets](#using-keyvault-for-storing-secrets) section.

#### Mounting Unmanaged File Systems

Batch AI allows you to mount your own NFS, cifs or GlusterFS clusters using configuration file. It's recommended to create
GPU and storage clusters in the same vnet and use private IP addresses for mounting storage clusters.

For example, you can create a [GlusterFS using Batch Shipyard](https://github.com/Azure/batch-shipyard/tree/master/recipes/RemoteFS-GlusterFS)
and mount it on Batch AI nodes by creating a cluster.json file like this:

```json
{
    "properties": {
        "nodeSetup": {
            "mountVolumes": {
                "unmanagedFileSystems": [
                    {
                        "mountCommand": "mount -t glusterfs 10.0.0.4:/gv0",
                        "relativeMountPath": "glusterfs"
                    }
                ]
            }
        },
        "subnet": {
            "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/gluster/providers/Microsoft.Network/virtualNetworks/myvnet/subnets/my-server-subnet"
        }
    }
}
```

where `10.0.0.4` is a private IP of any GlusterFS node, `gv0` is the default volume name used by Batch Shipyard and
`subnet.id` is an ID of vnet subnet created by Batch Shipyard during GlusterFS creation.

Note, all NFSes and Unmanaged File Systems mounted to a cluster using private IP addresses must be in the same vnet subnet.
   
## Monitoring Clusters

You can get a list of Batch AI clusters under a workspace using the following command:

```bash
$ az batchai cluster list -o table -g demoGroup -w demoWorkspace
```

Example output:
```
Name           Resource Group    Workspace  VM Size       State      Idle    Running    Preparing    Leaving    Unusable
-------------  ----------------  ---------  ------------  -------  ------  ---------  -----------  ---------  ----------
dsvm           demoGroup         demoWks    STANDARD_D1   steady        1          0            0          0           0
democluster    demoGroup         demoWks    STANDARD_NC6  steady        0          0            1          0           0
```

, where:
- State - current state of the cluster: steady, resizing, deleting;
- Idle - number of idling nodes ready to execute jobs;
- Running - number of nodes currently executing jobs;
- Preparing - number of recently allocated nodes which perform preparation tasks (e.g drivers installation, mounting
file system, running startup task);
- Leaving - number of nodes which are leaving the cluster because of scale down or resizing command;
- Unusable - number of nodes in unusable state (e.g. nodes which failed preparation or startup tasks).

To get detailed information about a cluster use `az batchai cluster show` command. For example:

```bash
$ az batchai cluster show -g demoGroup -w demoWorkspace -n demoCluster
```
  
Sample output:
```json
{
  "allocationState": "steady",                                                                                                                                                                                     
  "allocationStateTransitionTime": "2018-06-21T17:15:18.288000+00:00",                                                                                                                                             
  "creationTime": "2018-06-21T17:13:07.848000+00:00",                                                                                                                                                              
  "currentNodeCount": 2,                                                                                                                                                                                           
  "errors": null,                                                                                                                                                                                                  
  "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/demoGroup/providers/Microsoft.BatchAI/workspaces/demoWorkspace/clusters/demoCluster",                                                               
  "name": "demoCluster",                                                                                                                                                                                            
  "nodeSetup": {                                                                                                                                                                                                   
    "mountVolumes": {                                                                                                                                                                                              
      "azureBlobFileSystems": [                                                                                                                                                                                    
        {                                                                                                                                                                                                          
          "accountName": "baibekzxwtqryuh",                                                                                                                                                                        
          "containerName": "batchaicontainer",                                                                                                                                                                     
          "credentials": {                                                                                                                                                                                         
            "accountKey": null,                                                                                                                                                                                    
            "accountKeySecretReference": null                                                                                                                                                                      
          },                                                                                                                                                                                                       
          "mountOptions": null,                                                                                                                                                                                    
          "relativeMountPath": "autobfs"                                                                                                                                                                           
        }                                                                                                                                                                                                          
      ],                                                                                                                                                                                                           
      "azureFileShares": [                                                                                                                                                                                         
        {                                                                                                                                                                                                          
          "accountName": "apgslurmeu",                                                                                                                                                                             
          "azureFileUrl": "https://apgslurmeu.file.core.windows.net/slurm",                                                                                                                                        
          "credentials": {                                                                                                                                                                                         
            "accountKey": null,                                                                                                                                                                                    
            "accountKeySecretReference": null                                                                                                                                                                      
          },                                                                                                                                                                                                       
          "directoryMode": "0777",                                                                                                                                                                                 
          "fileMode": "0777",                                                                                                                                                                                      
          "relativeMountPath": "afs"                                                                                                                                                                               
        },                                                                                                                                                                                                         
        {                                                                                                                                                                                                          
          "accountName": "baibekzxwtqryuh",                                                                                                                                                                        
          "azureFileUrl": "https://baibekzxwtqryuh.file.core.windows.net/batchaishare",                                                                                                                            
          "credentials": {                                                                                                                                                                                         
            "accountKey": null,                                                                                                                                                                                    
            "accountKeySecretReference": null                                                                                                                                                                      
          },                                                                                                                                                                                                       
          "directoryMode": "0777",                                                                                                                                                                                 
          "fileMode": "0777",                                                                                                                                                                                      
          "relativeMountPath": "autoafs"                                                                                                                                                                           
        }                                                                                                                                                                                                          
      ],                                                                                                                                                                                                           
      "fileServers": null,                                                                                                                                                                                         
      "unmanagedFileSystems": null                                                                                                                                                                                 
    },
    "performanceCountersSettings": null,
    "setupTask": {
      "commandLine": "$AZ_BATCHAI_MOUNT_ROOT/afs/config/gpu_worker_setup.sh",
      "environmentVariables": null,
      "secrets": null,
      "stdOutErrPathPrefix": "$AZ_BATCHAI_MOUNT_ROOT/afs",
      "stdOutErrPathSuffix": "0000000-0000-0000-0000-00000000/demoGroup/workspaces/demoWorkspace/clusters/demoCluster/ec1936c8-41e9-4dbe-ac8a-120bcbd3b29b"
    }
  },
  "nodeStateCounts": {
    "idleNodeCount": 2,
    "leavingNodeCount": 0,
    "preparingNodeCount": 0,
    "runningNodeCount": 0,
    "unusableNodeCount": 0
  },
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2018-06-21T17:13:09.235000+00:00",
  "resourceGroup": "demoGroup",
  "scaleSettings": {
    "autoScale": null,
    "manual": {
      "nodeDeallocationOption": "requeue",
      "targetNodeCount": 2
    }
  },
  "subnet": {
    "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/demoGroup/providers/Microsoft.Network/virtualNetworks/demovnet/subnets/demosubnet",
    "resourceGroup": "demoGroup"
  },
  "type": "Microsoft.BatchAI/workspaces/clusters",
  "userAccountSettings": {
    "adminUserName": "myuser",
    "adminUserPassword": null,
    "adminUserSshPublicKey": "ssh-rsa AAAAB3N..."
  },
  "virtualMachineConfiguration": {
    "imageReference": {
      "offer": "UbuntuServer",
      "publisher": "Canonical",
      "sku": "16.04-LTS",
      "version": "latest",
      "virtualMachineImageId": null
    }
  },
  "vmPriority": "dedicated",
  "vmSize": "STANDARD_NC6"
}

```

## Working with Cluster Nodes

You can get information about the nodes belonging to the cluster using `az batchai cluster list-nodes` command:

```bash
$ az batchai cluster node list -g demoGroup -w demoWorkspace -c demoCluster
```

Example output:

````json
[
  {
    "ipAddress": "168.61.39.164",
    "nodeId": "tvm-1915592855_1-20180621t171517z",
    "port": 50000.0
  },
  {
    "ipAddress": "168.61.39.164",
    "nodeId": "tvm-1915592855_2-20180621t171517z",
    "port": 50001.0
  }
]
````

, where:
- ID - node id (used as suffix in file names for standard and error output of setup tasks);
- IP - public IP of the node;
- port - SSH port of the node.

GNU/Linux users can ssh to the node using the following command:

```bash
$ ssh 52.168.39.226 -p 50000
```

In addition, Batch AI provides a command to execute an arbitrary command line on a cluster node with optional ports
forwarding:

```bash
$ az batchai cluster node exec -h
```

output:

```text
Command
    az batchai cluster node exec: Executes a command line on a cluster's node with optional ports
    forwarding.

Arguments
    --cluster -c        [Required]: Name of cluster.
    --resource-group -g [Required]: Name of resource group. You can configure the default group
                                    using `az configure --defaults group=<name>`.
    --workspace -w      [Required]: Name of workspace.
    --address -L                  : Specifies that connections to the given TCP port or Unix socket
                                    on the local (client) host are to be forwarded to the given host
                                    and port, or Unix socket, on the remote side. e.g. -L
                                    8080:localhost:8080.
    --exec                        : Optional command line to be executed on the node. If not
                                    provided, the command will perform ports forwarding only.
    --node-id -n                  : ID of the node to forward the ports to. If not provided, the
                                    command will be executed on the first available node.
    --password -p                 : Optional password to establish SSH connection.
    --ssh-private-key -k          : Optional SSH private key path to establish SSH connection. If
                                    omitted, the default SSH private key will be used.

Global Arguments
    --debug                       : Increase logging verbosity to show all debug logs.
    --help -h                     : Show this help message and exit.
    --output -o                   : Output format.  Allowed values: json, jsonc, table, tsv.
                                    Default: json.
    --query                       : JMESPath query string. See http://jmespath.org/ for more
                                    information and examples.
    --subscription                : Name or ID of subscription. You can configure the default
                                    subscription using `az account set -s NAME_OR_ID`".
    --verbose                     : Increase logging verbosity. Use --debug for full debug logs.

Examples
    Report a snapshot of the current processes.
        az batchai cluster node exec -g MyResourceGroup -w MyWorkspace -c MyCluster \
            -n tvm-xxx --exec "ps axu"


    Report a GPU information for a node.
        az batchai cluster node exec -g MyResourceGroup -w MyWorkspace -c MyCluster \
            -n tvm-xxx --exec "nvidia-smi"


    Forward local 9000 to port 9001 on the node.
        az batchai cluster node exec -g MyResourceGroup -w MyWorkspace -c MyCluster \
            -n tvm-xxx -L 9000:localhost:9001
```

## Resizing Clusters

You can resize a cluster at any time using `az batchai cluster resize` command.
For example, the following command will resize `demoCluster` to have no nodes:

```bash
$ az batchai cluster resize -g demoGroup -w demoWorksapce -n demoCluster -t 0
```

You can also switch a cluster into auto-scale mode using `az batchai cluster auto-scale`
command. For example, the following command will setup auto-scale mode for `demoCluster` and Batch AI
will scale the cluster automatically between 0 and 10 nodes depending on the number of running and pending jobs:

```bash
$ az batchai cluster auto-scale -g demoGroup -w demoWorkspace --min 0 --max 10
```

## Deleting Clusters

You can delete the cluster using `az batchai cluster delete` command, e.g.

```bash
$ az batchai cluster delete -g demoGroup -w demoWorkspace -n demoCluster
```

Note, the command will ask you for confirmation and may take a significant time to complete. You can provide `-y` option
to skip the confirmation (e.g. this command is a part of non-interactive script). You can provide `--no-wait` option to
skip waiting for the deletion completion (useful if you need to delete multiple resources simultaneously).

# Experiments Management

Azure CLI 2.0 allows you to create, delete and get information about Batch AI experiments using `az batchai experiment`
command group:

```bash
$ az batchai experiment -h
```

output:

```text
Group
    az batchai experiment: Commands to manage experiments.

Commands:
    create: Create an experiment.
    delete: Delete an experiment.
    list  : List experiments.
    show  : Show information about an experiment.
```

# Jobs Management

Azure CLI 2.0 allows you to submit, terminate, delete and get information about Batch AI training jobs.

Please use take look at integrated help to get familiar with jobs related commands:

```bash
$ az batchai job --help
```

Output:

```
Group
    az batchai job: Commands to manage jobs.

Subgroups:
    file     : Commands to list and stream files in job's output directories.
    node     : Commands to work with nodes which executed a job.

Commands:
    create   : Create a job.
    delete   : Delete a job.
    list     : List jobs.
    show     : Show information about a job.
    terminate: Terminate a job.
    wait     : Waits for specified job completion and setups the exit code to the job's exit code.
```

## Creation

To create and submit a job use `az batchai job create command`:

```bash
$ az batchai job create -h
```

Output:
```
Command
    az batchai job create: Create a job.

Arguments
    --cluster -c        [Required]: Name or ARM ID of the cluster to run the job. You need to
                                    provide ARM ID if the cluster belongs to a different workspace.
    --config-file -f    [Required]: A path to a json file containing job create parameters (json
                                    representation of
                                    azure.mgmt.batchai.models.JobCreateParameters).
    --experiment -e     [Required]: Name of experiment.
    --name -n           [Required]: Name of job.
    --resource-group -g [Required]: Name of resource group. You can configure the default group
                                    using `az configure --defaults group=<name>`.
    --workspace -w      [Required]: Name of workspace.

Azure Storage Mount Arguments
    --afs-mount-path              : Relative mount path for Azure File Share. The File Share will be
                                    available at $AZ_BATCHAI_JOB_MOUNT_ROOT/<relative_mount_path>
                                    folder.  Default: afs.
    --afs-name                    : Name of Azure File Share to mount during the job execution. The
                                    File Share will be mounted only on the nodes which are executing
                                    the job. Must be used in conjunction with --storage-account-
                                    name.  Multiple shares can be mounted using configuration file
                                    (see --config-file option).
    --bfs-mount-path              : Relative mount path for Azure Storage Blob Container. The
                                    container will be available at
                                    $AZ_BATCHAI_JOB_MOUNT_ROOT/<relative_mount_path> folder.
                                    Default: bfs.
    --bfs-name                    : Name of Azure Storage Blob Container to mount during the job
                                    execution. The container will be mounted only on the nodes which
                                    are executing the job. Must be used in conjunction with
                                    --storage-account-name. Multiple containers can be mounted using
                                    configuration file (see --config-file option).
    --storage-account-key         : Storage account key. Required if the storage account belongs to
                                    a different subscription. Can be specified using
                                    AZURE_BATCHAI_STORAGE_KEY environment variable.
    --storage-account-name        : Storage account name for Azure File Shares and/or Azure Storage
                                    Containers to be mounted on each cluster node. Can be specified
                                    using AZURE_BATCHAI_STORAGE_ACCOUNT environment variable.

File Server Mount Arguments
    --nfs                         : Name or ARM ID of the file server to be mounted during the job
                                    execution. You need to provide ARM ID if the file server belongs
                                    to a different workspace. You can configure multiple file
                                    servers using job's  configuration file.
    --nfs-mount-path              : Relative mount path for NFS. The NFS will be available at
                                    $AZ_BATCHAI_JOB_MOUNT_ROOT/<relative_mount_path> folder.
                                    Default: nfs.

Global Arguments
    --debug                       : Increase logging verbosity to show all debug logs.
    --help -h                     : Show this help message and exit.
    --output -o                   : Output format.  Allowed values: json, jsonc, table, tsv.
                                    Default: json.
    --query                       : JMESPath query string. See http://jmespath.org/ for more
                                    information and examples.
    --subscription                : Name or ID of subscription. You can configure the default
                                    subscription using `az account set -s NAME_OR_ID`".
    --verbose                     : Increase logging verbosity. Use --debug for full debug logs.

Examples
    Create a job to run on a cluster in the same resource group.
        az batchai job create -g MyResourceGroup -w MyWorkspace -e MyExperiment -n MyJob \
            -r MyCluster -f job.json


    Create a job to run on a cluster in a different workspace.
        az batchai job create -g MyJobResourceGroup -w MyJobWorkspace -e MyExperiment -n MyJob \
            -f job.json \
            -r "/subscriptions/00000000-0000-0000-0000-000000000000/"\
            "resourceGroups/MyClusterResourceGroup"\
            "/providers/Microsoft.BatchAI/workspaces/MyClusterWorkspace/clusters/MyCluster"
```

To create a job you need to specify resource group, workspace, experiment, job name, cluster to run the job and provide
a job configuration file.

For example,

```bash
$ az batchai job create -g demoGroup -w demoWorkspace -e demoExperiment -n demoJob -c demoCluster -f job.json 
```

will submit a new job `demoJob` to be run on `demoCluster` cluster from `demoWorkspace` workspace, the job configuration
will be read from job.json file.

You can use submit a job on a cluster in a different workspace providing fully qualified ARM ID of the cluster:

```bash
$ az batchai job create -g demoGroup -w demoWorkspace -e demoExperiment -n demoJob \
            -f job.json \
            -r "/subscriptions/00000000-0000-0000-0000-000000000000/"\
            "resourceGroups/clusterResourceGroup"\
            "/providers/Microsoft.BatchAI/workspaces/clusterWorkspace/clusters/cluster" 
```
 

### Job Configuration File

Job configuration file is a json file containing `JobCreateParameters` object as defined by swagger spec available at
[Azure/azure-rest-api-specs GitHub](https://github.com/Azure/azure-rest-api-specs/blob/master/specification/batchai/resource-manager/Microsoft.BatchAI/stable/2018-05-01/BatchAI.json).

Batch AI GitHub provides a set of job JSON schema validation files available at https://github.com/Azure/BatchAI/tree/master/schemas/2018-05-01.
These schemas can be used for job configuration validation and enabling auto-completion support in editors having this
feature (e.g. VS Code, pyCharm, etc). If you are using VS Code it's enough to add "$schema" attribute into the json file,
e.g.

```json
{
    "$schema": "https://raw.githubusercontent.com/Azure/BatchAI/master/schemas/2018-05-01/<toolkit type>.json",
    "properties": {
      "comment": "Job creation parameters"
    }
}
```

Job configuration file defines framework specific parameters, number of nodes required for job execution, description of
input and output directories, docker container to run the job and job preparation steps. The following sections
describes all those parameters in details. Here is a job configuration file which we will use as a reference:

```json
{
    "$schema": "https://raw.githubusercontent.com/Azure/BatchAI/master/schemas/2018-05-01/cntk.json",
    "properties": {
        "nodeCount": 1,
        "cntkSettings": {
            "pythonScriptFilePath": "$AZ_BATCHAI_INPUT_SCRIPT/ConvNet_MNIST.py",
            "commandLineArgs": "$AZ_BATCHAI_INPUT_DATASET $AZ_BATCHAI_OUTPUT_MODEL"
        },
        "jobPreparation": {
            "commandLine": "echo This is a job preparation task"
        },
        "environmentVariables": [
            {
                "name": "ENVIRONMENT_VARIABLE_1", "value": "Value1"
            },
            {
                "name": "ENVIRONMENT_VARIABLE_2", "value": "Value2"
            }
        ],
        "secrets": [
            {
                "name": "ENVIRONMENT_VARIABLE_3", "value": "Value 3"
            },
            {
                "name": "ENVIRONMENT_VARIABLE_4",
                "valueSecretReference": {
                    "sourceVault": {
                        "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/demoGroup/providers/Microsoft.KeyVault/vaults/demokeyvault"
                    },
                    "secretUrl": "https://demokeyvault.vault.azure.net/secrets/nameofsecter"
                }
            }
        ],
        "stdOutErrPathPrefix": "$AZ_BATCHAI_MOUNT_ROOT/external",
        "inputDirectories": [{
            "id": "DATASET",
            "path": "$AZ_BATCHAI_MOUNT_ROOT/external/mnist_database"
        }, {
            "id": "SCRIPT",
            "path": "$AZ_BATCHAI_MOUNT_ROOT/external/cntk_samples"
        }],
        "outputDirectories": [{
            "id": "MODEL",
            "pathPrefix": "$AZ_BATCHAI_MOUNT_ROOT/external",
            "pathSuffix": "Models"
        }],
        "containerSettings": {
            "shmSize": "16gb",
            "imageSourceRegistry": {
                "image": "microsoft/cntk:2.1-gpu-python3.5-cuda8.0-cudnn6.0"
            }
        }
    }
}
```

### Number of Nodes to Run the Job

You need to specify number of nodes required to run your job using `nodeCount` attribute. Batch AI will take care of
setting up required environment to run a distributed job if this value greater than 1.

The job will start execution when required number of compute nodes become available in the cluster.

### Framework Specific Settings

Batch AI supports multiple frameworks (CNTK, Caffe, Caffe2, TensorFlow, etc). The best way to get familiar with framework
specific arguments required for running single GPU and distributed training jobs is to explore recipes available on
[Azure/BatchAI github](https://github.com/Azure/BatchAI/tree/master/recipes). You can use job's configuration described 
in those recipes as a starting point for your job configuration.

For example, the job configuration file given above describes a job which uses CNTK framework with `ConvNet_MNIST.py` 
python script and requires two command line arguments.

### Job Preparation Task

You can configure special preparation steps which needs to be run before job execution using job preparation task. This
functionality can be used to downloading and prepare training data as done in
[this recipe](https://github.com/Azure/BatchAI/blob/master/recipes/CNTK/CNTK-GPU-Python-Distributed/job.json) or to
install additional dependencies like in 
[this recipe](https://github.com/Azure/BatchAI/blob/master/recipes/Horovod/Horovod/job.json).

Job preparation task is executed directly on the node or in the same container as the job depending on presence of
`containerSettings` configuration section. 

For example, the configuration file given above specifies that `echo This is a job preparation task` should be executed
in each container before starting CNTK job.

Note, if job preparation task fails, the job will fail as well.

### User Defined Environment Variables

You can define environment variable which will be setup by Batch AI for your job using `environmentVariables` array as
in example above. The environment variable will be available both for the job and for the job preparation task.

### User Defined Environment Variables With Secret Values

You can define environment variable with secret values which will be setup by Batch AI for your job using `secrets` array
as in example above. The environment variable will be available both for the job and for the job preparation task.

The differences between environmentVariables and secrets are:

1. Server never returns values of secrets;
2. You can specify values for secrets using Azure KeyVault (see [Using KeyVault for Storing Secrets](#using-keyvault-for-storing-secrets)
for details).
 
### Standard and Error Output

Batch AI will store job and job preparation task standard output (stdout and stderr) and execution log in a folder 
`{stdOutErrPathPrefix}/{subscription id}/{resource group}/workspaces/{workspace name}/experiments/{experiment name}/jobs/{job name}/{job uuid}/`, where `job uuid` is an unique ID
of a job, it's used to distinguish output of the job from output of deleted jobs which had the same job name. You can
obtain the information about the auto generated part of the path using the following command:

```bash
$ az batchai job show -g demoGroup -w demoWorkspace -e demoExperiment -n demoJob --query jobOutputDirectoryPathSegment
```  

It's recommended to make stdOutErrPathPrefix to be located on Azure File Share mount point if you want to monitor job
output during job execution via Azure Portal, Storage Explorer, Jupyter notebook or CLI.

You can configure `stdOutErrPathPrefix` to be located on Azure Container as well, but client side caching of blob fuse
makes job's output/error available only when job is completed.

You can configure `stdOutErrPathPrefix` to be equal to `$AZ_BATCHAI_JOB_TEMP_DIR` (a temporary folder created on node's
ssd drive) if you don't want to store job's output in external storage. Batch AI doesn't provide API to access this
folder, so you will to ssh to the compute node to access job's standard and error outputs. Note, the content of
`$AZ_BATCHAI_JOB_TEMP_DIR` is deleted when a new job is going to be executed by a node.


### Input Directories

Input directories is a way to setup aliases for directories containing training data. For example, 
the job configuration file given above defines two input directories: `DATASET` with path 
`$AZ_BATCHAI_MOUNT_ROOT/external/mnist_database` and `SCRIPT` with path `$AZ_BATCHAI_MOUNT_ROOT/external/cntk_samples`.
The job can access those directories using environment variables `$AZ_BATCHAI_INPUT_DATASET` and 
`$AZ_BATCHAI_INPUT_SCRIPT`.

Defining input directories allows you to create training job scripts which depend on aliases instead of paths, so you
can change data location without changing the script.

Another benefit of using input directories is an additional functionality provided by various tools to work with them (
e.g. AI plugin for Visual Studio and Azure Portal provide a simple access to content of the input directories).
 
### Output Directories

Output directories is a way to specify where job should store its output. Output directory is configured by specifying an
unique (in job's scope) directory ID, path prefix and suffix. For each output directory Batch AI will create a folder
with a path `{prefix}/{subscription id}/{resource group}/workspaces/{workspace name}/experiments/{experiment name}/jobs/{job name}/{job uuid}/` and will setup an 
environment variable `$AZ_BATCHIA_OUTPUT_{directory ID}`. Here `job uuid` is an unique ID of a job, it's used to avoid
conflicts  between job's output and output of a deleted jobs which had the same job name. You can obtain the information
about the auto generated part of the path using the following command:

```bash
$ az batchai job show -g demoGroup -w demoWorkspace -e demoExperiment -n demoJob --query jobOutputDirectoryPathSegment
```  

Azure CLI 2.0, Azure Portal and AI plugin for Visual Studio provide access to output files stored in configured output 
directories.

### Docker Container

Batch AI can run training jobs in docker containers or directly on the compute nodes. To run the the job in a docker
container you need to provide `containerSettings` in your jobs configuration file. For example, the configuration file
given above tells Batch AI to run CNTK job in a container with `microsoft/cntk:2.1-gpu-python3.5-cuda8.0-cudnn6.0`
docker image.

Batch AI allows to use custom image repository by providing `serverUrl` attribute. You can use private images by
providing user name and password or KeyVaultSecret reference as well.

Here is a full featured example of specifying `containerSetting` using private image from a custom registry:

```json
{
    "properties": {
        "comment": "other settings",
        "containerSettings": {
            "imageSourceRegistry": {
                "serverUrl": "demo.azurecr.io",
                "image": "demo.azurecr.io/myimage",
                "credentials": {
                    "username": "demo",
                    "password": "demoPassword"
                }
            }
        }
    }
}
```

Note, you need to use fully-qualified image name if you are using custom image repository.

Instead of providing the password in the config file, you can use KeyVault to share it with Batch AI (see [Using KeyVault for Storing Secrets](#using-keyvault-for-storing-secrets) section for more information):

```json
{
    "properties": {
        ...
        "containerSettings": {
            "imageSourceRegistry": {
                "serverUrl": "demo.azurecr.io",
                "image": "demo.azurecr.io/myimage",
                "credentials": {
                    "username": "demo",
                    "passwordSecretReference": {
                        "sourceVault": {
                            "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/batchaisecrets/providers/Microsoft.KeyVault/vaults/demokeyvault"
                        },
                        "secretUrl": "https://demokeyvault.vault.azure.net/secrets/nameofsecter"
                    }
                }
            }
        }
    }
}
```
 
## Monitoring Jobs

You can list all jobs under particular experiment using the following command:

```bash
$ az batchai job list -o table -g demoGroup -w demoWorkspace -e demoExperiment
```

Example output:
```
Name    Cluster      Cluster RG  Cluster Workspace  Tool      Nodes  State        Exit code
------  -----------  ----------  -----------------  ------  -------  ---------  -----------
job1    demo         demo         demoWorkspace      custom        1  succeeded            0
job2    demoCluster  defaultrg    default            cntk          1  failed             127
job3    nc6          tests        default            caffe         1  queued               

```

, where:
- `Name` is the job name;
- `Cluster`, `Cluster RG` and `Cluster Workspace` are name, resource group and workspace of the cluster to which this
job is assigned;
- `Tool` is the name of the toolkit used in the job;
- Nodes is the number of nodes configured for the job execution;
- State is the current state of the job: queued, failed, terminating, succeeded or failed;
- Exit code is the job's exit code if available (if the job is succeeded or failed).

To get full information about a job use `az batchai job show` command. For example:

```bash
$ az batchai job show -g demoGroup -w demoWorkspace -e demoExperiment -n demoJob
```

example output:
```
{
  "caffe2Settings": null,
  "caffeSettings": null,
  "chainerSettings": {
    "commandLineArgs": "-g -o $AZ_BATCHAI_OUTPUT_MODEL",
    "processCount": 2,
    "pythonInterpreterPath": null,
    "pythonScriptFilePath": "$AZ_BATCHAI_JOB_MOUNT_ROOT/scripts/chainer/train_mnist.py"
  },
  "cluster": {
    "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/demoGroup/providers/Microsoft.BatchAI/workspaces/demoWorkspace/clusters/demoCluster",
    "resourceGroup": "demoGroup"
  },
  "cntkSettings": null,
  "constraints": {
    "maxWallClockTime": "7 days, 0:00:00"
  },
  "containerSettings": {
    "imageSourceRegistry": {
      "credentials": null,
      "image": "batchaitraining/chainermn:openMPI",
      "serverUrl": null
    },
    "shmSize": null
  },
  "creationTime": "2018-06-13T00:35:47.573000+00:00",
  "customMpiSettings": null,
  "customToolkitSettings": null,
  "environmentVariables": null,
  "executionInfo": {
    "endTime": "2018-06-13T00:38:15.967000+00:00",
    "errors": [
      {
        "code": "JobFailed",
        "details": null,
        "message": "Job failed with non-zero exit code"
      }
    ],
    "exitCode": 2,
    "startTime": "2018-06-13T00:35:50.457000+00:00"
  },
  "executionState": "failed",
  "executionStateTransitionTime": "2018-06-13T00:38:15.967000+00:00",
  "horovodSettings": null,
  "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/demoGroup/providers/Microsoft.BatchAI/workspaces/demoWorkspace/experiments/demoExperiment/jobs/demoJob",
  "inputDirectories": null,
  "jobOutputDirectoryPathSegment": "00000000-0000-0000-0000-000000000000/demoGroup/workspaces/demoWorkspace/experiments/demoExperiment/jobs/demoJob/23648195-5849-4723-ba34-39acf7becf6e",
  "jobPreparation": null,
  "mountVolumes": {
    "azureBlobFileSystems": null,
    "azureFileShares": [
      {
        "accountName": "batchairecipestorage",
        "azureFileUrl": "https://batchairecipestorage.file.core.windows.net/logs",
        "credentials": {
          "accountKey": null,
          "accountKeySecretReference": null
        },
        "directoryMode": "0777",
        "fileMode": "0777",
        "relativeMountPath": "logs"
      },
      {
        "accountName": "batchairecipestorage",
        "azureFileUrl": "https://batchairecipestorage.file.core.windows.net/scripts",
        "credentials": {
          "accountKey": null,
          "accountKeySecretReference": null
        },
        "directoryMode": "0777",
        "fileMode": "0777",
        "relativeMountPath": "scripts"
      }
    ],
    "fileServers": null,
    "unmanagedFileSystems": null
  },
  "name": "demoJob",
  "nodeCount": 2,
  "outputDirectories": null,
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2018-06-13T00:35:48.280000+00:00",
  "pyTorchSettings": null,
  "resourceGroup": "batchai.recipes",
  "schedulingPriority": "normal",
  "secrets": null,
  "stdOutErrPathPrefix": "$AZ_BATCHAI_JOB_MOUNT_ROOT/logs",
  "tensorFlowSettings": null,
  "toolType": "chainer",
  "type": "Microsoft.BatchAI/workspaces/experiments/jobs"
}
```

In this output you can find information about the job (toolkit, container, input/output directories, container, etc),
failure reason, execution time and other information.

## Access Files in Output Directories

You can enumerate files in job's output directories by using `az batchai job file list` command: 

```text
Command
    az batchai job file list: List job's output files in a directory with given id.
        List job's output files in a directory with given id if the output directory is located on
        mounted Azure File Share or Blob Container.

Arguments
    --experiment -e     [Required]: Name of experiment.
    --job -j            [Required]: Name of job.
    --resource-group -g [Required]: Name of resource group. You can configure the default group
                                    using `az configure --defaults group=<name>`.
    --workspace -w      [Required]: Name of workspace.
    --expiry                      : Time in minutes for how long generated download URL should
                                    remain valid.  Default: 60.
    --output-directory-id -d      : The Id of the job's output directory (as specified by "id"
                                    element in outputDirectories collection in the job create
                                    parameters).  Default: stdouterr.
    --path -p                     : Relative path in the given output directory.  Default: ..

Global Arguments
    --debug                       : Increase logging verbosity to show all debug logs.
    --help -h                     : Show this help message and exit.
    --output -o                   : Output format.  Allowed values: json, jsonc, table, tsv.
                                    Default: json.
    --query                       : JMESPath query string. See http://jmespath.org/ for more
                                    information and examples.
    --subscription                : Name or ID of subscription. You can configure the default
                                    subscription using `az account set -s NAME_OR_ID`".
    --verbose                     : Increase logging verbosity. Use --debug for full debug logs.

Examples
    List files in the standard output directory of the job.
        az batchai job file list -g MyResourceGroup -w MyWorkspace -e MyExperiment -j MyJob


    List files in the standard output directory of the job. Generates output in a table format.
        az batchai job file list -g MyResourceGroup -w MyWorkspace -e MyExperiment -j MyJob -o table


    List files in a folder 'MyFolder/MySubfolder' of an output directory with id 'MODELS'.
        az batchai job file list -g MyResourceGroup -w MyWorkspace -e MyExperiment -j MyJob \
            -d MODELS -p MyFolder/MySubfolder


    List files in the standard output directory of the job making download URLs to remain valid for
    15 minutes.
        az batchai job file list -g MyResourceGroup -w MyWorkspace -e MyExperiment -j MyJob \
            --expiry 15
```

## Stream Files from Output Directories

You can stream (similar to GNU/Linux `tail -f` command) the job's output using `az batchai job file stream` command:

```text
Command
    az batchai job file list: List job's output files in a directory with given id.
        List job's output files in a directory with given id if the output directory is located on
        mounted Azure File Share or Blob Container.

Arguments
    --experiment -e     [Required]: Name of experiment.
    --job -j            [Required]: Name of job.
    --resource-group -g [Required]: Name of resource group. You can configure the default group
                                    using `az configure --defaults group=<name>`.
    --workspace -w      [Required]: Name of workspace.
    --expiry                      : Time in minutes for how long generated download URL should
                                    remain valid.  Default: 60.
    --output-directory-id -d      : The Id of the job's output directory (as specified by "id"
                                    element in outputDirectories collection in the job create
                                    parameters).  Default: stdouterr.
    --path -p                     : Relative path in the given output directory.  Default: ..

Global Arguments
    --debug                       : Increase logging verbosity to show all debug logs.
    --help -h                     : Show this help message and exit.
    --output -o                   : Output format.  Allowed values: json, jsonc, table, tsv.
                                    Default: json.
    --query                       : JMESPath query string. See http://jmespath.org/ for more
                                    information and examples.
    --subscription                : Name or ID of subscription. You can configure the default
                                    subscription using `az account set -s NAME_OR_ID`".
    --verbose                     : Increase logging verbosity. Use --debug for full debug logs.

Examples
    List files in the standard output directory of the job.
        az batchai job file list -g MyResourceGroup -w MyWorkspace -e MyExperiment -j MyJob


    List files in the standard output directory of the job. Generates output in a table format.
        az batchai job file list -g MyResourceGroup -w MyWorkspace -e MyExperiment -j MyJob -o table


    List files in a folder 'MyFolder/MySubfolder' of an output directory with id 'MODELS'.
        az batchai job file list -g MyResourceGroup -w MyWorkspace -e MyExperiment -j MyJob \
            -d MODELS -p MyFolder/MySubfolder


    List files in the standard output directory of the job making download URLs to remain valid for
    15 minutes.
        az batchai job file list -g MyResourceGroup -w MyWorkspace -e MyExperiment -j MyJob \
            --expiry 15


(env) alex@alexu:~/slurm$ az batchai job file stream -h

Command
    az batchai job file stream: Stream the content of a file (similar to 'tail -f').
        Waits for the job to create the given file and starts streaming it similar to 'tail -f'
        command. The command completes when the job finished execution.

Arguments
    --experiment -e     [Required]: Name of experiment.
    --file-name -f      [Required]: The name of the file to stream.
    --job -j            [Required]: Name of job.
    --resource-group -g [Required]: Name of resource group. You can configure the default group
                                    using `az configure --defaults group=<name>`.
    --workspace -w      [Required]: Name of workspace.
    --output-directory-id -d      : The Id of the job's output directory (as specified by "id"
                                    element in outputDirectories collection in the job create
                                    parameters).  Default: stdouterr.
    --path -p                     : Relative path in the given output directory.  Default: ..

Global Arguments
    --debug                       : Increase logging verbosity to show all debug logs.
    --help -h                     : Show this help message and exit.
    --output -o                   : Output format.  Allowed values: json, jsonc, table, tsv.
                                    Default: json.
    --query                       : JMESPath query string. See http://jmespath.org/ for more
                                    information and examples.
    --subscription                : Name or ID of subscription. You can configure the default
                                    subscription using `az account set -s NAME_OR_ID`".
    --verbose                     : Increase logging verbosity. Use --debug for full debug logs.

Examples
    Stream standard output file of the job.
        az batchai job file stream -g MyResourceGroup -w MyWorkspace -e MyExperiment -j MyJob \
            -f stdout.txt


    Stream a file 'log.txt' from a folder 'logs' of an output directory with id 'OUTPUTS'.
        az batchai job file stream -g MyResourceGroup -w MyWorkspace -e MyExperiment -j MyJob \
            -d OUTPUTS -p logs -f log.txt 
```

This command periodically checks requested file and prints its updates on the screen. The command will return when the 
job has finished execution, you cat press `Ctrl-C` to interrupt the output at any moment.

Note, `az` does not know which files your job will generate, so it accepts any file name and waits for this file to 
become available.

Note, if Azure Container is configured as an output directory, the file will become available for streaming only when job
closes the file.

## Working with Job Nodes

Batch AI provides `az batchai job node` group of commands similar to `az batchai cluster node` described above.

## Jobs Termination and Deletion

You can terminate and delete jobs using `az batchai job terminate` and `az batchai job delete` commands. Both commands
require you to confirm the action, so if you are going to use this commands from non-interactive scripts, please provide
`-y` parameter. Job deletion may take a long time, specify `--no-wait` to skip waiting if you need to submit multiple
requests simultaneously.

For example,

```bash
$ az batchai job delete -g demoGroup -w demoWorkspace -e demoExperiment -n demoJob -y --no-wait
``` 

will submit `demoJob` deletion request without confirmation and return execution immediately without waiting for the
job to be actually deleted.

# Single node NFS

## Creation

Batch AI provide you with a simple way to create single node NFS using `az batchai file-server create` command:

```bash
$ az batchai file-server create -h
```

Output:

```
Command
    az batchai file-server create: Create a file server.

Arguments
    --name -n           [Required]: Name of file server.
    --resource-group -g [Required]: Name of resource group. You can configure a default value by
                                    setting up default workspace using `az batchai workspace set-
                                    default`.
    --no-wait                     : Do not wait for the long-running operation to finish.
    --vm-size -s                  : VM size.
    --workspace -w                : Name or ARM ID of the workspace. You can configure default
                                    workspace using `az batchai workspace set-default`.  Default:
                                    pgunda.

Admin Account Arguments
    --generate-ssh-keys           : Generate SSH public and private key files in ~/.ssh directory
                                    (if missing).
    --password -p                 : Optional password for the admin user created on the NFS node.
    --ssh-key -k                  : Optional SSH public key value or path. If ommited and no
                                    password specified, default SSH key (~/.ssh/id_rsa.pub) will be
                                    used.
    --user-name -u                : Name of admin user account to be created on NFS node. If the
                                    value is not provided and no user configuration is provided in
                                    the config file, current user's name will be used.

Advanced Arguments
    --config-file -f              : A path to a json file containing file server create parameters
                                    (json representation of
                                    azure.mgmt.batchai.models.FileServerCreateParameters). Note,
                                    parameters given via command line will overwrite parameters
                                    specified in the configuration file.

Storage Disks Arguments
    --caching-type                : Caching type for premium disks. If not provided via command line
                                    or in configuration file, no caching will be used.  Allowed
                                    values: none, readonly, readwrite.
    --disk-count                  : Number of disks.
    --disk-size                   : Disk size in Gb.
    --storage-sku                 : The sku of storage account to persist VM.  Allowed values:
                                    Premium_LRS, Standard_LRS.

Virtual Network Arguments
    --subnet                      : ARM ID of a virtual network subnet to put the file server in. If
                                    not provided via command line or in the configuration file,
                                    Batch AI will create a new virtual network and subnet under your
                                    subscription.

Global Arguments
    --debug                       : Increase logging verbosity to show all debug logs.
    --help -h                     : Show this help message and exit.
    --output -o                   : Output format.  Allowed values: json, jsonc, table, tsv.
                                    Default: json.
    --query                       : JMESPath query string. See http://jmespath.org/ for more
                                    information and examples.
    --subscription                : Name or ID of subscription. You can configure the default
                                    subscription using `az account set -s NAME_OR_ID`".
    --verbose                     : Increase logging verbosity. Use --debug for full debug logs.

Examples
    Create a NFS file server using a configuration file.
        az batchai file-server create -g MyResourceGroup -w MyWorkspace -n MyNFS -c nfs.json

    Create a NFS manually providing parameters.
        az file-server create -g MyResourceGroup -w MyWorkspace -n MyNFS \
            -s Standard_D14 --disk-count 4 --disk-size 512 \
            --storage-sku Premium_LRS --caching-type readonly \
            -u $USER -k ~/.ssh/id_rsa.pub
```

Batch AI will automatically create and administrator user account on NFS node using either provided credentials or
using your current user name and default SSH public key.

You can specify the name for the account using `-u` option. If this option is not provided, Azure CLI will use your
current user name.

The admin user account requires you to provide a password and/or SSH public key which you will be able to use to SSH to
the node. If none has been provided, the Azure CLI will use your default SSH public key from ~/.ssh/id_rsa.pub. If you
have no default SSH key pair, you can generate one providing `--generate-ssh-keys` option.

You can specify admin account password using `-p` option.

You can specify a value or a path to SSH public key using `-k` option.

## VM size and Storage Disks

You need to select VM size and storage disks based on required performance. This [article](https://docs.microsoft.com/en-us/azure/virtual-machines/windows/premium-storage)
can be a good starting point for choosing good parameters for file server.

## Subnet

Each Batch AI File Server belongs to a particular virtual network subnet. To be able to mount a File Server to a cluster
during cluster creation or during job submission, both cluster and file server must be in the same virtual network. So,
if you are planning to mount multiple File Servers to a single cluster you need to put them into the same virtual network
using `--subnet` option. In addition, if you are going to mount file server during jobs submission, you should create
cluster in the same vnet.


## Monitoring

Similar to clusters, you can list NFSes and get information about particular NFS using `az batchai file-server list` and
`az batchai file-server show` commands.

For example, 

```bash
az batchai file-server list -o table -g demoGroup -w demoWorkspace
```

example output:

```
Name      Resource Group    Size         Disks      Public IP     Internal IP    Type    Mount Point
--------  ----------------  -----------  ---------  ------------  -------------  ------  -------------
demoNfs   demoGroup         STANDARD_D2  1 x 10 Gb  40.76.81.214  10.0.0.4       nfs     /mnt/data
```

## SSH to NFS node

To ssh to NFS node use the public IP returned by `az batchai file-server list` or `az batchai file-server show` command
and standard ssh port 22 (you don't need to provide it in ssh command).
 
## Deletion

Use `az batchai file-server delete` command to delete NFS.

# Using KeyVault for Storing Secrets

There are currently two types of secrets you may need to provide to Batch AI service - storage account keys and docker
images private repositories credentials. You can either provide this information via configuration files or use KeyVault
to share secrets with Batch AI.

This section describes how to create KeyVault and share secrets with Batch AI.

1. Create a resource group for new KeyVault (it's recommended to have a dedicated resource group for it). For example:
```bash
$ az group create -l eastus -n batchaisecrets
```

2. Create a key vault with a globally unique name in new resource group:
 
```bash
$ az keyvault create -l eastus -g batchaisecrets -n <keyvault name>
```

, where <keyvault name> is an unique name (GNU/Linux users can use `pwgen` utility to generate an unique name
 for KeyVault - ```pwgen 24 1```).
 
Example output:
```json
{
  "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/batchaisecrets/providers/Microsoft.KeyVault/vaults/demokeyvault",
  "location": "eastus",
  "name": "demokeyvault",
  "vaultUri": "https://demokeyvault.vault.azure.net/",
  "comment": "other parameters",  
  "resourceGroup": "batchaisecrets",
  "tags": {},
  "type": "Microsoft.KeyVault/vaults"
}
```

3. Give Batch AI Reader role for KeyVault resource:

```bash
az role assignment create --scope /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/batchaisecrets/providers/Microsoft.KeyVault/vaults/demokeyvault --role Reader --assignee 9fcb3732-5f52-4135-8c08-9d4bbaf203ea -g ""
```
, here `9fcb3732-5f52-4135-8c08-9d4bbaf203ea` is a service principal of Microsoft BatchAI.

4. Give Batch AI 'get' permission on this KeyVault:
```bash
$ az keyvault set-policy --spn 9fcb3732-5f52-4135-8c08-9d4bbaf203ea -n <keyvault name> -g batchaisecrets --secret-permissions get list
```
, here `9fcb3732-5f52-4135-8c08-9d4bbaf203ea` is a service principal of Microsoft BatchAI.

5. Add new secret containing the private repo password:
```bash
az keyvault secret set --vault-name <keyvault name> --name nameofsecret --value secretvalue
```
, here `nameofsecret` is a name of the secret (e.g. demoStorageKey) and `secretvalue` is the secret itself (e.g. a value
of the storage key).

Example output:

```json
{
  "attributes": {
    "created": "2017-11-28T23:14:56+00:00",
    "enabled": true,
    "expires": null,
    "notBefore": null,
    "recoveryLevel": "Purgeable",
    "updated": "2017-11-28T23:14:56+00:00"
  },
  "contentType": null,
  "id": "https://demokeyvault.vault.azure.net/secrets/nameofsecter/769fef65a64f476d9b3924a96fe73c57",
  "kid": null,
  "managed": null,
  "tags": {
    "file-encoding": "utf-8"
  },
  "value": "secretvalue"
}
```

Now, for example, instead of providing a storage key in Cluster Configuration File, you can provide 
`accountKeySecretReference` like this:

```json
{
    "comment": "other parameters",
    "azureFileShares": [
        {
            "accountName": "demoStorage",
            "azureFileUrl": "https://demoStorage.file.core.windows.net/demoShare",
            "credentials": {
                "accountKeySecretReference": {
                    "sourceVault": {
                        "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/batchaisecrets/providers/Microsoft.KeyVault/vaults/demokeyvault"
                    },
                    "secretUrl": "https://demokeyvault.vault.azure.net/secrets/nameofsecter"
                }
            },
            "relativeMountPath": "afs"
        }
    ]
}
```
