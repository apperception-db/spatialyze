FROM mambaorg/micromamba:jammy-cuda-12.1.1

WORKDIR /workspace
USER root

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update --yes --quiet
RUN apt-get install --yes --quiet --no-install-recommends \
    curl ffmpeg git

RUN sed -i 's/#force_color_prompt/force_color_prompt/g' $HOME/.bashrc
RUN git clone --recurse-submodules --depth 1 https://github.com/chanwutk/.config.git $HOME/.config
RUN echo "source $HOME/.config/rc" >> $HOME/.bashrc
RUN cat <(echo "source $HOME/.config/profile") $HOME/.profile > $HOME/.profile.tmp
RUN mv $HOME/.profile.tmp $HOME/.profile


# configre python to output directly to terminal
# see: https://stackoverflow.com/questions/59812009/what-is-the-use-of-pythonunbuffered-in-docker-file
ENV PYTHONUNBUFFERED=1

RUN micromamba install --yes --name base python=3.10 poetry=1.7 --channel conda-forge
RUN micromamba clean --all --yes
ARG MAMBA_DOCKERFILE_ACTIVATE=1

ENV POETRY_VIRTUALENVS_CREATE=false
# COPY pyproject.toml poetry.lock* ./
# RUN poetry install --no-root

# ARG PINECONE_API
# ENV PINECONE_API=$PINECONE_API
ENV PYDEVD_DISABLE_FILE_VALIDATION=1