#!/bin/sh
set -eu
PROJECT_DIR=$(cd $(dirname $0)/..; pwd)
PROJECT_ID=${PROJECT_ID:-"dummy"}
REGION=${REGION:-"asia-northeast1"}
SERVICE_ACCOUNT_NAME=${SERVICE_ACCOUNT_NAME:-"glossary-llm-chat-bot-sa"}

SPREADSHEET_KEY=${SPREADSHEET_KEY:-"dummy"}
SPREADSHEET_NAME=${SPREADSHEET_NAME:-"dummy"}
OPENAI_API_KEY=${OPENAI_API_KEY:-"dummy"}
SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN:-"dummy"}
SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET:-"dummy"}
SLACK_VERIFY_TOKEN=${SLACK_VERIFY_TOKEN:-"dummy"}

DATASET_TEXT_COLUMNS=${DATASET_TEXT_COLUMNS:-"dummy"}
DATASET_META_COLUMNS=${DATASET_META_COLUMNS:-"dummy"}

cd ${PROJECT_DIR}

# install act
act --version &> /dev/null
if [ $? -ne 0 ] ; then
    wget -qO act.tar.gz https://github.com/nektos/act/releases/latest/download/act_Linux_x86_64.tar.gz
    sudo tar xf act.tar.gz -C /usr/local/bin act
fi
echo "act version : `act --version`"

# run ci/cd for dev release on local env with act
GCP_SA_KEY=$( base64 credentials/${SERVICE_ACCOUNT_NAME}.json )
act pull_request -e tools/pull_request.json \
    -s PROJECT_ID=${PROJECT_ID} \
    -s REGION=${REGION} \
    -s GCP_SA_KEY="${GCP_SA_KEY}" \
    -s SPREADSHEET_KEY="${SPREADSHEET_KEY}" \
    -s SPREADSHEET_NAME="${SPREADSHEET_NAME}" \
    -s OPENAI_API_KEY="${OPENAI_API_KEY}" \
    -s SLACK_BOT_TOKEN="${SLACK_BOT_TOKEN}" \
    -s SLACK_SIGNING_SECRET="${SLACK_SIGNING_SECRET}" \
    -s SLACK_VERIFY_TOKEN="${SLACK_VERIFY_TOKEN}" \
    -s DATASET_TEXT_COLUMNS="${DATASET_TEXT_COLUMNS}" \
    -s DATASET_META_COLUMNS="${DATASET_META_COLUMNS}"

