FROM python:latest

COPY . /sources

RUN pip install /sources \
    && rm -rf /sources

ENTRYPOINT [ "report-generator" ]