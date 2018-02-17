# Azure Batch AI environment variables

The Azure Batch AI service sets the following environment variables on VMs. You can reference these environment variables in your training job configuration, such as command lines, input/output directories, and user defined environment variables. 

The environment variables are available for job using Docker container as well as directly running on host VM.

## Environment variable visibility
These environment variables are visible only in the context of the Batch AI job user, the user account on the node under which a training job is executed. You will not see these if you connect remotely to a compute node via Secure Shell (SSH) and list the environment variables. This is because the user account that is used for remote connection is not the same as the account that is used by the job.

## Environment Variables

| Variable name | Description | Availability | Example |
|---------------|-------------|--------------|---------|
| AZ_BATCHAI_MOUNT_ROOT | the mount root for all external file systems | All Jobs | /mnt/batch/tasks/shared/LS_root/mounts |
|AZ_BATCHAI_JOB_TEMP|the temporary job directory created for each job|All Jobs|/mnt/batch/tasks/shared/LS_root/jobs/job01|
|AZ_BATCHAI_JOB_TEMP_DIR|the root directory of all temporary job directories|All Jobs|/mnt/batch/tasks/shared/LS_root/jobs/|
|AZ_BATCHAI_JOB_TEMP|the temporary job directory created for each job|All Jobs|/mnt/batch/tasks/shared/LS_root/jobs/job01|
|AZ_BATCHAI_SHARED_JOB_TEMP|the shared NFS temporary job directory created for each job|All Jobs|/mnt/batch/tasks/shared/LS_root/jobs/job01/shared|
|AZ_BATCHAI_STDOUTERR_DIR|the absolute directory path where job stdout and stderr log locate|All Jobs|/mnt/batch/tasks/shared/LS_root/mounts/nfs/0000-000-0000-0000/myrg/jobs/myjob/0000-000-0000-0000|
|AZ_BATCHAI_MPI_HOST_FILE|the absolute file path for OpenMPI hostfile|All Jobs|/mnt/batch/tasks/shared/LS_root/jobs/job01/hostfile|
|AZ_BATCHAI_NUM_GPUS|the number of GPUs on the VM|All Jobs|4|
|AZ_BATCHAI_PS_HOSTS|the list of hosts addresses for TensorFlow parameter servers|TensorFlow|`10.0.0.4:2222`|
|AZ_BATCHAI_WORKER_HOSTS|the list of hosts addresses for TensorFlow workers|TensorFlow|`10.0.0.4:2223,10.0.0.5:2222`|
|TF_CONFIG|Environment variable to set up a distributed processing cluster for TensorFlow|TensorFlow|`{"cluster":{"ps":["10.0.0.4:2222"],"worker":["10.0.0.4:2223","10.0.0.5:2223"]},"task":{"type":"master","index":0},"environment":"cloud"}`|
|AZ_BATCHAI_TASK_INDEX|the sub task index of each worker in a distributed training job|TensorFlow/Caffe2|0|