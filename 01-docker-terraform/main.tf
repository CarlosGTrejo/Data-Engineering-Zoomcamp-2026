terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.16.0"
    }
  }
}

provider "google" {
  project                            = "de-zoomcamp-484419"
  region                             = "us-central1"
  impersonate_service_account        = var.impersonate_service_account
  impersonate_service_account_delegates = var.impersonate_service_account_delegates
}

variable "impersonate_service_account" {
  description = "Service account email to impersonate (needs roles/iam.serviceAccountTokenCreator on itself)."
  type        = string
}

variable "impersonate_service_account_delegates" {
  description = "Optional delegate chain for impersonation."
  type        = list(string)
  default     = []
}

resource "google_storage_bucket" "demo-bucket" {
  name          = "de-zoomcamp-484419-demo-bucket"
  location      = "US"
  force_destroy = true
  uniform_bucket_level_access = true 

  lifecycle_rule {
    condition {
      age = 3
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}