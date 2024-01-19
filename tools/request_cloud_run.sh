#!/bin/sh
set -eu
PROJECT_ID=${PROJECT_ID:-"dummy"}
REGION=${REGION:-"asia-northeast1"}
CLOUD_RUN_NAME=${CLOUD_RUN_NAME:-"glossary-llm-chat-bot"}
SLACK_VERIFY_TOKEN=${SLACK_VERIFY_TOKEN:-"dummy"}

# API URL 取得
API_URL=$( gcloud run services describe ${CLOUD_RUN_NAME} --region ${REGION} --format 'value(status.url)' )
echo "API_URL: ${API_URL}"

# call api
curl -X GET ${API_URL}/health | jq .

curl -X PUT "${API_URL}/update_db" | jq .

curl -X POST \
    -d text="hogehogeについて教えて" -d token="${SLACK_VERIFY_TOKEN}" \
    "${API_URL}/chat" | jq .
