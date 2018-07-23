from __future__ import print_function

import copy
import itertools
import json
import posixpath
import re
from builtins import *

import azure.mgmt.batchai.models as models
import azure.storage.file.models
import numpy as np
import six
from azure.storage.blob import BlockBlobService
from azure.storage.file import FileService
from jsonschema import validate


class Parameter(object):
    def __init__(self, parameter_name):
        if not re.match("^[A-Z_][A-Z0-9_]*$", parameter_name):
            raise ValueError(
                "Invalid parameter name {0}. Name only include uppercase "
                "letters, digits, and underscores".format(parameter_name))
        self.parameter_name = parameter_name
        self.values = []

    def get_random(self):
        return self.values[np.random.randint(0, len(self.values))]


class NumericParameter(Parameter):
    ENDPOINT_OFFSET = 0.001

    def __init__(self, parameter_name, data_type, start, end, scale,
                 num_values=None, step=None):
        """
        Create a specification for a number parameter. If using generating
        jobs with random search, num_values/step is not required.

        :param parameter_name: the name of the parameter
        :param data_type: "INTEGER" or "REAL". If "INTEGER", all generated
        values will be rounded to the nearest integer. For "REAL", decimal
        :param start: the lowest value of this parameter (inclusive)
        :param end: the highest value of this parameter (inclusive)
        :param scale: "LINEAR" or "LOG"; how values should be distributed in
        the range [start, end]
        :param num_values: the number of values to generate in the range.
        Required if performing grid search sweep and scale is "LOG".
        :param step: the interval size between each parameter. Required if
        performing grid search sweep and scale is "LINEAR".
        """
        super().__init__(parameter_name)
        if start >= end:
            raise ValueError("End value must be greater than start value")
        if scale not in ["LINEAR", "LOG"]:
            raise ValueError("Invalid scale")
        if data_type not in ["INTEGER", "REAL"]:
            raise ValueError("Invalid data type")
        self.data_type = data_type
        self.start = start
        self.end = end
        self.scale = scale
        self.num_values = num_values
        self.step = step
        if self.num_values or self.step:
            self.values = self._generate_values()

    def _generate_values(self):
        if self.scale == 'LINEAR' and self.step:
            values = list(np.arange(self.start, self.end +
                                    self.ENDPOINT_OFFSET, self.step))
        elif self.scale == 'LINEAR' and self.num_values:
            values = list(np.linspace(self.start, self.end,
                                      self.num_values))
        elif self.scale == 'LOG' and self.num_values:
            values = list(np.geomspace(self.start, self.end,
                                       self.num_values))
        else:
            raise ValueError("Invalid configuration of NumericParameter")
        if self.data_type == 'REAL':
            pass
        elif self.data_type == 'INTEGER':
            values = [int(round(val)) for val in values]
        else:
            raise ValueError("Invalid data type {} in NumericParameter".format(
                self.data_type
            ))
        return values

    def get_random(self):
        if self.scale == 'LINEAR':
            return np.random.uniform(self.start, self.end)
        elif self.scale == 'LOG':
            return np.exp(np.random.uniform(np.log(self.start),
                                            np.log(self.end)))


class DiscreteParameter(Parameter):
    def __init__(self, parameter_name, values):
        """
        Create a specification for a discrete parameter.

        :param parameter_name: the name of the parameter
        :param values: a list of values for the parameter
        """
        super().__init__(parameter_name)
        self.validate(values)
        self.values = values

    def validate(self, values):
        for val in values:
            if (not isinstance(val, float) and
                    not isinstance(val, int) and
                    not isinstance(val, six.string_types)):
                raise ValueError("Values must be string, int, or float.")


class DictParameter(Parameter):
    def __init__(self, parameter_name, values):
        """
        For specifying a custom list of parameters, which each parameter is a
        dictionary of parameters. This method allows pairs of parameters to be
        grouped together during combination generation.

        :param parameter_name: the name of the parameter
        :param values: a list of dictionary objects
        """
        super().__init__(parameter_name)
        self.validate(values)
        self.values = values
        self.dict_keys = values[0].keys()

    def validate(self, values):
        if not values:
            raise ValueError("Param has no values")
        d_0 = values[0]
        for d in values:
            if set(d.keys()) != set(d_0.keys()):
                raise ValueError("All dicts must have the same keys")
            for d_val in d.values():
                if (not isinstance(d_val, float) and
                        not isinstance(d_val, int) and
                        not isinstance(d_val, str)):
                    raise ValueError("Values must be string, int, or float.")


class FileParameter(Parameter):

    def __init__(self, parameter_name, storage_account_name,
                 storage_account_key, storage_type, mount_path, mount_method,
                 container=None, fileshare=None, directory=None,
                 filter_str=None):
        """
        For generating a list of files stored in an Azure File/Blob storage.
        The File share or Blob container must be mounted to the job (or the
        cluster the job is running on) for file parameter sweeping to work.
        
        :param parameter_name: the name of the parameter
        :param storage_account_name: the name of the Azure storage account to
        use
        :param storage_account_key: the key of the Azure storage account to
        use
        :param storage_type: "BLOB" or "FILE". Whether accessing files in
        Azure Blob container or an Azure File share.
        :param mount_method: "JOB" or "CLUSTER". Whether the Azure storage
        volume was mounted through the JobCreateParameters or
        ClusterCreateParameters
        :param mount_path: the
        models.AzureBlobFileSystemReference.relative_mount_path or
        models.AzureFileShareReference.relative_mount_path
        specified when mounting the Blob container or File share.
        :param container: the name of the Blob container. Required if
        storage_type is "BLOB".
        :param fileshare: the name of the File share. Required if
        storage_type is "FILE".
        :param directory: the directory that contains the files to be
        listed. If unspecified, all files in the File share will be listed (this
        may take a long time).
        :param filter_str: a regex, used with re.match, which must match the
        full path of the file for the file to be returned. If unspecified, all
        files will be returned.
        """
        super().__init__(parameter_name)
        if mount_method == "JOB":
            mount_root = "$AZ_BATCHAI_JOB_MOUNT_ROOT"
        elif mount_method == "CLUSTER":
            mount_root = "$AZ_BATCHAI_MOUNT_ROOT"
        else:
            raise ValueError('Invalid mount method')
        if storage_type == 'BLOB' and container:
            blob_service = BlockBlobService(
                storage_account_name, storage_account_key)
            blobs = blob_service.list_blobs(container)
            blob_names = [b.name for b in blobs]
            if filter_str:
                blob_names = [
                    b for b in blob_names
                    if re.match(filter_str, b) is not None
                ]
            blob_paths = [
                posixpath.join(mount_root, mount_path, blob_name)
                for blob_name in blob_names
            ]
            self.values = blob_paths
        elif storage_type == 'FILE' and fileshare:
            file_service = FileService(storage_account_name, storage_account_key)
            file_paths = self._list_files_in_fileshare(
                file_service, fileshare, root_dir=directory)
            if filter_str:
                file_paths = [
                    f for f in file_paths
                    if re.match(filter_str, f) is not None
                ]
            file_paths = [
                posixpath.join(mount_root, mount_path, file_path)
                for file_path in file_paths
            ]
            self.values = file_paths
        else:
            raise ValueError('Invalid options for file parameter sweep')

    def _list_files_in_fileshare(self, service, fileshare, root_dir):
        """
        List the paths of all files in share.

        :param client: instance of azure.storage.file.FileService
        :param fileshare: file share name
        :param root_dir: root directory. If None, all files in fileshare
        are listed
        :return: list of paths of files in the file share
        """
        files = []
        dirs = [root_dir]
        while dirs:
            current_dir = dirs.pop()
            files_in_dir = service.list_directories_and_files(
                share_name=fileshare,
                directory_name=current_dir
            )
            for f in files_in_dir:
                if current_dir is not None:
                    file_path = posixpath.join(current_dir, f.name)
                else:
                    file_path = f.name
                if isinstance(f, azure.storage.file.models.File):
                    files.append(file_path)
                else:  # f is a directory
                    dirs.append(file_path)
        return files


class ParameterSweep(object):

    def __init__(self, param_specs):
        """
        Creates a ParameterSweep object which can used as a placeholder for
        parameter substitution. Sets Substitution objects as instance variables
        of this object, corresponding to the parameters in param_specs.

        :param param_specs: a list of Parameter objects
        """
        if not param_specs:
            raise ValueError("No params in ParameterSweep init")
        self.param_specs = param_specs
        for param_spec in param_specs:
            if isinstance(param_spec, DictParameter):
                sub = Substitution(param_spec.parameter_name)
                setattr(self, param_spec.parameter_name, sub)
                for key in param_spec.dict_keys:
                    dict_parameter_name = param_spec.parameter_name + '__' + key
                    setattr(self, dict_parameter_name, Substitution(
                        dict_parameter_name))
                    sub.dictParams[key] = Substitution(dict_parameter_name)
            else:
                setattr(self, param_spec.parameter_name, Substitution(
                    param_spec.parameter_name))

    @classmethod
    def from_json(cls, param_specs_json):
        """
        Converts a JSON file containing a parameter sweep configuration into
        a list of Parameter objects. The configuration file must match the
        schema specified in param_sweep_spec_schema.json.

        :param param_specs_json: a file containing a parameter sweep
        specification
        """
        with open('param_sweep_spec_schema.json', 'r') as f:
            schema = json.load(f)
        validate(param_specs_json, schema)
        param_specs = []
        for p in param_specs_json['params']:
            param_spec = None
            if p['paramType'] == 'NumParam':
                param_spec = NumericParameter(
                    parameter_name=p['parameterName'],
                    data_type=p['dataType'],
                    start=p['start'],
                    end=p['end'],
                    scale=p['scale'],
                    step=(p['step'] if 'step' in p else None),
                    num_values=(p['numValues'] if 'numValues' in p else None)
                )
            elif p['paramType'] == 'DiscreteParam':
                param_spec = DiscreteParameter(
                    parameter_name=p['parameterName'],
                    values=p['values']
                )
            elif p['paramType'] == 'DictParam':
                param_spec = DictParameter(
                    parameter_name=p['parameterName'],
                    values=p['values']
                )
            elif p['paramType'] == 'FileParam':
                param_spec = FileParameter(
                    parameter_name=p['parameterName'],
                    storage_account_name=p['storageAccountName'],
                    storage_account_key=p['storageAccountKey'],
                    storage_type=p['storageType'],
                    mount_method=p['mountMethod'],
                    mount_path=p['mountPath'],
                    container=(p['container'] if 'container' in p else None),
                    fileshare=(p['fileshare'] if 'fileshare' in p else None),
                    filter_str=(p['filterStr'] if 'filterStr' in p else None)
                )
            if not param_spec:
                raise ValueError("Invalid param spec type")
            param_specs.append(param_spec)
        return cls(param_specs)

    def __getitem__(self, key):
        """
        Allows this object's variables to be accessed through bracket syntax.
        """
        return getattr(self, key)

    def generate_jobs(self, job_create_parameters):
        """
        Generate jobs with grid search.

        :param job_create_parameters: an instance of JobCreateParameters
        :return: a list of JobCreateParameters with parameters substituted
        through grid search
        """
        return self._generate_jobs(job_create_parameters)

    def generate_jobs_random_search(self, job_create_parameters, num_jobs):
        """
        Generate jobs with random search. Jobs will be generated with each
        parameter value being randomly generated.

        :param job_create_parameters: an instance of JobCreateParameters
        :param num_jobs: the number of jobs to generate.
        :return: a list of JobCreateParameters with parameters substituted
        through random search
        """
        if num_jobs <= 0:
            raise ValueError("Num jobs must be greater than 0")
        return self._generate_jobs(job_create_parameters, num_jobs=num_jobs)

    def _generate_jobs(self, job_create_parameters, num_jobs=None):
        """
        Creates copies of job_create_parameters with the template strings
        and Substitution objects substituted with combinations of parameters
        specified in param_specs.

        :param job_create_parameters: an instance of JobCreateParameters
        :param num_jobs: the number of jobs to generate with random search. If
        None, grid search will be performed.
        """
        jcps = []
        param_dicts = []
        for param_dict in self._generate_param_dicts(num_jobs):
            jcp_substituted = self._substitute_params(
                job_create_parameters, param_dict)
            environment_variables = [models.EnvironmentVariable(
                name=parameter_name,
                value=str(value)
            ) for parameter_name, value in param_dict.items()]
            jcp_substituted.environment_variables = environment_variables
            jcps.append(jcp_substituted)
            param_dicts.append(param_dict)
        return jcps, param_dicts

    def _generate_param_dicts(self, num=None):
        """
        Generates a dict with parameter combinations from the Cartesian
        product of possible parameter values specified by param_specs.

        :param num: the number of jobs to generate with random search. If None,
        grid search will be performed.
        """
        num_params = len(self.param_specs)
        param_names = [ps.parameter_name for ps in self.param_specs]
        param_values = [ps.values for ps in self.param_specs]
        if num:
            param_combinations = [[p.get_random() for p in self.param_specs]
                                  for _ in range(num)]
        else:
            param_combinations = itertools.product(*param_values)
        for param_combination in param_combinations:
            param_dict = {}
            for i in range(num_params):
                param = param_combination[i]
                param_name = param_names[i]
                if isinstance(param, dict):  # Handling DictParameter
                    for key, value in param.items():
                        dict_param_name = param_name + '__' + key
                        param_dict[Substitution.convert_name(
                            dict_param_name)] = value
                else:
                    param_dict[Substitution.convert_name(param_name)] = param
            yield param_dict

    def _substitute_params(self, job_create_parameters, param_dict):
        """
        Creates a copy of job_create_parameters and substitutes properties in
        it with the parameter combination in param_dict.
        """
        jcp_copy = copy.deepcopy(job_create_parameters)
        self._replace_properties_with_params(jcp_copy, param_dict)
        return jcp_copy

    def _replace_properties_with_params(self, obj, param_dict):
        """
        Do a recursive search through the object's properties, substituting
        Substitution objects and strings which are parameter templates
        with a parameter combination specified by param_dict.
        """
        try:
            for prop, val in vars(obj).items():
                if isinstance(val, six.string_types):
                    setattr(obj, prop, self._replace_str_with_params(
                        val, param_dict))
                elif isinstance(val, Substitution):
                    setattr(obj, prop, param_dict[val.__str__()])
                else:
                    self._replace_properties_with_params(val, param_dict)
        except TypeError:
            pass  # Item is not an object

    def _replace_str_with_params(self, string, param_dict):
        """
        Find any parameter template strings in string and replace them with
        them with the corresponding parameter values from param_dict.
        """
        for parameter_name, value in param_dict.items():
            string = string.replace(parameter_name, str(value))
        return string


class Substitution(object):
    ENV_VAR_PREFIX = "PARAM_"

    def __init__(self, parameter_name):
        self.parameter_name = parameter_name
        self.dictParams = {}

    @classmethod
    def convert_name(cls, parameter_name):
        return cls.ENV_VAR_PREFIX + parameter_name

    def __getitem__(self, key):
        """Allows dict params to be accessed through bracket syntax.
        """
        return self.dictParams[key]

    def __str__(self):
        return Substitution.convert_name(self.parameter_name)
