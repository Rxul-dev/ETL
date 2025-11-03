# from pyspark.sql import SparkSession
# from pyspark.sql.functions import hour, count

# spark = SparkSession.builder.appName("quick-demo").getOrCreate()

# url = "jdbc:postgresql://dw:5432/warehouse"
# props = {"user":"postgres","password":"postgres","driver":"org.postgresql.Driver"}

# df = spark.read.jdbc(url=url, table="fact_messages", properties=props)

# # 1) mensajes por usuario
# by_user = df.groupBy("sender_id").agg(count("*").alias("messages")).orderBy("messages", ascending=False)
# by_user.show(10)

# # 2) heatmap por hora (simple)
# by_hour = df.withColumn("h", hour("created_at")).groupBy("h").agg(count("*").alias("messages")).orderBy("h")
# by_hour.show(24)

# # opcional: guarda resultados en parquet dentro del contenedor (visible en Spark UI)
# by_user.write.mode("overwrite").parquet("/opt/spark-data/out/messages_by_user")
# by_hour.write.mode("overwrite").parquet("/opt/spark-data/out/messages_by_hour")

# spark.stop()