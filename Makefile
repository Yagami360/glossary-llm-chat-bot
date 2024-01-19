IMAGE_NAME=glossary-llm-chat-bot
IMAGE_NAME_DEV=glossary-llm-chat-bot-dev


.PHONY: docker-build-dev
docker-build-dev:
	docker build -f Dockerfile -t ${IMAGE_NAME_DEV} \
		--target dev \
		--build-arg LOG_LEVEL="INFO" \
		--build-arg PROJECT_ID=${PROJECT_ID} \
		--build-arg REGION=${REGION} \
		--build-arg GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS} \
		--build-arg PORT=3000 \
		--build-arg SPREADSHEET_KEY=${SPREADSHEET_KEY} \
		--build-arg SPREADSHEET_NAME=${SPREADSHEET_NAME} \
		--build-arg OPENAI_API_KEY=${OPENAI_API_KEY} \
		--build-arg SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN} \
		--build-arg SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET} \
		--build-arg SLACK_VERIFY_TOKEN=${SLACK_VERIFY_TOKEN} \
		--build-arg DATASET_TEXT_COLUMNS=${DATASET_TEXT_COLUMNS} \
		--build-arg DATASET_META_COLUMNS=${DATASET_META_COLUMNS} \
		.


.PHONY: docker-build-prod
docker-build-prod:
	docker build -f Dockerfile -t ${IMAGE_NAME} \
		--target prod \
		--build-arg LOG_LEVEL="INFO" \
		--build-arg PROJECT_ID=${PROJECT_ID} \
		--build-arg REGION=${REGION} \
		--build-arg GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS} \
		--build-arg PORT=3000 \
		--build-arg SPREADSHEET_KEY=${SPREADSHEET_KEY} \
		--build-arg SPREADSHEET_NAME=${SPREADSHEET_NAME} \
		--build-arg OPENAI_API_KEY=${OPENAI_API_KEY} \
		--build-arg SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN} \
		--build-arg SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET} \
		--build-arg SLACK_VERIFY_TOKEN=${SLACK_VERIFY_TOKEN} \
		--build-arg DATASET_TEXT_COLUMNS=${DATASET_TEXT_COLUMNS} \
		--build-arg DATASET_META_COLUMNS=${DATASET_META_COLUMNS} \
		.


.PHONY: docker-push
docker-push:
	docker run -it --rm -v ${PWD}:/app --name ${IMAGE_NAME_DEV} ${IMAGE_NAME_DEV} /bin/sh -c "\
		gcloud config --quiet set project ${PROJECT_ID} && \
		gcloud auth login && \
		gcloud services enable containerregistry.googleapis.com"
	docker tag ${IMAGE_NAME} gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest
	docker push gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest


.PHONY: create-sa
create-sa:
	docker run -it --rm -v ${PWD}:/app --name ${IMAGE_NAME_DEV} ${IMAGE_NAME_DEV} /bin/sh -c "bash tools/make_service_account.sh"


.PHONY: deploy
deploy:
	docker run -it --rm -v ${PWD}:/app --name ${IMAGE_NAME_DEV} ${IMAGE_NAME_DEV} /bin/sh -c "bash tools/deploy.sh"


.PHONY: get-api-url
get-api-url:
	docker run -it --rm -v ${PWD}:/app --name ${IMAGE_NAME_DEV} ${IMAGE_NAME_DEV} /bin/sh -c "\
		gcloud config --quiet set project ${PROJECT_ID} && \
		gcloud auth login && \
		gcloud run services describe glossary-llm-chat-bot --region ${REGION} --format 'value(status.url)'"


.PHONY: lint
lint:
	flake8 .


.PHONY: check-fmt
check-fmt:
	isort -rc -m 3 --check-only .


.PHONY: fmt
fmt:
	isort -rc -sl .
	isort -rc -m 3 .
