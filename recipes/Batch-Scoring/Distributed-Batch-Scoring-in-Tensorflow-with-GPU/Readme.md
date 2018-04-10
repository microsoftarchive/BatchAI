# Batch Scoring

## Introduction

This example demonstrate how to run standard TensorFlow sample (https://github.com/tensorflow/tensorflow/blob/master/tensorflow/tools/dist_test/python/mnist_replica.py) on Azure Batch AI cluster of 2 nodes.

## Details

- For demonstration purposes, pretained [Inception-V3](https://arxiv.org/abs/1512.00567) model and approxinately 900 evaluation images from [ImageNet](http://image-net.org/) dataset will be deployed to Azure Blob Container
- Standard output of the job will be stored on Azure File Share;
- Azure Blob Container and Azure File Share will be mounted on Batch AI GPU clusters 
- The recipe uses [batch_image_label.py](./batch_image_label.py) script to perform Distributed Batch Scoring with the given model and image datasets. The input images for evaluation will be partitioned by the MPI rank, so that each MPI worker will evaluate part of the whole image set independently. 

## Instructions to Run Recipe

### Python Jupyter Notebook

You can find Jupyter Notebook for this recipe in [Distributed-Batch-Scoring-Tensorflow.ipynb](./Distributed-Batch-Scoring-Tensorflow.ipynb).

## License Notice

Under construction...

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
