FROM python:3.11.5-bookworm AS base

# install basic libs
ENV DEBIAN_FRONTEND noninteractive

RUN set -x && apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    sudo \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip

# define ARG and ENV
ARG WORKDIR="/app"
ENV WORKDIR=${WORKDIR}

ARG LOG_LEVEL="INFO"
ENV LOG_LEVEL=${LOG_LEVEL}

ARG PROJECT_ID="dummy"
ENV PROJECT_ID=${PROJECT_ID}

ARG REGION="dummy"
ENV REGION=${REGION}

ARG GOOGLE_APPLICATION_CREDENTIALS="dummy"
ENV GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}

ARG PORT="3000"
ENV PORT=${PORT}

ARG SPREADSHEET_KEY="dummy"
ENV SPREADSHEET_KEY=${SPREADSHEET_KEY}

ARG SPREADSHEET_NAME="dummy"
ENV SPREADSHEET_NAME=${SPREADSHEET_NAME}

ARG OPENAI_API_KEY="dummy"
ENV OPENAI_API_KEY=${OPENAI_API_KEY}

ARG SERPAPI_API_KEY="dummy"
ENV SERPAPI_API_KEY=${SERPAPI_API_KEY}

ARG SLACK_BOT_TOKEN="dummy"
ENV SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}

ARG SLACK_SIGNING_SECRET="dummy"
ENV SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}

ARG SLACK_VERIFY_TOKEN="dummy"
ENV SLACK_VERIFY_TOKEN=${SLACK_VERIFY_TOKEN}

ARG DATASET_TEXT_COLUMNS="dummy"
ENV DATASET_TEXT_COLUMNS=${DATASET_TEXT_COLUMNS}

ARG DATASET_META_COLUMNS="dummy"
ENV DATASET_META_COLUMNS=${DATASET_META_COLUMNS}

ENV LC_ALL=C.UTF-8
ENV export LANG=C.UTF-8
ENV PYTHONIOENCODING utf-8

# install dependences
WORKDIR ${WORKDIR}
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# write src
COPY . ${WORKDIR}

# set workdir
WORKDIR ${WORKDIR}

# run api
EXPOSE 3000 8080
CMD /bin/bash -c "python3 app.py"

#-------------------
# for prod env
#-------------------
FROM base as prod

#-------------------
# for dev env
#-------------------
FROM base as dev

# install docker
ENV DOCKER_CLIENT_VERSION=latest
ENV DOCKER_API_VERSION=1.39
RUN curl -fsSL https://get.docker.com/builds/Linux/x86_64/docker-${DOCKER_CLIENT_VERSION}.tgz | tar -xzC /usr/local/bin --strip=1 docker/docker

# install gcloud
RUN curl https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz > /tmp/google-cloud-sdk.tar.gz
RUN mkdir -p /usr/local/gcloud \
  && tar -C /usr/local/gcloud -xvf /tmp/google-cloud-sdk.tar.gz \
  && /usr/local/gcloud/google-cloud-sdk/install.sh

ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin

# Install terraform
ARG terraform_version="1.2.3"
RUN wget https://releases.hashicorp.com/terraform/${terraform_version}/terraform_${terraform_version}_linux_amd64.zip \
    && unzip ./terraform_${terraform_version}_linux_amd64.zip -d /usr/local/bin/ \
    && rm -rf ./terraform_${terraform_version}_linux_amd64.zip
