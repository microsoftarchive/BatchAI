# Horovod

This recipe shows how to run [Horovod](https://github.com/uber/horovod) distributed training framework for PyTorch using Batch AI.


## Details

- Standard Horovod [pytorch_mnist.py](https://raw.githubusercontent.com/uber/horovod/master/examples/pytorch_mnist.py) example will be used;
- pytorch_mnist.py downloads training data on its own during execution;
- The job will be run on standard tensorflow container batchaitraining/pytorch:0.4.0-cp36-cuda9-cudnn7;
- Horovod framework will be installed in the container using job preparation command line. Note, you can build your own docker image containing tensorflow and horovod instead.
- Standard output of the job will be stored on Azure File Share.

## Instructions to Run Recipe

### Python Jupyter Notebook

You can find Jupyter Notebook for this recipe in [Horovod-PyTorch.ipynb](./Horovod-PyTorch.ipynb).

### Azure CLI 2.0

You can find Azure CLI 2.0 instructions for this recipe in [cli-instructions.md](./cli-instructions.md).

## License Notice

Under construction...

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
