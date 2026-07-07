FROM python:3.10-slim

WORKDIR /app

ENV GDAL_CACHEMAX=75%
ENV GDAL_DISABLE_READDIR_ON_OPEN=TRUE
ENV GDAL_HTTP_MERGE_CONSECUTIVE_RANGES=YES
ENV GDAL_HTTP_MULTIPLEX=YES
ENV GDAL_INGESTED_BYTES_AT_OPEN=32768
ENV GDAL_HTTP_VERSION=2
ENV CPL_VSIL_CURL_ALLOWED_EXTENSIONS=tif,tiff,vrt,cog
ENV VSI_CACHE=TRUE


COPY pyproject.toml poetry.lock /app/
COPY ./ctod /app/ctod/
COPY ./scripts /app/scripts/
COPY ./config /app/config/
COPY start_server.py /app/

RUN apt-get update \
    && apt-get install -y gcc libexpat1 libgdal36 libgeos-dev libproj-dev \
        libglm-dev libxml2-dev libxslt1-dev cmake \
    && pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-root \
    && pip install --no-cache-dir "numpy<2" \
    && apt-get remove -y gcc cmake \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 5000

ENTRYPOINT ["python", "start_server.py"]