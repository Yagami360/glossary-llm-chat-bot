#!/bin/sh
set -eu
PROJECT_DIR=$(cd $(dirname $0)/..; pwd)

PROJECT_ID=${PROJECT_ID:-"dummy"}
REGION=${REGION:-"asia-northeast1"}

IMAGE_NAME=${IMAGE_NAME:-"glossary-llm-chat-bot"}
IMAGE_NAME_DEV=${IMAGE_NAME_DEV:-"glossary-llm-chat-bot-dev"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}

CLOUD_RUN_NAME=${CLOUD_RUN_NAME:-"glossary-llm-chat-bot"}
PORT=${PORT:-3000}

cd ${PROJECT_DIR}
gcloud config --quiet set project ${PROJECT_ID}
gcloud auth login

# 各種 GCP API 有効化
gcloud services enable \
    drive.googleapis.com \
    sheets.googleapis.com \
    containerregistry.googleapis.com \
    run.googleapis.com \
    cloudresourcemanager.googleapis.com \
    cloudscheduler.googleapis.com

#-----------------------------
# GCS パケットを作成する
#-----------------------------
cd ${PROJECT_DIR}/terraform/gcp/gcs

terraform init -backend-config="bucket=glossary-llm-chat-bot-tf-states-${PROJECT_ID}"
terraform plan -var "project_id=${PROJECT_ID}" -var "region=${REGION}"
terraform apply -auto-approve -var "project_id=${PROJECT_ID}" -var "region=${REGION}"
terraform show

#-----------------------------
# docker image を GCR に push
#-----------------------------
# cd ${PROJECT_DIR}

# # docker image を作成
# make docker-build-prod

# # docker image を GCR にアップロード
# docker tag ${IMAGE_NAME} gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}
# docker push gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}

#-----------------------------
# Cloud Run を作成する
#-----------------------------
cd ${PROJECT_DIR}/terraform/gcp/cloud_run

terraform init -backend-config="bucket=glossary-llm-chat-bot-tf-states-${PROJECT_ID}"
terraform plan -var "project_id=${PROJECT_ID}" -var "region=${REGION}" -var "port=${PORT}"
terraform apply -auto-approve -var "project_id=${PROJECT_ID}" -var "region=${REGION}" -var "port=${PORT}"
terraform show

#-----------------------------
# Cloud Scheduler を作成する
#-----------------------------
cd ${PROJECT_DIR}/terraform/gcp/cloud_scheduler
API_URL=$( gcloud run services describe ${CLOUD_RUN_NAME} --region ${REGION} --format 'value(status.url)' )

terraform init -backend-config="bucket=glossary-llm-chat-bot-tf-states-${PROJECT_ID}"
terraform plan -var "project_id=${PROJECT_ID}" -var "region=${REGION}" -var "api_url=${API_URL}"
terraform apply -auto-approve -var "project_id=${PROJECT_ID}" -var "region=${REGION}" -var "api_url=${API_URL}"
terraform show
