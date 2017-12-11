# Distrbuted CNTK with GPU and Infiniband 

This example uses the CIFAR-10 dataset to demonstrate how to train a Residual network (ResNet) on a multi-node multi-GPU cluster with infiniband. 

## Details

- The official CNTK ResNet for CIFAR10 [example](https://github.com/Microsoft/CNTK/tree/master/Examples/Image/Classification/ResNet/Python) is used.
- CIFAR-10 dataset(http://www.cs.toronto.edu/~kriz/cifar.html) has been preprocessed available at the [Azure storage](https://batchaisamples.blob.core.windows.net/samples/CIFAR-10_dataset.tar?st=2017-09-29T18%3A29%3A00Z&se=2099-12-31T08%3A00%3A00Z&sp=rl&sv=2016-05-31&sr=b&sig=nFXsAp0Eq%2BoS5%2BKAEPnfyEGlCkBcKIadDvCPA%2BcX6lU%3D), and will be downloaded to GPU local SSD. 
- The job will be run on a prebuild CNTK container ```batchaitraining/cntk:2.1-gpu-1bitsgd-py36-cuda8-cudnn6-intelmpi``` based on [dockerfile](./dockerfile). Intel MPI package will be installed in the container using job preparation command line.
- For demonstration purposes, CIFAR-10 data preparation script and CNTK job scripts will be deployed at Azure File Share.
- Standard output of the job and the model will be stored on Azure File Share.
- This sample needs to use at lesat two STANDARD_NC24r nodes, please be sure you have enough quota
- If you like to conduct performance comparasion with TCP network, you can create the cluster with VM size `STANDARD_NC24` that does not support Infiniband.

## Instructions to Run Recipe

### Python Jupyter Notebook

You can find Jupyter Notebook for this recipe in [CNTK-GPU-Python-Distrbuted-Infiniband.ipynb](./CNTK-GPU-Python-Distrbuted-Infiniband.ipynb).

### Azure CLI 2.0

You can find Azure CLI 2.0 instructions for this recipe in [cli-instructions.md](./cli-instructions.md).

## License Notice

Under construction...

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
