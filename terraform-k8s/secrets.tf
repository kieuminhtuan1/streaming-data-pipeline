resource "kubernetes_secret" "pipeline-secrets" {
  metadata {
    name      = "pipeline-secrets"
    namespace = "${var.namespace}"
  }

  depends_on = [
        "kubernetes_namespace.pipeline-namespace"
  ]

  data = {
    #IMPORTANT! while specifying custom password for Cassandra - remember to add password into grafana/dashboards/dashboard.json
    #file if you want to use custom one (or something else). https://community.grafana.com/t/dashboard-provisioning-with-variables/45516/9
    FINNHUB_API_TOKEN  = var.finnhub_api_token
    CASSANDRA_USER     = var.cassandra_user
    CASSANDRA_PASSWORD = var.cassandra_password
  }

  type = "opaque"
}