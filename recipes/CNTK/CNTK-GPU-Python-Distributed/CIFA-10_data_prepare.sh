#!/usr/bin/bash
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
