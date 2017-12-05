# Horovod-Infiniband-Benchmark

This recipe shows how to reproduce [Horovod distributed training benchmarks](https://github.com/uber/horovod/blob/master/docs/benchmarks.md) using Azure Batch AI.

Currently Batch AI has no native support for Horovod framework, but it's easy to run it using Batch AI custom toolkit.


## Details

- Official Horovod Benchmark [scripts](https://github.com/alsrgv/benchmarks/tree/master/scripts/tf_cnn_benchmarks) will be used;
- The job will be run on standard tensorflow container ```tensorflow/tensorflow:1.4.0-gpu```;
- Horovod framework and IntelMPI will be installed in the container using job preparation command line. Note, you can build your own docker image containing tensorflow and horovod instead.
- Benchmark scripts will be downloaded to GPU nodes using job preparation command line as well, stored in `$AZ_BATCHAI_JOB_TEMP` at each node
- This sample needs to use at lesat two `STANDARD_NC24r` nodes, please be sure you have enough quota
- Standard output of the job will be stored on Azure File Share.
- This recipe ONLY reproduce the training results with synthetic data on NVIDIA K80 GPUs. 


## Instructions to Run Recipe

### Python Jupyter Notebook

You can find Jupyter Notebook for this recipe in [Horovod-Infiniband-Benchmark.ipynb](./Horovod-Infiniband-benchmark.ipynb).

### Azure CLI 2.0

You can find Azure CLI 2.0 instructions for this recipe in [cli-instructions.md](./cli-instructions.md).

## License Notice

Under construction...

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
