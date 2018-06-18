from __future__ import print_function

import json
import os
import time
import re
import numpy
import uuid
import requests
import azure.mgmt.batchai.models as models

#  Class and helper functions for hyperparameter tuning
class Hyperparameter:
    """Class to define a hyperparameter used for the training job"""

    def __init__(self, name, symbol, type, value):
        self.name = name
        self.symbol = symbol
        self.type = type
        self.value = value

    def generate(self):
        """
        Generate a random instance of the defined hyperparameter
        """
        if self.type == "uniform":
            return numpy.random.uniform(self.value[0], self.value[1])
        elif self.type == "log":
            return numpy.exp(numpy.random.uniform(numpy.log(self.value[0]), numpy.log(self.value[1])))
        elif self.type == "choice":
            return self.value[numpy.random.randint(0, len(self.value))]

    def get_random_hyperparameter_configuration(space):
        """
        Generate random configurations given the hyperparameter space
        """
        vars = {}
        for p in space:
            vars[p.symbol] = p.generate()
        return vars

class MetricExtractor:
    """
    Helper class to extract desired metric from job's output files.
    
    list_option:  job list-file option used to obtain learning log file download URL
    logfile: the name of learning log file
    regex: the regular expression to extract the desired metric from log text
    metric: option to aggregate the desired metric, default is the last occurrence 
    
    """
    def __init__(self, list_option, logfile, regex, metric = "last"):
        self.list_option = list_option
        self.logfile = logfile
        self.regex = regex
        self.metric = metric

    def get_metric(self, job_name, resource_group, workspace_name, experiment_name, client):
        files = client.jobs.list_output_files(resource_group, workspace_name, experiment_name, job_name,
                                              models.JobsListOutputFilesOptions(outputdirectoryid=self.list_option))
        val = float("inf")
        for file in list(files):
            if file.name == self.logfile:
                text = ""
                try:
                    r = requests.get(file.download_url, stream=True)
                    for chunk in r.iter_content(chunk_size=512 * 1024):
                        if chunk:  # filter out keep-alive new chunks
                            text += chunk.decode(encoding='UTF-8')
                except Exception as e:
                    print(e)
                vals = re.findall(self.regex, text, re.DOTALL)
                if self.metric is "last":
                    val = float(vals[len(vals) - 1])
                elif self.metric is "mean":
                    val = sum([float(m) for m in vals])/len(vals)
                elif self.metric is "min":
                    val = min([float(m) for m in vals])
                elif self.metric is "max":
                    val = max([float(m) for m in vals])
                break

        return val

def run_then_return_metric(config_index, resource_group, workspace_name, experiment_name, 
                            parameter, client, metric_extractor, result, delete_job=True):
    """
    Submit a job with gvien parameter 

    Waits for job completion and extract the metric form log file specified by output_directory_id
    and file_name.

    Finally delete the job
    """

    job_name = str(uuid.uuid4())[:8]
    try:
        _ = client.jobs.create(resource_group, workspace_name, experiment_name, job_name, parameter).result()
        polling_interval = 5
        while True:
            job = client.jobs.get(resource_group, workspace_name, experiment_name, job_name)
            if job.execution_state == models.ExecutionState.succeeded or job.execution_state == models.ExecutionState.failed:
                break
            time.sleep(polling_interval)

        val = metric_extractor.get_metric(job_name=job_name, resource_group=resource_group, workspace_name=workspace_name, 
                                          experiment_name=experiment_name, client=client)
        result.put((val, config_index))
        print("Job {0} has completed for config {1}".format(job_name, config_index))
        

    except Exception as e:
        print(e)

    finally:
        if delete_job:
            client.jobs.delete(resource_group, workspace_name, experiment_name, job_name).result()