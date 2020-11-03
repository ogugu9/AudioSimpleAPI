FROM library/ubuntu:20.04
MAINTAINER Kojima <kojima.ryosuke.8e@kyoto-u.ac.jp>
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN apt update -y && \
    apt upgrade -y && \
    apt install -y wget bzip2 curl git

ENV CONDA_ROOT /root/miniconda
ENV PATH /root/miniconda/bin:$PATH
SHELL ["/bin/bash", "-c"]
RUN git clone https://github.com/kojima-r/AudioSimpleAPI.git

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    bash ~/miniconda.sh -b -p $CONDA_ROOT && \
    ln -s ${CONDA_ROOT}/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". ${CONDA_ROOT}/etc/profile.d/conda.sh" >> ~/.bashrc 

RUN apt install -y libfontconfig1 libxrender1
RUN conda install scikit-learn joblib pandas
RUN conda install -c conda-forge librosa
RUN conda install flask
RUN conda install -c conda-forge flask-restx
WORKDIR /AudioSimpleAPI

ENTRYPOINT ["python", "app.py"]
