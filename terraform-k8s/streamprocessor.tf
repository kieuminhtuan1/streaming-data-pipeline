resource "kubectl_manifest" "streamprocessor" {
  depends_on = [
      "kubernetes_deployment.kafka_service",
      "kubernetes_deployment.cassandra"
  ]
  yaml_body = <<YAML
apiVersion: "sparkoperator.k8s.io/v1beta2"
kind: SparkApplication
metadata:
  name: streamprocessor
  namespace: ${var.namespace}
spec:
  type: Python                      
  pythonVersion: "3"                 
  mode: cluster
  imagePullPolicy: Never
  image: docker.io/library/streamdataproject-spark-k8s:latest 
  mainApplicationFile: "local:///opt/spark/work-dir/StreamProcessor.py"  
  sparkVersion: "3.0.0"
  restartPolicy:
    type: OnFailure
    onFailureRetries: 3
    onFailureRetryInterval: 10
    onSubmissionFailureRetries: 3
    onSubmissionFailureRetryInterval: 10
  volumes:
    - name: spark-volume
      hostPath:
        path: /host
  driver:
    cores: 2
    memory: "1g"
    serviceAccount: spark
    volumeMounts:
      - name: spark-volume
        mountPath: /host
    env:
      - name: PYTHONPATH
        value: "/opt/spark/work-dir"  
      - name: PYSPARK_PYTHON
        value: "python3"              
      - name: PYSPARK_DRIVER_PYTHON
        value: "python3"              
    envFrom:
    - configMapRef:
        name: pipeline-config
    - secretRef:
        name: pipeline-secrets
  executor:
    cores: 2
    instances: 1
    memory: "2g"
    volumeMounts:
      - name: spark-volume
        mountPath: /host
    env:
      - name: PYTHONPATH
        value: "/opt/spark/work-dir"  
      - name: PYSPARK_PYTHON
        value: "python3"             
    envFrom:
    - configMapRef:
        name: pipeline-config
    - secretRef:
        name: pipeline-secrets
  deps:                           
    jars:
      - "local:///opt/spark/jars/spark-sql-kafka-0-10_2.12-3.0.0.jar"
      - "local:///opt/spark/jars/spark-avro_2.12-3.0.0.jar"
      - "local:///opt/spark/jars/spark-cassandra-connector_2.12-3.0.0.jar"
YAML
}