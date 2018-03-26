# Copyright (c) Microsoft. All rights reserved.

# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

from __future__ import print_function
import numpy as np
import sys
import os
import cntk
import argparse


# Merge stdout and stderr
sys.stdout = sys.stderr


# Define the reader for both training and evaluation action.
def create_reader(path, is_training, input_dim, label_dim):
    return cntk.io.MinibatchSource(cntk.io.CTFDeserializer(path, cntk.io.StreamDefs(
        features=cntk.io.StreamDef(field='features', shape=input_dim),
        labels=cntk.io.StreamDef(field='labels', shape=label_dim)
    )), randomize=is_training, max_sweeps=cntk.io.INFINITELY_REPEAT if is_training else 1)


# Creates and trains a feedforward classification model for MNIST images
def convnet_mnist(data_path, model_path, max_epochs = 40, model_suffix=None, hidden_layers_dim=96, feedforward_const=0.0039, log_dir=None, tensorboard_logdir=None, debug_output=False):
    image_height = 28
    image_width = 28
    num_channels = 1
    input_dim = image_height * image_width * num_channels
    num_output_classes = 10

    # Input variables denoting the features and label data
    input_var = cntk.ops.input((num_channels, image_height, image_width), np.float32)
    label_var = cntk.ops.input(num_output_classes, np.float32)

    # Instantiate the feedforward classification model
    scaled_input = cntk.ops.element_times(cntk.ops.constant(feedforward_const), input_var)

    with cntk.layers.default_options(activation=cntk.ops.relu, pad=False):
        conv1 = cntk.layers.Convolution2D((5, 5), 32, pad=True)(scaled_input)
        pool1 = cntk.layers.MaxPooling((3, 3), (2, 2))(conv1)
        conv2 = cntk.layers.Convolution2D((3, 3), 48)(pool1)
        pool2 = cntk.layers.MaxPooling((3, 3), (2, 2))(conv2)
        conv3 = cntk.layers.Convolution2D((3, 3), 64)(pool2)
        f4 = cntk.layers.Dense(hidden_layers_dim)(conv3)
        drop4 = cntk.layers.Dropout(0.5)(f4)
        z = cntk.layers.Dense(num_output_classes, activation=None)(drop4)

    ce = cntk.losses.cross_entropy_with_softmax(z, label_var)
    pe = cntk.metrics.classification_error(z, label_var)

    reader_train = create_reader(os.path.join(data_path, 'Train-28x28_cntk_text.txt'), True, input_dim,
                                 num_output_classes)
    # training config
    epoch_size = 60000  # for now we manually specify epoch size
    minibatch_size = 64

    # Set learning parameters
    lr_per_sample = [0.001] * 10 + [0.0005] * 10 + [0.0001]
    lr_schedule = cntk.learning_rate_schedule(lr_per_sample, cntk.learners.UnitType.sample, epoch_size)
    mm_time_constant = [0] * 5 + [1024]
    mm_schedule = cntk.learners.momentum_as_time_constant_schedule(mm_time_constant, epoch_size)

    # Instantiate the trainer object to drive the model training
    learner = cntk.learners.momentum_sgd(z.parameters, lr_schedule, mm_schedule)
    progress_writers = [cntk.logging.ProgressPrinter(
        # freq=training_progress_output_freq,
        tag='Training',
        log_to_file=log_dir,
        num_epochs=max_epochs)]

    if tensorboard_logdir is not None:
        progress_writers.append(cntk.logging.TensorBoardProgressWriter(freq=10, log_dir=tensorboard_logdir, model=z))

    trainer = cntk.Trainer(z, (ce, pe), learner, progress_writers)

    model_name = "MNIST_Model"
    if model_suffix is not None:
        model_name += ("_" + model_suffix)

    # define mapping from reader streams to network inputs
    input_map = {
        input_var: reader_train.streams.features,
        label_var: reader_train.streams.labels
    }

    cntk.training_session(
        trainer=trainer,
        mb_source=reader_train,
        mb_size=minibatch_size,
        model_inputs_to_streams=input_map,
        max_samples=epoch_size * max_epochs,
        checkpoint_config=cntk.CheckpointConfig(frequency = epoch_size,
                                           filename = os.path.join(model_path, model_name),
                                           restore = True),
        progress_frequency=epoch_size
    ).train()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-datadir', '--datadir', help='Data directory where the MNIST dataset is located', required=True)
    parser.add_argument('-outputdir', '--outputdir', help='Output directory for checkpoints and models', required=False, default=None)
    parser.add_argument('-model_suffix', '--model_suffix', help='Suffix of the model name', required=False, default=None)
    parser.add_argument('-n', '--epochs', help='Total number of epochs to train', type=int, required=False, default='5')
    parser.add_argument('-logdir', '--logdir', help='Log file', required=False, default=None)
    parser.add_argument('-tensorboard_logdir', '--tensorboard_logdir',
                        help='Directory where TensorBoard logs should be created', required=False, default=None)
    parser.add_argument('-d', '--hidden_layers_dim', help='hidden layers dimension', type=int, required=False, default='200')
    parser.add_argument('-f', '--feedforward_const', help='feedforward constant', type=float, required=False, default='0.00390625')

    args = vars(parser.parse_args())
    data_dir = args['datadir']
    model_path = args['outputdir']
    if args['logdir'] is not None:
        log_dir = args['logdir'] + "/progress.log"


    convnet_mnist(
        data_path=data_dir,
        model_path=model_path,
        max_epochs=args['epochs'],
        model_suffix=args['model_suffix'],
        hidden_layers_dim=args['hidden_layers_dim'],
        feedforward_const=args['feedforward_const'],
        log_dir=log_dir,
        tensorboard_logdir=args['tensorboard_logdir']
    )

