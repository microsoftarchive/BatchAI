# TensorFlow Distributed GPU

## Introduction

This example demonstrate how to run standard TensorFlow sample (https://github.com/tensorflow/tensorflow/blob/master/tensorflow/tools/dist_test/python/mnist_replica.py) on Azure Batch AI cluster of 2 nodes.

## Details

- For demonstration purposes, MNIST dataset and `mnist_replica.py` will be deployed at Azure File Share;
- Standard output of the job and the model will be stored on Azure File Share;
- MNIST dataset (http://yann.lecun.com/exdb/mnist/) is archived and uploaded into the [blob](https://batchaisamples.blob.core.windows.net/samples/mnist_dataset_original.zip?st=2017-09-29T18%3A29%3A00Z&se=2099-12-31T08%3A00%3A00Z&sp=rl&sv=2016-05-31&sr=b&sig=Qc1RA3zsXIP4oeioXutkL1PXIrHJO0pHJlppS2rID3I%3D).
- The recipe uses official `mnist_replica.py` (https://github.com/tensorflow/tensorflow/blob/master/tensorflow/tools/dist_test/python/mnist_replica.py).

## Instructions to Run Recipe

### Python Jupyter Notebook

You can find Jupyter Notebook for this recipe in [TensorFlow-GPU-Distributed.ipynb](./TensorFlow-GPU-Distributed.ipynb).

### Azure CLI 2.0

You can find Azure CLI 2.0 instructions for this recipe in [cli-instructions.md](./cli-instructions.md).

## License Notice

Under construction...

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
