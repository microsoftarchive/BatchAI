# Caffe2 GPU Distributed

This example demonstrates how to run standard Caffe2 resnet50_trainer.py example using Batch AI. You can run it on a single or multiple compute nodes.

## Details

- Standard Caffe2 sample script [resnet50_trainer.py](https://github.com/caffe2/caffe2/blob/master/caffe2/python/examples/resnet50_trainer.py) is used;
- MNIST Dataset has been translated into a lmdb database, and can be obtained at http://download.caffe2.ai/databases/mnist-lmdb.zip;
- NFS will be used for rendezvous temp files to coordinate between each shard/node 
- Standard output of the job will be stored on Azure File Share.


## Instructions to Run Recipe

### Python Jupyter Notebook

You can find Jupyter Notebook for this sample in [Caffe2-GPU-Distributed.ipynb](./Caffe2-GPU-Distributed.ipynb).

### Azure CLI 2.0

Under Construction...

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
