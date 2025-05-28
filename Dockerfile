FROM pytorch/pytorch:2.7.0-cuda12.6-cudnn9-devel

ENV DEBIAN_FRONTEND=noninteractive \
    HOST=docker \
    LANG=C.UTF-8 LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    MPLLOCALFREETYPE=1 \
    # https://serverfault.com/questions/683605/docker-container-time-timezone-will-not-reflect-changes
    TZ=America/New_York

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG DEPENDENCIES="  \
    ca-certificates \
    curl \
    build-essential \
    espeak-ng \
    libsndfile1-dev \
    libasound-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    git"

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -ex && \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' >/etc/apt/apt.conf.d/keep-cache && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ${DEPENDENCIES} && \
    echo "no" | dpkg-reconfigure dash

# WORKDIR "/root"

# # Install uv and configure deps
# ADD https://astral.sh/uv/install.sh /uv-installer.sh
# RUN sh /uv-installer.sh && \
#     rm /uv-installer.sh

# ENV PATH="/root/.local/bin/:$PATH"

WORKDIR "/app"

COPY pyproject.toml uv.lock app.py requirements.txt ./

# RUN uv sync --locked

RUN python -m pip install --upgrade pip wheel setuptools && \
    pip install -r requirements.txt

ENTRYPOINT ["fastapi", "run", "app.py"]
