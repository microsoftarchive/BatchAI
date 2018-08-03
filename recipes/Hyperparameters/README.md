# Hyperparameter Tuning

The goal of [hyperparameter tuning](https://en.wikipedia.org/wiki/Hyperparameter_(machine_learning)) is to find the optimized parameters that are used as input constants for each training job, such as learning rate and network model definitions. Hyperparameter Tuning can be treated as an upper layer of the actual learning problems which may require much more computational resources.

We provide a collection of helper classes/functions in [job_factory.py](../../utilities/job_factory.py) and [experiment.py](../../utilities/experiment.py) to submit/monitor hyperparameter jobs. Please refer to the [README.md](../../utilities/README.md#job-factory) for detail.

#### [Random-Search](./Random-Search)
This Random-Search recipe contains information on how to implement the basic random search based hyperparameter tuning using BatchAI.

#### [HyperBand](./HyperBand)
This recipe contains an example on how to implement the basic [hyperband](https://people.eecs.berkeley.edu/~kjamieson/hyperband.html) hyperparameter tuning algorithm using BatchAI.

## Help or Feedback
--------------------
If you have any problems or questions, you can reach the Batch AI team at [AzureBatchAITrainingPreview@service.microsoft.com](mailto:AzureBatchAITrainingPreview@service.microsoft.com) or you can create an issue on GitHub.

We also welcome your contributions of additional sample notebooks, scripts, or other examples of working with Batch AI.
