# Caffe GPU

This example demonstrates how to run standard Caffe lenet_solver.prototxt example using Batch AI. This recipe is running on a signle .

## Details

- For demonstration purposes, MNIST dataset and caffe configuration file will be deployed at Azure File Share;
- Standard output of the job and the model will be stored on Azure File Share;
- MNIST dataset has been preprocessed according to http://caffe.berkeleyvision.org/gathered/examples/mnist.html available [here](https://batchaisamples.blob.core.windows.net/samples/mnist_lmdb.zip?st=2017-10-06T00%3A15%3A00Z&se=2100-01-01T00%3A00%3A00Z&sp=rl&sv=2016-05-31&sr=b&sig=jKlQA8x190lLGDXloeHrSe6jpOtUEYLD1DRoyWuiAdQ%3D).
- The original Caffe solver and net prototxt files have been modified to take environment variables: AZ_BATCHAI_INPUT_SAMPLE and AZ_BATCHAI_OUTPUT_MODEL, and available here lenet_solver.prototxt and lenet_train_test.prototxt. 
- Since prototxt files supports neither command line overloading nor environment variable, we use job preparation task preparation_script.sh to expand the environment varible specified in the files, providing more flexibility of the job setup.


## Instructions to Run Recipe

### Python Jupyter Notebook

You can find Jupyter Notebook for this sample in [Caffe-GPU.ipynb](./Caffe-GPU.ipynb).

### Azure CLI 2.0

Under Construction...

## License Notice

Under construction...

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
