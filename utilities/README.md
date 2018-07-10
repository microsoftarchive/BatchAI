# Batch AI Utilities

A collection of tools for creating and monitoring jobs using the Azure Batch 
AI Python SDK.

## Features
- support for configuration file (for Azure Active Directory and Azure 
Storage credentials)
- show status of clusters and jobs
- list and download output files from jobs
- wait on job completion and stream output from jobs
- job factories to generate jobs with parameter sweeps and file enumeration
- bulk job submission and resubmission of failed jobs
- metric extraction from job logfile

## User Guides
* [Job Factory](#job-factory)
* [Experiment Utilities](#experiment-utilities)

## Job Factory

The Job Factory tool enables generating collections of jobs with parameter 
sweeps and file enumeration, and easy-to-use parameter substitution.

### Use Cases
* enumerating combinations of parameters as configuration variables in a training script (e.g. for hyperparameter tuning)
* creating a job for each file in an Azure File/Blob storage (e.g. train one model per data file)

### Features
* supports numerical parameters, discrete parameters, and files in an Azure File/Blob storage
* substitutes parameters into JobCreateParameters object

### Usage
Performing a parameter sweep involves two steps: defining parameter 
specifications and substituting parameters into your JobCreateParameters 
object. In this example, we create 4 jobs with different learning rates, 
implemented via a command line argument to the input script.

#### 1. Define Parameter Specifications

Create a list of parameter specifications:
```
from utilities.job_factory import NumParamSpec, ParameterSweep
from utilities.experiment import ExperimentUtils

param_spec_list = [
    NumParamSpec(
        parameterName='LEARNING_RATE',
        start=1e-4,
        end=1e-1,
        dataType='REAL',
        numValues=4,
        scale="LOG"
    ) # will generate [1e-4, 1e-3, 1e-2, 1e-1]
]
```

For more details on the types of parameters allowed, see [below](#parameter-specifications).

#### 2. Substitute Parameters into JobCreateParameters

Create a ParameterSweep object as a template for parameters:
```
parameters = ParameterSweep(param_spec_list)
```

Use this object to specify where you want parameters substituted:
```
jcp = models.JobCreateParameters(
    cluster=models.ResourceId(
        id=cluster.id),
    node_count=2,
    input_directories=input_directories,
    std_out_err_path_prefix=std_output_path_prefix,
    container_settings=models.ContainerSettings(
        image_source_registry=models.ImageSourceRegistry(
            image='tensorflow/tensorflow:1.8.0-gpu')),
    tensor_flow_settings=models.TensorFlowSettings(
        python_script_file_path='$AZ_BATCHAI_INPUT_SCRIPT/train.py',
        master_command_line_args='--learning-rate={0}'.format(parameters['LEARNING_RATE'])))
```

In the 4 jobs that are submitted, 
`models.JobCreateParameters.tensor_flow_settings.master_command_line_args` will 
equal `--learning-rate=1e-4`, `--learning-rate=1e-3`, `--learning-rate=1e-2`, 
and `--learning-rate=1e-1`. Furthermore, an environment variable 
`$PARAM_LEARNING_RATE` will be set in the job container.

The `parameters[<parameterName>]` variable can be used with string substitution (like above) or directly to substitute a variable (e.g. `node_count=parameters['NODE_COUNT']` and `master_command_line_args=parameters['CMD_LINE_ARGS']'`).

#### 3. Generate Jobs

To generate the jobs with a grid search, use the following code. The number 
of jobs generated will be the product of the number of possible values for 
each parameter. Every possible combination of parameters will be enumerated.
```
jobs_to_submit = parameters.generate_jobs(jcp)
```

To generate the jobs with a random search, use the following code. You must 
specify the number of jobs to generate. Each job will contain a randomly 
generated value of each parameter.
```
num_jobs = 16
jobs_to_submit = parameters.generate_jobs_random_search(jcp, num_jobs)
```

To submit the jobs from the `parameters` and `jcp` objects:
```
experiment_utils = ExperimentUtils(client, resource_group_name, workspace_name, 
experiment_name)
submission = experiment_utils.submit_jobs(jcp, parameters, "job_name_prefix")
```

### Parameter Specifications

This library supports four types of parameters: 

__Numerical Parameters__

Arguments:
* parameterName: the name of the parameter. Only capital letters and underscores are allowed. Required.
* dataType: "INTEGER" or "REAL". If "INTEGER", all generated values will be rounded to the nearest integer. For "REAL", decimal values will be retained. Required.
* start: the lowest value of this parameter (inclusive). Required.
* end: the highest value of this parameter (inclusive). Required.
* scale: "LINEAR" or "LOG" or "RANDOM_UNIFORM"; how values should be distributed in the range [start, end]. Required.
* numValues: num_values: the number of values to generate in the range.
        Required if performing grid search sweep and scale is "LOG".
* step: step: the interval size between each parameter. Required if
        performing grid search sweep and scale is "LINEAR".

Examples:

```
NumParamSpec(
    parameterName="BATCH_SIZE",
    start=10,
    end=50,
    step=10,
    dataType='INTEGER',
    scale="LINEAR"
)
# will generate [10, 20, 30, 40, 50]
```

```
NumParamSpec(
    parameterName="LEARNING_RATE",
    start=1e-4,
    end=1e-1,
    dataType='REAL',
    numValues=4,
    scale="LOG"
)
# will generate [1e-4, 1e-3, 1e-2, 1e-1]
```

__Discrete Parameters__

For specifying a custom list of parameters.

Arguments:
* parameterName: the name of the parameter. Only capital letters and underscores are allowed. Required.
* values: a list of values for the parameter. The values supplied must be a string, integer, or float. Required.

Examples:

```
DiscreteParamSpec(
    parameterName="DEVICE_ID",
    values=["Device_1", "Device_2", "Device_3"]
)
# will generate ["Device_1", "Device_2", "Device_3"]
```

__Dictionary Parameters__

For specifying a custom list of parameters, which each parameter is a dictionary of parameters. This method allows pairs of parameters to be grouped together during combination generation.

Arguments:
* parameterName: the name of the parameter. Only capital letters and underscores are allowed. Required.
* values: a list of values for the parameter, where each value is a dictionary.

Examples:

```
DictParamSpec(
    parameterName="HYPERPARAMS",
    values=[{
        "LEARNING_RATE": 1e-4,
        "HIDDEN_LAYER_SIZE": 100
    }, {
        "LEARNING_RATE": 1e-3,
        "HIDDEN_LAYER_SIZE": 200
    }, {
        "LEARNING_RATE": 1e-2,
        "HIDDEN_LAYER_SIZE": 300
    }]
)
# will generate 3 jobs
```

The values can be substituted with `parameters['HYPERPARAMS']['LEARNING_RATE']` and  `parameters['HYPERPARAMS']['HIDDEN_LAYER_SIZE']`.

__File Parameters__

For generating a list of files stored in an Azure File/Blob storage. The File share or Blob container must be mounted to the job (or the cluster the job is running on) for file parameter sweeping to work.

Arguments:
* parameterName: the name of the parameter. Only capital letters and underscores are allowed. Required.
* storageAccountName: the name of the Azure storage account to use. Required.
* storageAccountKey: the key of the Azure storage account to use. Required.
* storageType: "BLOB" or "FILE". Whether accessing files in Azure Blob container or an Azure File share. Required.
* mountMethod: "JOB" or "CLUSTER". Whether the Azure storage volume was mounted through the JobCreateParameters or ClusterCreateParameters. Required.
* mountPath: the `models.AzureBlobFileSystemReference.relative_mount_path` or `models.AzureFileShareReference.relative_mount_path` specified when mounting the Blob container or File share. Required.
* container: the name of the Blob container. Required if storageType is "BLOB".
* fileshare: the name of the File share. Required if storageType is "FILE".
* directory: the directory that contains the files to be listed. If unspecified, all files in the File share will be listed (this may take a long time).
* filterStr: a regex, used with re.match, which must match the full path of the file for the file to be returned. If unspecified, all files will be returned.

Examples:

```
FileParamSpec(
    parameterName="DATA_INPUT",
    storageAccountName="example_name",
    storageAccountKey="example_key",
    storageType="BLOB",
    mountPath="bfs",
    container="example_container",
    filterStr="/data/.+"
)
# if example_container contains the blobs
# - /other/a.txt
# - /b.txt
# - /data/c.txt
# - /data/d.txt
# then this spec will generate ['$AZ_BATCHAI_MOUNT_ROOT/bfs/data/c.txt', '$AZ_BATCHAI_MOUNT_ROOT/bfs/data/d.txt']
```

```
FileParamSpec(
    parameterName="DATA_INPUT",
    storageAccountName="example_name",
    storageAccountKey="example_key",
    storageType="FILE",
    mountPath="afs",
    fileshare="example_share",
    directory="data"
)
# if example_share contains the files
# - /other/a.txt
# - /b.txt
# - /data/c.txt
# - /data/d.txt
# then this spec will generate ['$AZ_BATCHAI_MOUNT_ROOT/afs/data/c.txt', '$AZ_BATCHAI_MOUNT_ROOT/afs/data/d.txt']
```

## Experiment Utilities

The ExperimentUtils class has several methods for helping submit and monitor 
jobs in an experiment.

### Usage
To use ExperimentUtils, create an object using a `BatchAIManagementClient` 
instance, and the name of the experiment you wish to use.
```
from utilities.experiment import ExperimentUtils
experiment_utils = ExperimentUtils(client, resource_group_name, 
workspace_name, experiment_name)
``` 

#### Bulk Job Submission
```
submit_jobs(jcp_list, job_name_prefix, max_retries=NUM_RETRIES,
            num_threads=NUM_THREADS)
```
Submit jobs with the JobCreateParameters in jcp_list. Jobs have name 
job_name_prefix with a hash of the JobCreateParameters object appended.

Arguments
- jcp_list: a list of JobCreateParameters objects to submit
- job_name_prefix: prefix for job names
- max_retries: number of retries if server returns 5xx for
submission
- num_threads: number of threads to use for submission
- return: a concurrent.futures.Future object. Call .result() on the
return object to get the list of azure.mgmt.batchai.models.Job submitted

#### Wait All Jobs
```
wait_all_jobs(job_names=None, on_progress=None)
```
Block until all jobs in the experiment are completed (succeeded or failed).

Arguments
- job_names: names of jobs to wait for. If None, wait until all
jobs in experiment are completed.
- on_progress: a function that wait_all_jobs will call every 10
secs with list of azure.mgmt.batchai.models.Job, representing current
state of jobs
- return: list of completed Jobs

#### Resubmit Failed Jobs
```
resubmit_failed_jobs(job_names=None, max_retries=NUM_RETRIES,
                     num_threads=NUM_THREADS)
```
Resubmit the failed jobs in an experiment.

Arguments
- job_names: names of jobs to resubmit. If None, all jobs will
be resubmitted.
- max_retries: number of retries if server returns 5xx for
submission
- num_threads: number of threads to use for submission
- return: list of Jobs that were resubmitted

#### Get Metrics for Jobs
```
get_metrics_for_jobs(jobs, metric_extractor)
```
Gets the metrics for a collection of jobs in the experiment.

Arguments
- jobs: a collection of azure.mgmt.batchai.models.Job objects
- metric_extractor: an instance of utilities.job.MetricExtractor
- return: a list of dictionaries with keys "job_name" (the name of the
job), "job" (the Job object), "metric_value" (the extracted value of
the metric).

#### Delete Jobs in Experiment
```
delete_jobs_in_experiment(execution_state=None, job_names=None,
                          num_threads=NUM_THREADS)
```
Delete the jobs in the experiment.

Arguments
- execution_state: one of azure.mgmt.batchai.models.ExecutionState. Delete 
only jobs with this execution state. If None, delete jobs regardless of 
execution state.
- job_names: List of names of jobs to resubmit. If none, all failed jobs in 
the experiment are resubmitted.
- job_name_regex: regex used with re.match to match names of jobs to delete
- num_threads: number of threads to use for deletion.
- return: None