# Chainer GPU Distributed Infiniband

This example demonstrates how to run standard ChainerMN [train_mnist.py](https://raw.githubusercontent.com/chainer/chainermn/v1.3.0/examples/mnist/train_mnist.py) distributed training job using Batch AI with Infiniband enabled.

## Details

- Standard chainer sample script [train_mnist.py](https://github.com/chainer/chainermn/blob/master/examples/mnist/train_mnist.py) is used;
- Chainer downloads the standard MNIST Database on its own and distributed across workers;
- Standard output of the job and the model will be stored on Azure File Share.
- IntelMPI (non-CUDA-aware) will be used to launch ChainerMN jobs cross nodes

## Instructions to Run Recipe

### Python Jupyter Notebook

You can find Jupyter Notebook for this recipe in [Chainer-GPU-Distributed-Infiniband.ipynb](./Chainer-GPU-Distributed-Infiniband.ipynb).

### Azure CLI 2.0

You can find Azure CLI 2.0 instructions for this recipe in [cli-instructions.md](./cli-instructions.md).

## Dockerfile

The `Dockerfile` for the Docker images used in this recipe can be found [here](./dockerfile). The dockerfile is a modified version of ChainerMN [example](https://github.com/chainer/chainermn/pull/71) built based on IntelMPI library.

## License Notice

Under construction...

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
