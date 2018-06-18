FROM nvidia/cuda:9.0-cudnn7-devel-ubuntu16.04

RUN apt-get update && \
	apt-get install -y --no-install-recommends build-essential  \
	cmake\ 
	git\ 
	curl\ 
	vim\ 
	ca-certificates\ 
	libjpeg-dev\ 
	libpng-dev && \
	rm -rf /var/lib/apt/lists/*

ENV PYTHON_VERSION=3.6

RUN curl -o ~/miniconda.sh -O  https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh  && \    
	chmod +x ~/miniconda.sh && \     
	~/miniconda.sh -b -p /opt/conda && \      
	rm ~/miniconda.sh && \    
	/opt/conda/bin/conda create -y --name pytorch-py$PYTHON_VERSION python=$PYTHON_VERSION numpy pyyaml scipy ipython mkl && \      
	/opt/conda/bin/conda clean -ya

ENV PATH=/opt/conda/bin:$PATH

RUN pip install http://download.pytorch.org/whl/cu90/torch-0.4.0-cp36-cp36m-linux_x86_64.whl && \   
	pip install torchvision