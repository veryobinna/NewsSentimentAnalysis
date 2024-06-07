spark-shell --master local --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.1

import org.apache.spark.sql._
import org.apache.spark.sql.types._ 

val dataSchema = new StructType()
 .add("title", "string")
 .add("source", "string")
 .add("content", "string")
 .add("sentiment", "string")

val newsdata = spark.readStream
  .format("csv")
  .option("header", "true")
  .schema(dataSchema)
  .option("path","hdfs:///bigdata/").load()

val news_data_filtered = newsdata.filter(col("title") !== "Removed")

val news_data_agg = news_data_filtered
  .withColumn("trump_count", size(split(lower(col("content")), "donald trump")) - 1)
  .groupBy("source")
  .agg(
    sum("trump_count").alias("total_trump_mentions"),
    sum(when(col("sentiment") === "1.0", 1).otherwise(0)).alias("pos_count"),
    sum(when(col("sentiment") === "0", 1).otherwise(0)).alias("neg_count"),
    sum(when(col("sentiment").isin("1.0", "0"), 1).otherwise(0)).alias("total_count")
  )

val news_value = news_data_agg.withColumn("key", lit(100))
 .select(
    col("key").cast("string"), 
    concat(col("source"), lit(","), 
    col("total_trump_mentions"), lit(","),
    col("pos_count"), lit(","), 
    col("neg_count"), lit(","),
    col("total_count")
    ).alias("value"))


 val stream = news_value.writeStream
 .format("kafka")
 .option("kafka.bootstrap.servers", "localhost:9092")
 .option("topic", "big-data-project") 
 .option("checkpointLocation", "file:////home/kingobiorah/chkpt")
 .outputMode("complete")
 .start()



