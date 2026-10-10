"""
Kafka configuration and connection helpers for Retail Sales streaming.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Kafka broker connection
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")

# Topic Names
TOPIC_RETAIL_SALES = os.getenv("KAFKA_TOPIC", "retail-sales")
TOPIC_RETAIL_SALES_PROCESSED = os.getenv("KAFKA_PROCESSED_TOPIC", "retail-sales-processed")

# Consumer configuration
CONSUMER_GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP", "retail-forecast-group")
AUTO_OFFSET_RESET = "earliest"

# Local fallback staging directory for HDFS simulation / offline mode
LOCAL_STAGING_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed", "kafka_ingest")
os.makedirs(LOCAL_STAGING_DIR, exist_ok=True)
