FROM library/ubuntu:20.04
MAINTAINER Kojima <kojima.ryosuke.8e@kyoto-u.ac.jp>
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN apt update -y && \
    apt upgrade -y && \
    apt install -y wget bzip2 curl git

ENV CONDA_ROOT /root/miniconda
ENV PATH /root/miniconda/bin:$PATH
SHELL ["/bin/bash", "-c"]

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    bash ~/miniconda.sh -b -p $CONDA_ROOT && \
    ln -s ${CONDA_ROOT}/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". ${CONDA_ROOT}/etc/profile.d/conda.sh" >> ~/.bashrc

RUN apt install -y libfontconfig1 libxrender1  build-essential sox
RUN conda install scikit-learn joblib pandas -y
RUN conda install -c conda-forge librosa -y
RUN conda install flask seaborn -y
RUN conda install -c conda-forge flask-restx flask-cors -y
RUN conda install -c conda-forge umap-learn -y
RUN pip install trimap pillow

RUN pip install git+https://github.com/kojima-r/HARK_TF_Parser.git
RUN pip install git+https://github.com/kojima-r/MicArrayX.git
RUN git clone https://github.com/kojima-r/AudioSimpleAPI.git

WORKDIR /AudioSimpleAPI

ENTRYPOINT ["python", "app.py"]
