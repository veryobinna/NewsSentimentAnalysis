spark-shell --master local --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.1



import org.apache.spark.sql.functions._
import org.apache.spark.ml.feature.{Tokenizer, HashingTF}
import org.apache.spark.ml.Pipeline
import org.apache.spark.ml.classification.LogisticRegression
import org.apache.spark.ml.tuning.{CrossValidator, CrossValidatorModel, ParamGridBuilder}
import org.apache.spark.ml.evaluation.MulticlassClassificationEvaluator

import org.apache.spark.ml.param.ParamMap
import org.apache.spark.sql.types.{DoubleType}

import org.apache.spark.sql._
import org.apache.spark.sql.types._ 


val dataSchema = new StructType()
 .add("title", "string")
 .add("source", "string")
 .add("content", "string")
 .add("sentiment", "string")


val newsdata = spark.read
  .format("csv")
  .option("header", "true")
  .schema(dataSchema)
  .option("path","hdfs:///bigdata/news_feed_1_0.csv").load()

val news_data_filtered = newsdata.filter(col("title") !== "Removed")

val content_data = news_data_filtered
  .select(col("content"), col("sentiment").cast(DoubleType))
  .na.drop()

val Array(trainingData, testData) = content_data.randomSplit(Array(0.8, 0.2), 443) 

val tokenizer = new Tokenizer().setInputCol("content").setOutputCol("words")
val hashingTF = new HashingTF().setNumFeatures(1000).setInputCol(tokenizer.getOutputCol).setOutputCol("features")

val lr = new LogisticRegression().setMaxIter(10).setRegParam(0.01).setFeaturesCol("features").setLabelCol("sentiment")

val pipeline = new Pipeline().setStages(Array(tokenizer, hashingTF, lr))

val evaluator = new MulticlassClassificationEvaluator()
  .setLabelCol("sentiment")
  .setPredictionCol("prediction")
  .setMetricName("accuracy")

val cross_validator = new CrossValidator()
  .setEstimator(pipeline)
  .setEvaluator(evaluator)
  .setEstimatorParamMaps(new ParamGridBuilder().build)
  .setNumFolds(3)

 val cvModel = cross_validator.fit(trainingData)

 val predictions = cvModel.transform(testData)

predictions
 .select(col("content"), col("sentiment"), col("prediction"))
 .write
 .format("csv")
 .save("hdfs:///bigdata/output/")

 val r2 = evaluator.evaluate(predictions)

println("r-squared on test data = " + r2)

