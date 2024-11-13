ARG PIXI_VERSION=0.34.0

FROM ubuntu:24.04 AS builder
# need to specify the ARG again to make it available in this stage
ARG PIXI_VERSION
RUN apt-get update && apt-get install -y curl
# download the musl build since the gnu build is not available on aarch64
RUN curl -Ls \
    "https://github.com/prefix-dev/pixi/releases/download/v${PIXI_VERSION}/pixi-$(uname -m)-unknown-linux-musl" \
    -o /pixi && chmod +x /pixi
RUN /pixi --version

FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    NVIDIA_VISIBLE_DEVICES=all \
    HF_HOME=/.hf-cache

SHELL ["/bin/bash", "-c"]

# https://github.com/prefix-dev/pixi-docker/blob/main/Dockerfile
COPY --from=builder --chown=root:root --chmod=0555 /pixi /usr/local/bin/pixi

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y curl git build-essential espeak-ng libsndfile1-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR "/root"

COPY pixi.toml pixi.lock app.py .

RUN pixi install

ENTRYPOINT ["pixi", "run", "start-prod"]
