#!/bin/sh
set -eu
PROJECT_ID=${PROJECT_ID:-"dummy"}
SERVICE_ACCOUNT_NAME=${SERVICE_ACCOUNT_NAME:-"glossary-llm-chat-bot-sa"}
PROJECT_DIR=$(cd $(dirname $0)/..; pwd)
JSON_KEY_DIR="${PROJECT_DIR}/credentials"

cd ${PROJECT_DIR}

gcloud config --quiet set project ${PROJECT_ID}
gcloud auth login

# サービスアカウントを作成する
if [ ! "$(gcloud iam service-accounts list | grep ${SERVICE_ACCOUNT_NAME})" ] ; then
    gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME}
fi

# サービスアカウントに必要な権限を付与する
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/storage.admin"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/run.admin"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/run.invoker"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/cloudscheduler.admin"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/iam.serviceAccountTokenCreator"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/iam.serviceAccountUser"

# サービスアカウントの秘密鍵 (json) を生成する
mkdir -p ${JSON_KEY_DIR}
gcloud iam service-accounts keys create ${JSON_KEY_DIR}/${SERVICE_ACCOUNT_NAME}.json --iam-account=${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
