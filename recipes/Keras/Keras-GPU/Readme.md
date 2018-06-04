# Keras GPU

This recipe shows how to run Keras using Batch AI. Keras supports tensorflow, cntk and theano backends. Currently only tensorflow and cntk backends supports running on GPU. Batch AI will automatic setup backend when toolkit is specified.

## Details

- Keras can run with CNTK or Tensorflow backend.
- Standard keras sample script [mnist_cnn.py](https://raw.githubusercontent.com/fchollet/keras/master/examples/mnist_cnn.py) is used;
- The script downloads the standard MNIST Database on its own;
- Standard output of the job will be stored on Azure File Share.

## Instructions to Run Recipe

### Python Jupyter Notebook

You can find Jupyter Notebook for this recipe in [Keras-GPU.ipynb](./Keras-GPU.ipynb).

### Azure CLI 2.0

You can find Azure CLI 2.0 instructions for this recipe in [cli-instructions.md](./cli-instructions.md).

## License Notice

Under construction...

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
