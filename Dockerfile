FROM python:3.10-slim

# Set up proxy to access Internet if necessary
#ENV http_proxy ""
#ENV https_proxy ""

RUN apt-get update && apt-get install -y git

RUN apt-get install -y gcc g++ linux-perf

RUN pip install --upgrade pip

COPY . /Coffe

RUN cd /Coffe && pip install .

# Note: `coffe init` is intentionally NOT run here. It calls Collector() to
# verify perf_event_open works, which needs the seccomp profile applied at
# `docker run` time — not available during `docker build`. Init is run on
# the host instead (see README step 3).