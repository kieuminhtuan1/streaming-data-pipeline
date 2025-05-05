FROM python:3.9-slim AS python_builder

WORKDIR /app
# Tạo file requirements.txt
RUN echo "pyspark==3.0.0" > requirements.txt && \
    echo "pyhocon==0.3.59" >> requirements.txt && \
    echo "cassandra-driver==3.25.0" >> requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

FROM kubeflow/spark-operator:latest

# Cài đặt các thư viện Python
USER root
COPY --from=python_builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=python_builder /usr/local/bin /usr/local/bin

# Tạo thư mục làm việc
WORKDIR /opt/spark/work-dir

# Copy mã nguồn Python
# Copy mã nguồn Python
COPY src/pyspark/*.py /opt/spark/work-dir/
COPY src/resources/schema/ /opt/spark/work-dir/schemas/
COPY src/resources/application.conf /opt/spark/work-dir/conf/
COPY src/resources/deployment.conf /opt/spark/work-dir/conf/

# Thiết lập biến môi trường
ENV PYTHONPATH="${PYTHONPATH}:/opt/spark/work-dir"
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Tải các JAR cần thiết
WORKDIR /opt/spark/jars
RUN wget -q https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.0.0/spark-sql-kafka-0-10_2.12-3.0.0.jar && \
    wget -q https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.12/3.0.0/spark-avro_2.12-3.0.0.jar && \
    wget -q https://repo1.maven.org/maven2/com/datastax/spark/spark-cassandra-connector_2.12/3.0.0/spark-cassandra-connector_2.12-3.0.0.jar

# Trở lại thư mục làm việc
WORKDIR /opt/spark/work-dir