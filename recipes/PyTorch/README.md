# PyTorch

PyTorch is a python-based package that provides two high-level features: 1) Tensor computation (like NumPy) with strong GPU acceleration; 2) Deep neural networks built on a tape-based autograd system.

For multi-node distributed training, PyTorch currenly supports three communication backends: Gloo, TCP and MPI. Please find the [tutorial](http://pytorch.org/docs/master/distributed.html) for detail on PyTorch distributed communication package.

See official PyTorch GitHub page (https://github.com/pytorch/pytorch). 

#### [PyTorch-GPU-Distributed-Gloo](./PyTorch-GPU-Distributed-Gloo)
This PyTorch-GPU-Distributed-Gloo recipe contains information on how to run distributed PyTorch training job across multiple GPU nodes with BatchAI using Gloo backend.

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
