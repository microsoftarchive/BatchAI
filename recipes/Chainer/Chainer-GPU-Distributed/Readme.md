# Chainer GPU Distributed

This example demonstrates how to run standard Chainer [train_mnist.py](https://github.com/chainer/chainer/blob/master/examples/mnist/train_mnist.py) example using Batch AI.

## Details

- batchaitraining/chainer:distributed docker image is used;
- Standard chainer sample script [train_mnist.py](https://github.com/chainer/chainer/blob/master/examples/mnist/train_mnist.py) is used;
- Chainer downloads the standard MNIST Database on its own;
- Standard output of the job and the model will be stored on Azure File Share;

## Instructions to Run Recipe

### Python Jupyter Notebook

You can find Jupyter Notebook for this recipe in [Chainer-GPU-Distributed.ipynb](./Chainer-GPU-Distributed.ipynb).

### Azure CLI 2.0

You can find Azure CLI 2.0 instructions for this recipe in [cli-instructions.md](./cli-instructions.md).

## Dockerfile

The `Dockerfile` for the Docker images used in this recipe can be found [here](./docker/dockerfile). The dockerfile is a modified version of ChainerMN example at https://github.com/chainer/chainermn/pull/71

## License Notice

Under construction...

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
