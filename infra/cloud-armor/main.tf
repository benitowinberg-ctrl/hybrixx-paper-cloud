# HYBRIXX – STAGED FIREWALL POLICY. NOT DEPLOYED.
# Requires a billed Google Cloud project and a separately configured private
# backend service behind an external Application Load Balancer. The policy
# does nothing until explicitly attached to THAT backend service.
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0"
    }
  }
}

variable "project_id" {
  description = "Existing Google Cloud project, configured by the owner"
  type        = string
}

variable "policy_name" {
  description = "WAF policy name for future private HYBRIXX admin backend"
  type        = string
  default     = "hybrixx-admin-waf"
}

provider "google" {
  project = var.project_id
}

resource "google_compute_security_policy" "hybrixx_admin" {
  name        = var.policy_name
  project     = var.project_id
  description = "HYBRIXX future private backend protection; not for GitHub Pages"
  type        = "CLOUD_ARMOR"

  # Start WAF signatures in preview. Evaluate false positives in Cloud Logging
  # before changing preview to false. Never assume preview blocks traffic.
  rule {
    action      = "deny(403)"
    priority    = 1000
    description = "SQL injection inspection: monitor first"
    preview     = true
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('sqli-v422-stable', {'sensitivity': 1})"
      }
    }
  }

  rule {
    action      = "deny(403)"
    priority    = 1010
    description = "Cross-site scripting inspection: monitor first"
    preview     = true
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('xss-v422-stable', {'sensitivity': 1})"
      }
    }
  }

  rule {
    action      = "deny(403)"
    priority    = 1020
    description = "Remote code execution inspection: monitor first"
    preview     = true
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('rce-v422-stable', {'sensitivity': 1})"
      }
    }
  }

  rule {
    action      = "deny(403)"
    priority    = 1030
    description = "File inclusion inspection: monitor first"
    preview     = true
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('lfi-v422-stable', {'sensitivity': 1})"
      }
    }
  }

  rule {
    action      = "throttle"
    priority    = 2000
    description = "Per-IP request throttling after identity gateway"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 60
        interval_sec = 60
      }
    }
  }

  # Never use Cloud Armor as a substitute for login. Any remaining request is
  # ALLOWED AT THE FIREWALL; private backend must separately enforce IAM/IAP.
  rule {
    action      = "allow"
    priority    = 2147483647
    description = "Default; authenticated backend still mandatory"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
  }
}

output "firewall_policy_id" {
  description = "Must be attached to the intended load-balancer backend service"
  value       = google_compute_security_policy.hybrixx_admin.id
}
