# Introduction

Azure CLI 2.0 has a command line module for managing Batch AI clusters, single node NFS and jobs.

This document covers Azure CLI 2.0 setup and usage.

# Setup

- The easiest way to start using Azure CLI 2.0 is to launch it from Shell Console in Azure Portal as described in
[Quickstart for Bash in Azure Cloud Shell tutorial](https://docs.microsoft.com/en-us/azure/cloud-shell/quickstart).

- Azure Data Science VM has Azure CLI 2.0 pre-installed but you may need to update it using [these instructions]
(https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest) to get access to the latest
features.

- If you prefer to setup Azure CLI 2.0 on your computer, please follow [these instructions]
(https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest).

- You can get access to the latest not published version of Azure CLI 2.0 by following [these instructions]
(https://github.com/Azure/azure-cli#edge-builds).

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
azure-cli (2.0.21)

acr (2.0.15)
acs (2.0.19)
appservice (0.1.20)
backup (1.0.3)
batch (3.1.7)
batchai (0.1.3)
...
```

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

# Clusters Management
Azure CLI 2.0 allows you to create, resize, delete and get information about clusters.

## Creation
Please get familiar with `az batchai cluster create` command:

```bash
$ az batchai cluster create -h

```

### Simple Use-Cases

In most cases, it's possible to create a new cluster using command line arguments without configuration file.

To create a cluster, you need to provide a cluster name, location, resource group name, VM size, cluster scaling
parameters, image to be used for cluster nodes and administrator account to be created on each cluster node. Optionally,
you can configure cluster to mount Azure File Share, Azure Storage Container and single node NFS on each compute node.

The following commands will create a new resource group `demoGroup` and single node GPU cluster `demoCluster` with
Ubuntu LTS image in EastUS region. Batch AI will create `demoUser` admin account on each node with `DemoPassword`:

```bash
$ az group create -l eastus -n demoGroup
$ az batchai cluster create -l eastus -g demoGroup -n demoCluster -s Standard_NC6 -i UbuntuLTS --min 1 --max 1 -u demoUser -p demoPassword
```

Note, you can avoid typing location and group name during clusters and jobs creation by setting up their default values
for Azure CLI 2.0:
```bash
$ az configure -d location=eastus
$ az configure -d group=demoGroup
```

#### Admin User Account
BatchAI creates an admin user account on each compute node allowing you to perform SSH access to the nodes. You need to
specify account name (using `-u` option), password and/or ssh public key for this account using `-p` and `-k` options.

Note, you cannot use `admin` as an account name because Batch AI nodes already has a group with that name.

It's highly recommended to use ssh public key option instead of password. GNU/Linux users can generate a private and
public ssh keys using `ssh-keygen` command line utility, Windows users can generate keys using different 3rd party
solutions (e.g. PuTTYgen included into a popular PuTTY client, cygwin, etc). `-k` value may contain either public key
value directly or a path to the file containing public ssh key.

GNU/Linux users can provide admin user name and key as `-u $USER -k ~/.ssh/id_rsa.pub` to allow password-less SSH to GPU
nodes. 

#### Manual Scale Cluster
If --min and --max arguments have the same value, `az` will create a cluster in manual scale mode - requested number of
nodes will be allocated immediately after cluster creation and will remain until the cluster is manually resized or 
deleted.

#### Auto-Scale Cluster
You can specify different values for --min and --max arguments. In this case, `Batch AI` will scale up/down cluster
automatically depending on number of queued and running jobs. This option allows you to save money by releasing unused
compute resources.

For example,

```bash
$ az batchai cluster create -l eastus -g demoGroup -n demoCluster -s Standard_NC6 -i UbuntuLTS --min 0 --max 1 -u demoUser -p demoPassword
```

will create a cluster with 0 nodes. The cluster will be scaled up when you submit a job and will scale down to 0 when
there are no jobs to execute.

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
$ az batchai cluster create -l eastus -g demoGroup -n demoCluster --storage-account-name demobatchaicli --afs-name demoafs --afs-mount-path azurefileshare --container-name democontainer --container-mount-path azurecontainer -s Standard_NC6 -i UbuntuLTS --min 1 --max 1 -u demoUser -p demoPassword 
```

Note, storage account name must have an unique value, otherwise storage account creation command will fail with 
`The storage account named demobatchaicli is already taken.` error message.

$AZ_BATCHAI_MOUNT_ROOT is an environment variable set by Batch AI for each job, it's value depends on the image
used for nodes creation. For example, on Ubuntu based images it's equal to `/mnt/batch/tasks/shared/LS_root/mounts`.

If you want to use Azure File Share or Azure Container belonging to a storage account created in a different subscription,
provide `--storage-account-key` argument containing a key for that storage account.

You can provide only one Azure File Share and/or Azure Container via command line arguments. Please use Cluster
Configuration File if you need to mount more file systems.

Note, Azure Container specified with `--container-name` argument will be mounted with the following mount options:
```bash
--use-https=true -o big_writes -o max_read=131072 -o max_write=131072 -o attr_timeout=240 -o fsname=blobfuse -o kernel_cache -o entry_timeout=240 -o negative_timeout=120 -o allow_other
```

You need to use Cluster Configuration File (described below) to use different mount options.

#### Mounting NFS
Azure File Shares and Azure Containers provide a convenient and cheap way to store data used or generated by training
jobs. Another storage option supported by Batch AI is a single node NFS. This solution is more expensive but can give
a better performance in some situations (depending on data access patterns).

To use this option you need to create a single node NFS using `az batchai file-server create` command as described in
*Single Node NFS* section below and provide it's name via `--nfs` command line argument during cluster creation.

For example, the following code will create a single node NFS `demoNFS` with 2 disks (10Gb each) and a single node GPU 
cluster `demoCluster` with NFS mounted at `$AZ_BATCHAI_MOUNT_ROOT/nfs`:

```bash
$ az batchai file-server create -l eastus -g demoGroup -n demoNFS --disk-count 2 --disk-size 10 -s Standard_D1 -u demoUser -p demoPassword
$ az batchai cluster create -l eastus -g demoGroup -n demoCluster --nfs demoNFS --nfs-mount-path nfs -s Standard_NC6 -i UbuntuLTS --min 1 --max 1 -u demoUser -p demoPassword
```

You can use different resource group name for the NFS and cluster, in this case you need to provide NFS's resource group
via `--nfs-resource-group` command line argument. For example,

```bash
$ az batchai file-server create -l eastus -g demoNFSGroup -n demoNFS --disk-count 2 --disk-size 10 -s Standard_D1 -u demoUser -p demoPassword
$ az batchai cluster create -l eastus -g demoGroup -n demoCluster --nfs demoNFS --nfs-resource-group demoNFSGroup --nfs-mount-path nfs -s Standard_NC6 -i UbuntuLTS --min 1 --max 1 -u demoUser -p demoPassword
```

### Using Cluster Configuration File
There are several scenarios (described below) which require you to use Cluster Configuration File for cluster creation.

Cluster Configuration File is a json file containing ClusterCreateParameters object as defined by swagger specification
available at [Azure/azure-rest-api-specs github](https://github.com/Azure/azure-rest-api-specs/blob/current/specification/batchai/resource-manager/Microsoft.BatchAI/2017-09-01-preview/BatchAI.json#L1560).

To create a cluster using using Cluster Configuration File use `az batchai cluster create` command with `-c` option.
Note, the command line arguments provided on command line (e.g. VM size, image, scaling options and admin account) will
overwrite the corresponding options defined in the configuration file.

The following sessions describe how to use Cluster Configuration File for different scenarios.

#### Running Custom Steps During Cluster Creation  
It's possible to make customizations (e.g. install additional packages or download data used by multiple jobs) to each
cluster node by providing `setupTask`. `setupTask` is a command line which will be executed on a node immediately after
the node has been allocated or rebooted. To provide `setupTask` create a cluster.json file like this:

```json
{
    "properties": {
        "nodeSetup": {
            "setupTask": {
                "commandLine": "echo Hello",
                "runElevated": true,
                "stdOutErrPathPrefix": "$AZ_BATCHAI_MOUNT_ROOT/afs",
                "environmentVariables": [
                    {
                        "name": "ENVIRONMENT_VARIABLE_1", "value": "Value1"
                    },
                    {
                        "name": "ENVIRONMENT_VARIABLE_2", "value": "Value2"
                    }
                ]
            }
        }
    }
}        
```

This configuration file specifies that `echo Hello` command line needs to be run on each node under `root` account, its
standard and error output should be stored on file system mounted at `$AZ_BATCHAI_MOUNT_ROOT/afs` and specifies two
environment variables which should be setup before the command line execution.

You will be able to find standard and error output of setup task for each node in a folder 
`/{subscription id}/{resource group}/clusters/{cluster name}` in files `stdout-{node id}.txt` and `stderr-{node id}.txt`.

To create a luster with given startup task run:

```bash
$ az cluster create -l eastus -g demoGroup -n demoCluster -s Standard_NC6 --min 1 --max 1 --storage-account-name demobatchaicli --afs-name demoafs --afs-mount-path afs -u demoUser -p demoPassword -c cluster.json
```

#### Cluster with Low Priority VMs
To create a cluster with Low Priority VMs, create cluster.json file with the following content:

```json
{
  "vmPriority": "lowpriority"
}
```

and create the cluster using the following command:

```bash
az batchai cluster create -l eastus -g demoGroup -n demoCluster -s Standard_NC6 --min 0 --max 1 -u demoUser -p demoPassword -c cluster.json
```

#### Mounting Multiple Filesystems
If you need to use multiple Azure File Shares, Azure Containers or NFS, create a cluster.json file containing
`nodeSetup.mountVolumes` object like this:

```json
{
    "properties": {
        "nodeSetup": {
            "mountVolumes": {
                "azureFileShares": [
                    {
                        "accountName": "<AZURE_BATCHAI_STORAGE_ACCOUNT>",
                        "azureFileUrl": "https://<AZURE_BATCHAI_STORAGE_ACCOUNT>.file.core.windows.net/dataset1",
                        "credentialsInfo": {
                            "accountKey": "<AZURE_BATCHAI_STORAGE_KEY>"
                        },
                        "directoryMode": "0777",
                        "fileMode": "0777",
                        "relativeMountPath": "afs1"
                    },
                    {
                        "accountName": "<AZURE_BATCHAI_STORAGE_ACCOUNT>",
                        "azureFileUrl": "https://<AZURE_BATCHAI_STORAGE_ACCOUNT>.file.core.windows.net/dataset2",
                        "credentialsInfo": {
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
                            "id": "<NFS resource ID>"
                        },
                        "relativeMountPath": "nfs1",
                        "mountOptions": "rw"
                    },
                    {
                        "fileServer": {
                            "id": "<another NFS resource ID>"
                        },
                        "relativeMountPath": "nfs2",
                        "mountOptions": "rw"
                    }
                ]
            }
        }
    }
}
```
This configuration file specifies two Azure File Shares, two Azure Containers and two NFSes which should be mounted on
compute nodes.

You can provide values for `accountName` and `accountKey` directly in the file, or use `<AZURE_BATCHAI_STORAGE_ACCOUNT>`
and `<AZURE_BATCHAI_STORAGE_KEY>` placeholders which will be replaced by `az` with storage account information provided 
via `--storage-account-name` and (optionally) `--storage-account-key` command line arguments.

Note, if no mount options are provided for Azure Blob File System (Azure Containers), the following default options will
be used (same options are used if Azure Container is specified via `--container-name` argument):

```bash
--use-https=true -o big_writes -o max_read=131072 -o max_write=131072 -o attr_timeout=240 -o fsname=blobfuse -o kernel_cache -o entry_timeout=240 -o negative_timeout=120 -o allow_other
```

You can find more information about the recommended options at
[Azure/azure-storage-fuse](https://github.com/Azure/azure-storage-fuse) github page.

Note, if you are mounting several NFSes into a cluster, all of them must be in the same vnet subnet.

#### Mounting Unmanaged Filesystems
BatchAI allows you to mount your own NFS, cifs or GlusterFS clusters using configuration file. It's recommended to create
GPU and storage clusters in the same vnet subnet and use private IP addresses for mounting storage clusters.

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
You can get a list of all BatchAI clusters under your subscription using the following command:

```bash
$ az batchai cluster list -o table -g ''
```

Example output:
```
Name           Resource Group    VM Size       State      Idle    Running    Preparing    Leaving    Unusable
-------------  ----------------  ------------  -------  ------  ---------  -----------  ---------  ----------
dsvm           demo              STANDARD_D1   steady        1          0            0          0           0
democluster    demogroup         STANDARD_NC6  steady        0          0            1          0           0
```

, where:
- State - current state of the cluster: steady, resizing, deleting;
- Idle - number of idling nodes ready to execute jobs;
- Running - number of nodes currently executing jobs;
- Preparing - number of recently allocated nodes which perform preparation tasks (e.g drivers installation, mounting
file system, running startup task);
- Leaving - number of nodes which are leaving the cluster because of scale down or resizing command;
- Unusable - number of nodes in unusable state (e.g. nodes which failed preparation or startup tasks).

Note, `-g ''` option tells `az` to show cluster in all resource groups even if default resource group was configured
(via `az configure -d group=<group name>` command). Without this option, the command will show only clusters created in
the default resource group.

You can list cluster belonging to a particular resource group by giving its name in `-g` option:

```bash
$ az batchai cluster list -o table -g demogroup
```

Example output:
```
Name           Resource Group    VM Size       State      Idle    Running    Preparing    Leaving    Unusable
-------------  ----------------  ------------  -------  ------  ---------  -----------  ---------  ----------
democluster    demogroup         STANDARD_NC6   steady        0          0            1          0           0
```
 
Note, if you are sharing a subscription with other users you can put all your clusters and jobs in a dedicated
resource group and configure default resource group to show only yours resources:

```bash
$ az configure -d group=demogroup
$ az batchai cluster list -o table
```
will give:
```
Name           Resource Group    VM Size       State      Idle    Running    Preparing    Leaving    Unusable
-------------  ----------------  ------------  -------  ------  ---------  -----------  ---------  ----------
democluster    demogroup         STANDARD_NC6   steady        0          0            1          0           0
```

To get detailed information about a cluster use `az batchai cluster show` command. For example:

```bash
$ az batchai cluster show -n democluster -g demogroup
```
  
Sample output:
```
{
  "allocationState": "steady",
  "allocationStateTransitionTime": "2017-11-27T16:39:19.930000+00:00",
  "creationTime": "2017-11-27T16:38:02.216000+00:00",
  "currentNodeCount": 1,
  "errors": null,
  "id": "/subscriptions/1cba1da6-5a83-45e1-a88e-8b397eb84356/resourceGroups/demogroup/providers/Microsoft.BatchAI/clusters/democluster",
  "location": "eastus",
  "name": "democluster",
  "nodeSetup": {
    "mountVolumes": {
      "azureBlobFileSystems": [
        {
          "accountName": "demobatchaicli",
          "containerName": "democontainer",
          "credentials": {
            "accountKey": null,
            "accountKeySecretReference": null
          },
          "mountOptions": null,
          "relativeMountPath": "azurecontainer"
        }
      ],
      "azureFileShares": [
        {
          "accountName": "demobatchaicli",
          "azureFileUrl": "https://demobatchaicli.file.core.windows.net/demoafs",
          "credentials": {
            "accountKey": null,
            "accountKeySecretReference": null
          },
          "directoryMode": "0777",
          "fileMode": "0777",
          "relativeMountPath": "azurefileshare"
        }
      ],
      "fileServers": null,
      "unmanagedFileSystems": null
    },
    "setupTask": null
  },
  "nodeStateCounts": {
    "idleNodeCount": 0,
    "leavingNodeCount": 0,
    "preparingNodeCount": 1,
    "runningNodeCount": 0,
    "unusableNodeCount": 0
  },
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2017-11-27T16:38:02.934000+00:00",
  "resourceGroup": "demogroup",
  "scaleSettings": {
    "autoScale": null,
    "manual": {
      "nodeDeallocationOption": "requeue",
      "targetNodeCount": 1
    }
  },
  "subnet": null,
  "tags": null,
  "type": "Microsoft.BatchAI/Clusters",
  "userAccountSettings": {
    "adminUserName": "demoUser",
    "adminUserPassword": null,
    "adminUserSshPublicKey": null
  },
  "virtualMachineConfiguration": {
    "imageReference": {
      "offer": "UbuntuServer",
      "publisher": "Canonical",
      "sku": "16.04-LTS",
      "version": "latest"
    }
  },
  "vmPriority": "dedicated",
  "vmSize": "STANDARD_D1"
}
```

Note, you can omit `-g` option if default resource group is configured.

## SSH to Cluster Nodes
You can get information about the nodes belonging to the cluster using `az batchai cluster list-nodes` command:

```bash
$ az batchai cluster list-nodes -n democluster -g demoGroup -o table
```

Example output:
```
ID                                 IP               Port
---------------------------------  -------------  ------
tvm-1783593343_1-20171127t163917z  52.168.39.226   50000
```

, where:
- ID - node id (used as suffix in file names for standard and error output of setup tasks);
- IP - public IP of the node;
- Port - SSH port of the node.

GNU/Linux users can ssh to the node using the following command:

```bash
$ ssh 52.168.39.226 -p 50000
```

## Resizing Clusters
You can resize a cluster at any time using `az batchai cluster resize` command.
For example, the following command will resize `demoCluster` to have no nodes:

```bash
$ az batchai cluster resize -n democluster -g demoGroup -t 0
```

You can also switch a cluster into auto-scale mode using `az batchai cluster auto-scale`
command. For example, the following command will setup auto-scale mode for `demoCluster` and Batch AI
will scale the cluster automatically between 0 and 10 nodes depending on the number of running and pending jobs:

```bash
$ az batchai cluster auto-scale -n democluster -g demoGroup --min 0 --max 10
```

## Deleting Clusters
You can delete the cluster using `az batchai cluster delete` command, e.g.
```bash
$ az batchai cluster delete -n democluster -g demoGroup
```

Note, the command will ask you for confirmation and may take a significant time to complete. You can provide `-y` option
to skip the confirmation (e.g. this command is a part of non-interactive script). You can provide `--no-wait` option to
skip waiting for the deletion completion (useful if you need to delete multiple resources simultaneously).

# Jobs Management
Azure CLI 2.0 allows you to submit, terminate, delete and get information about BatchAI training jobs.

Please use take look at integrated help to get familiar with jobs related commands:

```bash
$ az batchai job --help
```

Output:

```
Group
    az batchai job: Commands to manage jobs.

Commands:
    create     : Create a job.
    delete     : Delete a job.
    list       : List jobs.
    list-files : List job's output files in a directory with given id.
    list-nodes : List remote login information for nodes on which the job was run.
    show       : Show information about a job.
    stream-file: Output the current content of the file and outputs appended data as the file grows
                 (similar to 'tail -f').
    terminate  : Terminate a job.
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
    --config -c   [Required]: A path to a json file containing job create parameters (json
                              representation of azure.mgmt.batchai.models.JobCreateParameters).
    --name -n     [Required]: Name of the job.
    --cluster-name -r       : If specified, the job will run on the given cluster instead of the one
                              configured in the json file.
    --cluster-resource-group: Specifies a resource group for the cluster given with --cluster-name
                              parameter. If omitted, --resource-group value will be used.
    --location -l           : Location. You can configure the default location using `az configure
                              --defaults location=<location>` or specify it in the job configuration
                              file.  Default: eastus.
    --no-wait               : Do not wait for the long running operation to finish.
    --resource-group -g     : Name of resource group. You can configure the default group using `az
                              configure --defaults group=<name>`.  Default: alex.

Global Arguments
    --debug                 : Increase logging verbosity to show all debug logs.
    --help -h               : Show this help message and exit.
    --output -o             : Output format.  Allowed values: json, jsonc, table, tsv.  Default:
                              json.
    --query                 : JMESPath query string. See http://jmespath.org/ for more information
                              and examples.
    --verbose               : Increase logging verbosity. Use --debug for full debug logs.
```

To create a job you need to specify location, resource group name (you can use the same resource group as you used for
the cluster), job name, cluster to run the job and provide a job configuration file.

For example,

```bash
$ az batchai job create -l eastus -n demoJob -g demoGroup -r demoCluster -c job.json 
```

will submit a new job `demoJob` to be run on `demoCluster` cluster in `demoGroup` resource group, the job configuration
will be read from job.json file.

You can use different resource groups for clusters and jobs, in this case you need to specify cluster's resource group
using `--cluster-resource-group` argument. For example, the following command will create a job in `demoGroup` resource
group to be run on `demoCluster` cluster created in `demoClusterGroup` resource group:

```bash
$ az batchai job create -l eastus -n demoJob -g demoGroup -r demoCluster --cluster-resource-group demoClusterGroup -c job.json 
```

Job submission is a long running operation which usually takes a dozen of seconds to complete. You can skip waiting by
providing `--no-wait` argument (can be useful if you need to submit multiple jobs at once). 

### Job Configuration File
Job configuration file is a json file containing `JobCreateParameters` object as defined by swagger spec available at
[Azure/azure-rest-api-specs github](https://github.com/Azure/azure-rest-api-specs/blob/current/specification/batchai/resource-manager/Microsoft.BatchAI/2017-09-01-preview/BatchAI.json#L1847).

Job configuration file defines framework specific parameters, number of nodes required for job execution, description of
input and output directories, docker container to run the job and job preparation steps. The following sections
describes all those parameters in details. Here is a job configuration file which we will use as reference:

```json
{
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
            }, {
                "name": "ENVIRONMENT_VARIABLE_2", "value": "Value2"
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

### Standard and Error Output 
Batch AI will store job and job preparation task standard output (stdout and stderr) in a folder 
`{stdOutErrPathPrefix}/{subscription id}/{resource group}/jobs/{job name}/{job uuid}/`, where `job uuid` is an unique ID
of a job, it's used to distinguish output of the job from output of deleted jobs which had the same job name.

It's recommended to make stdOutErrPathPrefix to be located on Azure File Share mount point if you want to monitor job
output during job execution via Azure Portal, Storage Explorer, Jupyter notebook or CLI.

You can configure `stdOutErrPathPrefix` to be located on Azure Container as well, but client side caching of blob fuse
makes job's output/error available only when job is completed.

You can configure `stdOutErrPathPrefix` to be equal to `$AZ_BATCHAI_JOB_TEMP_DIR` (a temporary folder created on node's
ssd drive) if you don't want to store job's output in external storage. Batch AI doesn't provide API to access this
folder, so you will to ssh to the compute node to access job's standard and error outputs. Note, the content of
`$AZ_BATCHAI_JOB_TEMP_DIR` is deleted when a new job is going to be executed by a node.

### Input Directories
Input directories is a way to setup an alias for a directories containing training data. For example, 
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
with a path `{prefix}/{subscription id}/{resource group}/jobs/{job name}/{job uuid}/outputs/{suffix}` and will setup an 
environment variable `$AZ_BATCHIA_OUTPUT_{directory ID}`. Here `job uuid` is an unique ID of a job, it's used to avoid
conflicts  between job's output and output of a deleted jobs which had the same job name.

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
        ...
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

## Monitoring Jobs
You can list all jobs under your subscription using the following command:

```bash
$ az batchai job list -o table -g ''
```

Example output:
```
Name    Resource Group    Cluster       Cluster RG    Tool      Nodes  State        Exit code
------  ----------------  ------------  ------------  ------  -------  ---------  -----------
job1    demo              demoCluster   demo          custom        1  succeeded            0
job2    demoGroup         demoCluster   demoGroup     cntk          1  failed             127
job3    demoGroup         demoCluster   demoGroup     caffe         1  queued               

```

, where:
- `Name` and `Resource Group` are job name and resource group in which this job was created;
- `Cluster` and `Cluster RG` are name and resource group of the cluster on which this job is created;
- `Tool` is the name of the toolkit used in the job;
- Nodes is the number of nodes configured for the job execution;
- State is the current state of the job: queued, failed, terminating, succeeded or failed;
- Exit code is the job's exit code if available (if the job is succeeded or failed).

Note, `-g ''` tells the `az` to show all jobs in the subscription ignoring configured default resource group.

To show jobs belonging to a particular resource group, provide its name in `-g` option, e.g. `-g demo` will list only
jobs belonging to `demo` resource group.

To get full information about a job use `az batchai job show` command. For example:

```bash
$ az batchai job show -n job2 -g demoGroup
```

Example output:
```
{
  "caffeSettings": null,
  "chainerSettings": null,
  "cluster": {                        
    "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/demoGroup/providers/Microsoft.BatchAI/clusters/demoCluster",
    "resourceGroup": "alex"
  },
  "cntkSettings": {
    "commandLineArgs": null,
    "configFilePath": null,
    "languageType": "Python",
    "processCount": 1,
    "pythonInterpreterPath": null,
    "pythonScriptFilePath": "$AZ_BATCHAI_MOUNT_ROOT/afs/demo/ConvNet_MNIST.py"
  },
  "constraints": {
    "maxWallClockTime": "7 days, 0:00:00"
  },
  "containerSettings": {
    "imageSourceRegistry": {
      "credentials": null,
      "image": "ubuntu",
      "serverUrl": null
    }
  },
  "creationTime": "2017-11-21T22:31:22.128000+00:00",
  "customToolkitSettings": null,
  "environmentVariables": [],
  "executionInfo": {
    "endTime": "2017-11-21T22:31:50.134000+00:00",
    "errors": [
      {
        "code": "JobFailed",
        "details": null,
        "message": "Job failed with non-zero exit code"
      }
    ],
    "exitCode": 127,
    "startTime": "2017-11-21T22:31:25.128000+00:00"
  },
  "executionState": "failed",
  "executionStateTransitionTime": "2017-11-21T22:31:50.134000+00:00",
  "experimentName": null,
  "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/demoGroup/providers/Microsoft.BatchAI/jobs/job2",
  "inputDirectories": [
    {
      "id": "INPUT",
      "path": "$AZ_BATCHAI_MOUNT_ROOT/afs"
    }
  ],
  "jobPreparation": null,
  "location": null,
  "name": "tests",
  "nodeCount": 1,
  "outputDirectories": [],
  "priority": 0,
  "provisioningState": "succeeded",
  "provisioningStateTransitionTime": "2017-11-21T22:31:23.003000+00:00",
  "resourceGroup": "alex",
  "stdOutErrPathPrefix": "$AZ_BATCHAI_MOUNT_ROOT/afs/",
  "tensorFlowSettings": null,
  "toolType": "cntk",
  "type": "Microsoft.BatchAI/Jobs"
}
```

In this output you can find information about the job (toolkit, container, input/output directories, container, etc),
failure reason, execution time and other information.

## Access Files in Output Directories
You can enumerate files in job's output directories by using `az batchai job list-files` command. For example, the
following command will list files in standard `stdouterr` directory containing job and job preparation stdout and stderr
files for the job `job2`:
  
```bash
az batchai job list-files -n job2 -g demoGroup -d stdouterr
```

Example output:

```
[
  {
    "contentLength": 733,
    "downloadUrl": "https://demobatchaicli.file.core.windows.net/demoShare/00000000-0000-0000-0000-000000000000/demo/jobs/job2/stderr.txt?sv=2016-05-31&sr=f&sig=Rh%2BuTg9C1yQxm7NfA9YWiKb%2B5FRKqWmEXiGNRDeFMd8%3D&se=2017-10-05T07%3A44%3A38Z&sp=rl",
    "lastModified": "2017-10-05T06:44:38+00:00",
    "name": "stderr.txt"
  },
  {
    "contentLength": 300,
    "downloadUrl": "https://demobatchaicli.file.core.windows.net/demoShare/00000000-0000-0000-0000-000000000000/demo/jobs/job2/stdout.txt?sv=2016-05-31&sr=f&sig=jMhJfQOGry9jr4Hh3YyUFpW5Uaxnp38bhVWNrTTWMtk%3D&se=2017-10-05T07%3A44%3A38Z&sp=rl",
    "lastModified": "2017-10-05T06:44:29+00:00",
    "name": "stdout.txt"
  }
]
```

To enumerate files in other output directories (e.g. `MODEL`) provide directory ID in `-d` argument.

Note, currently you can list output directories only if they are configured on Azure File Share or Azure Container.

## Stream Files from Output Directories

You can stream (similar to GNU/Linux `tail -f` command) the job's output using `az batchai job stream-file` command:

```bash
$ az batchai job stream-file -j job2 -g demoGroup -d stdouterr -n stdout.txt 
```

this command will periodically check stdout.txt file and print its updates on the screen. You need to press `Ctrl-C` to 
interrupt the output.

Note, `az` does not know which files your job will generate, so it accepts any file name and waits for this file to 
become available.

Note, if Azure Container is configured as an output directory, the file will become available for streaming only when job
closes the file.

## SSH to Job Nodes
You can find information about nodes executed a job using `az batchai job list-nodes` command. For example,

```bash
$ az batchai job list-nodes -n democJob -g demoGroup -o table
```

Example output:
```
ID                                 IP               Port
---------------------------------  -------------  ------
tvm-1783593343_1-20171127t163917z  52.168.39.226   50000
```

Use returned IP address and port to ssh to the node, e.g.

```bash
$ ssh -p 50000 52.168.39.226
```

## Jobs Termination and Deletion

You can terminate and delete jobs using `az batchai job terminate` and `az batchai job delete` commands. Both commands
require you to confirm the action, so if you are going to use this commands from non-interactive scripts, please provide
`-y` parameter. Job deletion may take a long time, specify `--no-wait` to skip waiting if you need to submit multiple
requests simultaneously.

For example,

```bash
$ az batchai job delete -n job3 -g demoGroup -y --no-wait
``` 

will submit `job3` deletion request without confirmation and return execution immediately without waiting for the
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
    --name -n [Required]: Name of the file server.
    --location -l       : Location. You can configure the default location using `az configure
                          --defaults location=<location>` or specify it in the file server
                          configuration file.  Default: eastus.
    --no-wait           : Do not wait for the long running operation to finish.
    --resource-group -g : Name of resource group. You can configure the default group using `az
                          configure --defaults group=<name>`.  Default: alex.
    --vm-size -s        : VM size.

Admin Account Arguments
    --admin-user-name -u: Name of the admin user to be created on every compute node.
    --password -p       : Password.
    --ssh-key -k        : SSH public key value or path.

Advanced Arguments
    --config -c         : A path to a json file containing file server create parameters (json
                          representation of azure.mgmt.batchai.models.FileServerCreateParameters).
                          Note, parameters given via command line will overwrite parameters
                          specified in the configuration file.

Storage Arguments
    --disk-count        : Number of disks.
    --disk-size         : Disk size in Gb.
    --storage-sku       : The sku of storage account to persist VM.  Allowed values: Premium_LRS,
                          Standard_GRS, Standard_LRS, Standard_RAGRS, Standard_ZRS.  Default:
                          Premium_LRS.

Global Arguments
    --debug             : Increase logging verbosity to show all debug logs.
    --help -h           : Show this help message and exit.
    --output -o         : Output format.  Allowed values: json, jsonc, table, tsv.  Default: json.
    --query             : JMESPath query string. See http://jmespath.org/ for more information and
                          examples.
    --verbose           : Increase logging verbosity. Use --debug for full debug logs.
```

For example,

```bash
$ az batchai file-server create -l eastus -g demoGroup -n demoNFS -s Standard_D1 --disk-count 1 --disk-size 10 --storage-sku Premium_LRS -u demoUser -p demoPassword
```

will create a single node NFS in East US region in `demoGroup` resource group. The NFS will have one 10Gb data disk
backed by premium storage. You will be able to ssh to this NFS using `demoUser` account and `demoPassword` password.

Please take a look at `Admin User Account` section above discussing ssh public key usage.

You can configure NFS to have more than one disk, in this case the disks will be combined in RAID LEVEL 0 increasing the
capacity and bandwidth. Note, you need to chose VM size matching the total bandwidth of the attached disks to get the 
benefit of RAID-0.

## Monitoring
Similar to clusters, you can list NFSes and get information about particular NFS using `az batchai file-server list` and
`az batchai file-server show` commands.

For example, 

```bash
az batchai file-server list -o table -g ''
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