# Random Search CNTK GPU

This example shows how to perform random search hyperparameter tuning using CNTK with MNIST dataset to train a convolutional neural network (CNN) on a GPU cluster. 

## Details

- We provide a CNTK example [ConvMNIST.py](../ConvMNIST.py) to accept  command line arguments for CNTK dataset, model locations, model file suffix and two hyperparameters for tuning: 1. hidden layer dimension and 2. feedforward constant 
- For demonstration purposes, MNIST dataset and CNTK training script will be deployed at Azure File Share;
- Standard output of the job and the model will be stored on Azure File Share;
- MNIST dataset (http://yann.lecun.com/exdb/mnist/) has been preprocessed by usign install_mnist.py available [here](https://batchaisamples.blob.core.windows.net/samples/mnist_dataset.zip?st=2017-09-29T18%3A29%3A00Z&se=2099-12-31T08%3A00%3A00Z&sp=rl&sv=2016-05-31&sr=c&sig=PmhL%2BYnYAyNTZr1DM2JySvrI12e%2F4wZNIwCtf7TRI%2BM%3D).

## Instructions to Run Recipe

### Jupyter Notebook

You can find Jupyter Notebook for this recipe in [CNTK-GPU-Python.ipynb](./CNTK-GPU-Python.ipynb).

## License Notice

Under construction...

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
