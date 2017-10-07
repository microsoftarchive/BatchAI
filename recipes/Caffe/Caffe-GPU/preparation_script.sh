#!/usr/bin/bash

sed 's,$AZ_BATCHAI_OUTPUT_MODEL,'$AZ_BATCHAI_OUTPUT_MODEL',g; s,$AZ_BATCHAI_INPUT_SAMPLE,'$AZ_BATCHAI_INPUT_SAMPLE',g' $AZ_BATCHAI_INPUT_SAMPLE/lenet_solver.prototxt.template > $AZ_BATCHAI_INPUT_SAMPLE/lenet_solver.prototxt
sed 's,$AZ_BATCHAI_INPUT_SAMPLE,'$AZ_BATCHAI_INPUT_SAMPLE',g' $AZ_BATCHAI_INPUT_SAMPLE/lenet_train_test.prototxt.template > $AZ_BATCHAI_INPUT_SAMPLE/lenet_train_test.prototxt
