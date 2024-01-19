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
    prefix = "gcp/cloud_run"
  }
  required_providers {
    google = {
      version = "3.89"
    }
  }
}

#-------------------------------
# Cloud Run
#-------------------------------
resource "google_cloud_run_service" "glossary-llm-chat-bot" {
  name     = "glossary-llm-chat-bot"
  location = "${var.region}"

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/glossary-llm-chat-bot"
        ports {
          container_port = "${var.port}"
        }
      }
    }
    metadata {
      annotations = {
        "run.googleapis.com/startup-cpu-boost" = true
        "run.googleapis.com/cpu-throttling"    = false
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

# gcloud beta run deploy の --allow-unauthenticated 引数相当の設定
resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.glossary-llm-chat-bot.location
  project     = google_cloud_run_service.glossary-llm-chat-bot.project
  service     = google_cloud_run_service.glossary-llm-chat-bot.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
