def create_spark_connection():
    s_conn = None

    print("Creating Spark connection...")

    try:
        s_conn = SparkSession.builder \
            .appName('SparkDataStreaming') \
            .config('spark.jars.packages', "com.datastax.spark:spark-cassandra-connector_2.12:3.5.1,"
                                           "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
            .config('spark.cassandra.connection.host', 'broker') \
            .getOrCreate()

        # Set Spark log level to ERROR
        s_conn.sparkContext.setLogLevel("ERROR")

        print(f"Spark Version: {s_conn.version}")
        print(f"Spark Jars Packages: {s_conn.conf.get('spark.jars.packages')}")

        logging.info("Spark connection created successfully!")
        print("Connected")

    except Exception as e:
        logging.error(f"Couldn't create the Spark session due to exception: {e}")

    return s_conn
