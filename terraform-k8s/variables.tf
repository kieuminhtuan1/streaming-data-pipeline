variable "finnhub_api_token" {
  description = "API token for Finnhub"
  type        = string
}

variable "cassandra_user" {
  description = "Username for Cassandra"
  type        = string
}

variable "cassandra_password" {
  description = "Password for Cassandra"
  type        = string
}

variable "kube_config" {
  type    = string
  default = "~/.kube/config"
}

variable "namespace" {
  type    = string
  default = "pipeline"
}

variable "finnhub_stocks_tickers" {
  type    = list
  default = [ "BINANCE:BTCUSDT",
              "BINANCE:ETHUSDT",
              "BINANCE:XRPUSDT",
              "BINANCE:DOGEUSDT" ]
}