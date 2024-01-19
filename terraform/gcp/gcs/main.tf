#-------------------------------
# プロバイダー設定
#-------------------------------
provider "google" {
  project = "${var.project_id}"
  region  = "${var.region}"
}

#-------------------------------
# GCS パケット
#-------------------------------
# tfstate ファイルを保存する GCS パケット
resource "google_storage_bucket" "terraform-tf-states" {
  name          = "glossary-llm-chat-bot-tf-states-${var.project_id}"
  location      = "ASIA"
  versioning {
    enabled = true
  }
}
