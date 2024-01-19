#-------------------------------
# プロバイダー設定
#-------------------------------
provider "google" {
  project = "${var.project_id}"
  region  = "${var.region}"
}

provider "google-beta" {
  project = "${var.project_id}"
  region  = "${var.region}"
}

#-------------------------------
# 実行する Terraform 環境情報
#-------------------------------
terraform {
  backend "gcs" {
    bucket = "glossary-llm-chat-bot-tf-states"
    prefix = "gcp/cloud_scheduler"
  }
  required_providers {
    google = {
      version = "3.89"
    }
  }
}

#-------------------------------
# Cloud Scheduler
#-------------------------------
resource "google_cloud_scheduler_job" "glossary-llm-chat-bot" {
  name     = "glossary-llm-chat-bot"

  schedule = "0 * * * *"
  time_zone = "Asia/Tokyo"

  http_target {
    uri = "${var.api_url}/update_db"
    http_method = "PUT"
  }
}
