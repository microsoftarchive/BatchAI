# Batch Scoring

Batch Scoring refers to a scenario to make predictions/classifications of a unlabeled dataset using a pretrained network model in a Batch. For example, classifying millions of new images will be a common and challenging tasks for e-commerce providers.  

Similar to a distributed training scenario, it is also possible to exploit GPU and distributed computing resource to speed up the batch Scoring performance. The underlying idea would be to split and assign the whole unlabeled dataset to each workers in the cluster, and each worker can perform classification in parallel and independently.


#### [Distributed-Batch-Scoring-in-Tensorflow-with GPU](./Distributed-Batch-Scoring-in-Tensorflow-with-GPU)
This example demonstrate how to run distributed batch scoring job in TensorFlow on Azure Batch AI cluster. [Inception-V3](https://arxiv.org/abs/1512.00567) model and unlabeled images from [ImageNet](http://image-net.org/) dataset will be used.

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.