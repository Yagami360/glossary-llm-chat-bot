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

#-----------------------------
# Cloud Scheduler を削除する
#-----------------------------
cd ${PROJECT_DIR}/terraform/gcp/cloud_scheduler
API_URL=$( gcloud run services describe ${CLOUD_RUN_NAME} --region ${REGION} --format 'value(status.url)' )

terraform init -backend-config="bucket=glossary-llm-chat-bot-tf-states-${PROJECT_ID}"
terraform plan -destroy -var "project_id=${PROJECT_ID}" -var "region=${REGION}" -var "api_url=${API_URL}"
terraform destroy -auto-approve -var "project_id=${PROJECT_ID}" -var "region=${REGION}" -var "api_url=${API_URL}"
terraform show

#-----------------------------
# Cloud Run を削除する
#-----------------------------
cd ${PROJECT_DIR}/terraform/gcp/cloud_run

terraform init -backend-config="bucket=glossary-llm-chat-bot-tf-states-${PROJECT_ID}"
terraform plan -destroy -var "project_id=${PROJECT_ID}" -var "region=${REGION}" -var "port=${PORT}"
terraform destroy -auto-approve -var "project_id=${PROJECT_ID}" -var "region=${REGION}" -var "port=${PORT}"
terraform show
