# syntax=docker/dockerfile:experimental

FROM centos:centos7.9.2009

# NOTE(crag): NB_USER ARG for mybinder.org compat:
#             https://mybinder.readthedocs.io/en/latest/tutorials/dockerfile.html
ARG NB_USER=notebook-user
ARG NB_UID=1000
ARG PIP_VERSION

RUN yum -y update && \
  yum -y install gcc openssl-devel bzip2-devel libffi-devel make git sqlite-devel && \
  curl -O https://www.python.org/ftp/python/3.8.15/Python-3.8.15.tgz && tar -xzf Python-3.8.15.tgz && \
  cd Python-3.8.15/ && ./configure --enable-optimizations && make altinstall && \
  cd .. && rm -rf Python-3.8.15* && \
  ln -s /usr/local/bin/python3.8 /usr/local/bin/python3

# create user with a home directory
ENV USER ${NB_USER}
ENV HOME /home/${NB_USER}

RUN groupadd --gid ${NB_UID} ${NB_USER}
RUN useradd --uid ${NB_UID}  --gid ${NB_UID} ${NB_USER}
USER ${NB_USER}
WORKDIR ${HOME}
ENV PYTHONPATH="${PYTHONPATH}:${HOME}"
ENV PATH="/home/${NB_USER}/.local/bin:${PATH}"

COPY logger_config.yaml logger_config.yaml
COPY requirements/dev.txt requirements-dev.txt
COPY requirements/base.txt requirements-base.txt
COPY prepline_receipts prepline_receipts
COPY exploration-notebooks exploration-notebooks
COPY pipeline-notebooks pipeline-notebooks

# NOTE(crag) - Cannot use an ARG in the dst= path (so it seems), hence no ${NB_USER}, ${NB_UID}
RUN python3.8 -m pip install pip==${PIP_VERSION} \
  && pip3.8 install --no-cache -r requirements-base.txt \
  && pip3.8 install --no-cache -r requirements-dev.txt

#EXPOSE 5000

#ENTRYPOINT ["uvicorn", "prepline_receipts.api.receipts:app", \
#  "--log-config", "logger_config.yaml", \
#  "--host", "0.0.0.0", \
#  "--port", "5000"]
