from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, explode, current_timestamp, udf, avg
from pyspark.sql.avro.functions import from_avro
from pyspark.sql.types import *
import uuid
import time
import pkg_resources
from pyhocon import ConfigFactory

from Settings import Settings

def main():
    # Loading configuration
    conf = ConfigFactory.load()
    settings = Settings(conf)
    
    # Loading trades schema
    trades_schema_path = pkg_resources.resource_filename(__name__, settings.schemas["trades"])
    with open(trades_schema_path, "r") as schema_file:
        trades_schema = schema_file.read()
    
    # UDF for Cassandra UUIDs
    def generate_uuid():
        # Simulating time-based UUID similar to Cassandra's Uuids.timeBased()
        return str(uuid.uuid1())
    
    make_uuid = udf(generate_uuid, StringType())
    
    # Create Spark session
    spark = (SparkSession
        .builder
        .master(settings.spark["master"])
        .appName(settings.spark["appName"])
        .config("spark.cassandra.connection.host", settings.cassandra["host"])
        .config("spark.cassandra.auth.username", settings.cassandra["username"])
        .config("spark.cassandra.auth.password", settings.cassandra["password"])
        .config("spark.sql.shuffle.partitions", settings.spark["shuffle_partitions"])
        .getOrCreate())
    
    # Proper processing code below
    
    # Read streams from Kafka
    input_df = (spark
        .readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", settings.kafka["server_address"])
        .option("subscribe", settings.kafka["topic_market"])
        .option("minPartitions", settings.kafka["min_partitions"])
        .option("maxOffsetsPerTrigger", settings.spark["max_offsets_per_trigger"])
        .option("useDeprecatedOffsetFetching", settings.spark["deprecated_offsets"])
        .load())
    
    # Explode the data from Avro
    expanded_df = (input_df
        .withColumn("avroData", from_avro(col("value"), trades_schema))
        .select("avroData.*")
        .select(explode(col("data")), col("type"))
        .select("col.*"))
    
    # Rename columns and add proper timestamps
    final_df = (expanded_df
        .withColumn("uuid", make_uuid())
        .withColumnRenamed("c", "trade_conditions")
        .withColumnRenamed("p", "price")
        .withColumnRenamed("s", "symbol")
        .withColumnRenamed("t", "trade_timestamp")
        .withColumnRenamed("v", "volume")
        .withColumn("trade_timestamp", (col("trade_timestamp") / 1000).cast("timestamp"))
        .withColumn("ingest_timestamp", current_timestamp().alias("ingest_timestamp")))
    
    # Write query to Cassandra
    def process_batch(batch_df, batch_id):
        print(f"Writing to Cassandra {batch_id}")
        (batch_df.write
            .format("org.apache.spark.sql.cassandra")
            .options(table=settings.cassandra["trades"], keyspace=settings.cassandra["keyspace"])
            .mode("append")
            .save())
    
    query = (final_df
        .writeStream
        .foreachBatch(process_batch)
        .outputMode("update")
        .start())
    
    # Another DataFrame with aggregates - running averages from last 15 seconds
    summary_df = (final_df
        .withColumn("price_volume_multiply", col("price") * col("volume"))
        .withWatermark("trade_timestamp", "15 seconds")
        .groupBy("symbol")
        .agg(avg("price_volume_multiply")))
    
    # Rename columns in DataFrame and add UUIDs before inserting to Cassandra
    final_summary_df = (summary_df
        .withColumn("uuid", make_uuid())
        .withColumn("ingest_timestamp", current_timestamp().alias("ingest_timestamp"))
        .withColumnRenamed("avg(price_volume_multiply)", "price_volume_multiply"))
    
    # Write second query to Cassandra
    def process_batch2(batch_df, batch_id):
        print(f"Writing to Cassandra {batch_id}")
        (batch_df.write
            .format("org.apache.spark.sql.cassandra")
            .options(table=settings.cassandra["aggregates"], keyspace=settings.cassandra["keyspace"])
            .mode("append")
            .save())
    
    query2 = (final_summary_df
        .writeStream
        .trigger(processingTime="5 seconds")
        .foreachBatch(process_batch2)
        .outputMode("update")
        .start())
    
    # Let query await termination
    spark.streams.awaitAnyTermination()