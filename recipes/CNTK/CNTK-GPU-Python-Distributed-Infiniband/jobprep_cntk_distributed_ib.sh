#!/usr/bin/bash

# Download the CIFAR-10 dataset from Azure Blob
if [ ! -z $AZ_BATCHAI_JOB_TEMP ];then
    cd $AZ_BATCHAI_JOB_TEMP
    wget 'https://batchaisamples.blob.core.windows.net/samples/CIFAR-10_dataset.tar?st=2017-09-29T18%3A29%3A00Z&se=2099-12-31T08%3A00%3A00Z&sp=rl&sv=2016-05-31&sr=b&sig=nFXsAp0Eq%2BoS5%2BKAEPnfyEGlCkBcKIadDvCPA%2BcX6lU%3D' -k -O 'CIFAR-10_dataset.tar'
    echo "untar CIFAR-10 dataset........."
    tar -xf CIFAR-10_dataset.tar
    echo "done"
    ROOT_DIR=`pwd`
    files=( "train_map.txt" "test_map.txt" )
    for file in "${files[@]}"
    do
        output=$ROOT_DIR"/"$file
        if [ -f $output ];then
            rm $output
        fi
        touch $output
        while read -r line
        do
            name="$line"
            echo "$ROOT_DIR$name" >> $output
        done < $file".template"
    done
fi

# install intel MPI
cd /tmp
wget -q 'http://registrationcenter-download.intel.com/akdlm/irc_nas/tec/11595/l_mpi_2017.3.196.tgz' 
tar zxvf l_mpi_2017.3.196.tgz
sed -i -e 's/^ACCEPT_EULA=decline/ACCEPT_EULA=accept/g' /tmp/l_mpi_2017.3.196/silent.cfg
sed -i -e 's|^#ACTIVATION_LICENSE_FILE=|ACTIVATION_LICENSE_FILE=/tmp/l_mpi_2017.3.196/USE_SERVER.lic|g' /tmp/l_mpi_2017.3.196/silent.cfg
sed -i -e 's/^ACTIVATION_TYPE=exist_lic/ACTIVATION_TYPE=license_server/g' /tmp/l_mpi_2017.3.196/silent.cfg 
cd /tmp/l_mpi_2017.3.196 
./install.sh -s silent.cfg
cd .. 
rm -rf l_mpi_2017.3.196* 
echo "source /opt/intel/compilers_and_libraries_2017.4.196/linux/mpi/intel64/bin/mpivars.sh" >> ~/.bashrc
