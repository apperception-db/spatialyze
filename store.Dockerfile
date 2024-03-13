FROM postgis/postgis:16-3.4

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update --yes --quiet
RUN apt-get install --yes --quiet --no-install-recommends \
    python3

RUN rm -rf /pg-extender
COPY ./scripts/pg-extender /pg-extender
RUN cd /pg-extender && python3 install.py