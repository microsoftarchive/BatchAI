# Python CNTK GPU

This example uses the CIFAR-10 dataset to demonstrate how to train a convolutional neural network (CNN) on a multi-node multi-GPU cluster. You can run this recipe on a single or multiple nodes.

## Details

- For demonstration purposes, CIFAR-10 data preparation script and ConvNet_CIFAR10_DataAug_Distributed.py with its dependency will be deployed at Azure File Share;
- Standard output of the job and the model will be stored on Azure File Share;
- CIFAR-10 dataset(http://www.cs.toronto.edu/~kriz/cifar.html) has been preprocessed available [here](https://batchaisamples.blob.core.windows.net/samples/CIFAR-10_dataset.tar?st=2017-09-29T18%3A29%3A00Z&se=2099-12-31T08%3A00%3A00Z&sp=rl&sv=2016-05-31&sr=b&sig=nFXsAp0Eq%2BoS5%2BKAEPnfyEGlCkBcKIadDvCPA%2BcX6lU%3D).
- The official CNTK example ConvNet_CIFAR10_DataAug_Distributed.py (https://github.com/Microsoft/CNTK/blob/master/Examples/Image/Classification/ConvNet/Python/ConvNet_CIFAR10_DataAug_Distributed.py) is used. 


## Instructions to Run Recipe

### Python Jupyter Notebook

You can find Jupyter Notebook for this recipe in [CNTK-GPU-Python-Distrbuted.ipynb](./CNTK-GPU-Python-Distrbuted.ipynb).

### Azure CLI 2.0

You can find Azure CLI 2.0 instructions for this recipe in [cli-instructions.md](./cli-instructions.md).

## License Notice

Under construction...

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
