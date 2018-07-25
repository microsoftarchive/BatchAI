FROM nvidia/cuda:8.0-cudnn6-devel-ubuntu16.04
RUN apt-get update

# disable interactive functions
ENV DEBIAN_FRONTEND noninteractive

#################Install MiniConda and other dependencies##########
ENV CONDA_DIR /opt/conda
ENV PATH $CONDA_DIR/bin:$PATH
ENV OPENBLAS_NUM_THREADS $(nproc)

RUN mkdir -p $CONDA_DIR && \
    echo export PATH=$CONDA_DIR/bin:'$PATH' > /etc/profile.d/conda.sh && \

    apt-get update -y && \
    apt-get install -y \

    wget \
    vim \
    git \
    g++ \
    graphviz \

    software-properties-common \
    python-software-properties \
    python3-dev \

    libhdf5-dev \
    libopenblas-dev \
    liblapack-dev \
    libblas-dev \
    gfortran \
    cpio \
    libmlx4-1 \
    libmlx5-1 \
    librdmacm1 \
    libibverbs1 \
    libmthca1 \
    libdapl2 \
    dapl2-utils && \

    rm -rf /var/lib/apt/lists/* && \


    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    /bin/bash /Miniconda3-latest-Linux-x86_64.sh -f -b -p $CONDA_DIR && \
    rm Miniconda3-latest-Linux-x86_64.sh


######################### INTEL MPI ###########################
RUN cd /tmp && \
    wget -q 'http://registrationcenter-download.intel.com/akdlm/irc_nas/tec/11595/l_mpi_2017.3.196.tgz'  && \
    tar zxvf l_mpi_2017.3.196.tgz && \
    sed -i -e 's/^ACCEPT_EULA=decline/ACCEPT_EULA=accept/g' /tmp/l_mpi_2017.3.196/silent.cfg && \
    sed -i -e 's|^#ACTIVATION_LICENSE_FILE=|ACTIVATION_LICENSE_FILE=/tmp/l_mpi_2017.3.196/USE_SERVER.lic|g' /tmp/l_mpi_2017.3.196/silent.cfg && \
    sed -i -e 's/^ACTIVATION_TYPE=exist_lic/ACTIVATION_TYPE=license_server/g' /tmp/l_mpi_2017.3.196/silent.cfg  && \
    cd /tmp/l_mpi_2017.3.196  && \
    ./install.sh -s silent.cfg && \
    echo "source /opt/intel/compilers_and_libraries_2017.4.196/linux/mpi/intel64/bin/mpivars.sh" >> ~/.bashrc


#######################NCCL###########################
ENV CPATH /usr/local/cuda/include:/usr/local/include:$CPATH
RUN cd /usr/local && git clone https://github.com/NVIDIA/nccl.git && cd nccl && \

######### Compile for devices with cuda compute compatibility 3 (e.g. GRID K520 on aws)
# UNCOMMENT line below to compile for GPUs with cuda compute compatibility 3.0
#        sed -i '/NVCC_GENCODE ?=/a \                -gencode=arch=compute_30,code=sm_30 \\' Makefile && \
##########

        make CUDA_HOME=/usr/local/cuda -j"$(nproc)" && \
        make install && ldconfig


####################Python 3#########################
ARG python_version=3.5.2
RUN conda install -y python=${python_version} && \
    pip install -U pip && \
    . /opt/intel/compilers_and_libraries_2017.4.196/linux/mpi/intel64/bin/mpivars.sh && \

    conda install Pillow scikit-learn notebook pandas matplotlib mkl nose pyyaml six h5py && \

    pip install cupy && \
    pip install mpi4py && \
    pip install cython && \

    pip install chainer && \
    pip install chainercv && \
    pip install chainermn && \

    conda clean -yt

ENV PYTHONPATH $CONDA_DIR/lib/python3.5/site-packages/:$PYTHONPATH

######################################################

ENV PYTHONPATH /src/:$PYTHONPATH

################# remove Intel components #####################

RUN rm -rf /opt/intel