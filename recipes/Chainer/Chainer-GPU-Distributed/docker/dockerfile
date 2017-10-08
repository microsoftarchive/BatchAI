FROM nvidia/cuda:8.0-cudnn6-devel-ubuntu14.04
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
    gfortran && \

    rm -rf /var/lib/apt/lists/* && \


    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    /bin/bash /Miniconda3-latest-Linux-x86_64.sh -f -b -p $CONDA_DIR && \
    rm Miniconda3-latest-Linux-x86_64.sh


#########################MPI###########################
RUN cd /tmp && \
        wget "https://www.open-mpi.org/software/ompi/v2.1/downloads/openmpi-2.1.1.tar.gz" && \
        tar xzf openmpi-2.1.1.tar.gz && \
        cd openmpi-2.1.1  && \
        ./configure --with-cuda && make -j"$(nproc)" install # && ldconfig



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

    conda install Pillow scikit-learn notebook pandas matplotlib mkl nose pyyaml six h5py && \


    pip install mpi4py && \
    pip install cython && \

    pip install chainer && \
    pip install chainercv && \
    pip install chainermn && \

    conda clean -yt

ENV PYTHONPATH $CONDA_DIR/lib/python3.5/site-packages/:$PYTHONPATH

######################################################

ENV PYTHONPATH /src/:$PYTHONPATH