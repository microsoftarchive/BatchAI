from __future__ import print_function

import os
import zipfile

import requests


def download_file(sas, destination):
    dir_name = os.path.dirname(destination)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    print('Downloading {0} ...'.format(sas), end='')
    r = requests.get(sas, stream=True)
    with open(destination, 'wb') as f:
        for chunk in r.iter_content(chunk_size=512 * 1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    f.close()
    print('Done')


def download_and_upload_mnist_dataset_to_blob(blob_service, azure_blob_container_name,
                                              mnist_dataset_directory):
    """
    Download and Extract MNIST Dataset, then upload to given Azure Blob Container
    """
    mnist_dataset_url = 'https://batchaisamples.blob.core.windows.net/samples/mnist_dataset_full.zip?st=2018-03-04T00%3A21%3A00Z&se=2099-12-31T23%3A59%3A00Z&sp=rl&sv=2017-04-17&sr=b&sig=rrBgTFeIv3bjsyAfh87RoW5i0ay4mMyMEIh2RI45s%2B0%3D'

    mnist_files = ['t10k-images-idx3-ubyte.gz', 't10k-labels-idx1-ubyte.gz',
                   'train-images-idx3-ubyte.gz', 'train-labels-idx1-ubyte.gz',
                   'Train-28x28_cntk_text.txt', 'Test-28x28_cntk_text.txt',
                   os.path.join('mnist_train_lmdb', 'data.mdb'),
                   os.path.join('mnist_test_lmdb', 'data.mdb'),
                   os.path.join('mnist_train_lmdb', 'lock.mdb'),
                   os.path.join('mnist_test_lmdb', 'lock.mdb')]

    local_dir = 'mnist_dataset_full'

    if any(not os.path.exists(os.path.join(local_dir, f)) for f in mnist_files):
        download_file(mnist_dataset_url, 'mnist_dataset_full.zip')
        print('Extracting MNIST dataset...')
        with zipfile.ZipFile('mnist_dataset_full.zip', 'r') as z:
            z.extractall(local_dir)

    print('Uploading MNIST dataset...')
    for f in mnist_files:
        blob_service.create_blob_from_path(azure_blob_container_name,
                                           mnist_dataset_directory + '/' + f, os.path.join(local_dir, f))

    print('Done')


def download_and_upload_rnn_dataset_to_blob(blob_service,
                                            azure_blob_container_name,
                                            rnn_dataset_directory):
    rnn_dataset_url = 'https://teststoragewewa.blob.core.windows.net/batchaisample/rnn_dataset.zip?sp=r&st=2018-07-03T22:28:27Z&se=2030-07-04T06:28:27Z&spr=https&sv=2017-11-09&sig=laKwEnBycdm87ssmbr3HKnLJNEQVGoR3NONRMehZ8sk%3D&sr=b'
    local_dir = 'rnn_dataset'
    rnn_files = ['linux_input.txt',
                 'shakespeare_input.txt',
                 'war_and_peace_input.txt']

    if any(not os.path.exists(os.path.join(local_dir, f)) for f in rnn_files):
        download_file(rnn_dataset_url, 'rnn_dataset.zip')
        print('Extracting RNN dataset...')
        with zipfile.ZipFile('rnn_dataset.zip', 'r') as z:
            z.extractall(local_dir)

    print("Uploading RNN dataset")
    for f in rnn_files:
        blob_service.create_blob_from_path(azure_blob_container_name,
                                           rnn_dataset_directory + '/' + f,
                                           os.path.join(local_dir, f))

    print("Done")
