# PyTorch-GPU-Distributed-Gloo

This example demonstrates how to run distributed GPU training for PyTorch using Gloo backend in Batch AI

## Details

- The Gloo backend will be implemented using Batch AI shared job temporary directory which is visible for all GPU nodes in the job
- Will use Batch AI generated AZ_BATCHAI_PYTORCH_INIT_METHOD for shared file-system initialization.
- Will use Batch AI generated AZ_BATCHAI_TASK_INDEX as rank of each worker process
- Standard output of the job will be stored on Azure File Share.
- PyTorch training script [mnist_trainer.py](./mnist_trainer.py) is attached, which trains a CNN for MNIST dataset.

**Note** Due to a known bug in PyTorch Gloo backend, the job may fail with the following error as [reported](https://github.com/pytorch/pytorch/issues/2530):

```
terminate called after throwing an instance of 'gloo::EnforceNotMet'
  what():  [enforce fail at /pytorch/torch/lib/gloo/gloo/cuda.cu:249] error == cudaSuccess. 29 vs 0. Error at: /pytorch/torch/lib/gloo/gloo/cuda.cu:249: driver shutting down
```


## Instructions to Run Recipe

### Python Jupyter Notebook

You can find Jupyter Notebook for this sample in [PyTorch-GPU-Distributed-Gloo.ipynb](./PyTorch-GPU-Distributed-Gloo.ipynb).

### Azure CLI 2.0

Under Construction...

## License Notice

Under construction...

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
