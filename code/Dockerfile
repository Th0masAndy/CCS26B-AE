FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /home

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    openssl \
    build-essential \
    cmake \
    git \
    libtool \
    autoconf \
    automake \
    pkg-config \
    iproute2 \
    python3 \
    sudo \
    nasm \
    libssl-dev \
    libgmp-dev \
    wget \
    time \
    libfmt-dev \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY . /home/FPSI

RUN cd /home/FPSI && \
    chmod +x scripts/build/*.sh scripts/reproduction/*.sh \
        scripts/reproduction/*.py scripts/data/*.py && \
    FPSI_SKIP_SYSTEM_PACKAGES=1 ./scripts/build/run.sh

WORKDIR /home/FPSI

CMD ["bash", "-c", "./scripts/reproduction/run.sh --quick && exec bash"]
