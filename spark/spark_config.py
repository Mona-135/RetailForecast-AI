"""
Apache Spark configuration builder for local and cluster PySpark execution.
"""

import os
import sys
import logging

logger = logging.getLogger("SparkConfig")

def get_spark_session(app_name="RetailSalesETL", master=None):
    """
    Creates and returns an optimized SparkSession.
    Configured for local Windows or Docker HDFS cluster.
    """
    if master is None:
        master = os.getenv("SPARK_MASTER", "local[*]")

    try:
        from pyspark.sql import SparkSession
        builder = (
            SparkSession.builder
            .appName(app_name)
            .master(master)
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
            .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
            .config("spark.driver.memory", os.getenv("SPARK_DRIVER_MEMORY", "2g"))
            .config("spark.driver.host", "127.0.0.1")
            .config("spark.ui.enabled", "false")
        )

        # Connect to HDFS if explicitly requested in cluster mode
        hdfs_url = os.getenv("HDFS_NAMENODE_URL", "")
        if hdfs_url and not master.startswith("local"):
            builder = builder.config("fs.defaultFS", hdfs_url)

        spark = builder.getOrCreate()
        spark.sparkContext.setLogLevel("WARN")
        logger.info(f"Initialized SparkSession: version={spark.version}, master={master}")
        return spark
    except Exception as exc:
        logger.warning(f"Could not initialize PySpark session: {exc}")
        return None
