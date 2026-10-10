"""
Kafka Producer for Retail Sales Records.
Simulates streaming ingestion of Walmart historical sales records into Apache Kafka.
Handles CSV parsing, JSON formatting, batch delivery, configurable throttles,
graceful shutdown on SIGINT, and local dry-run staging if Kafka is offline.
"""

import os
import sys
import json
import time
import signal
import logging
import argparse
import csv
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [KafkaProducer] %(message)s"
)
logger = logging.getLogger("KafkaProducer")

# Graceful termination handler
RUNNING = True
def signal_handler(sig, frame):
    global RUNNING
    logger.info("Shutdown signal received. Stopping Kafka producer gracefully...")
    RUNNING = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def load_csv_records(file_path):
    """
    Reads Walmart sales CSV and yields normalized JSON-serializable dictionaries.
    Automatically detects column naming variations (e.g. Store, Dept, Date, Weekly_Sales).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input sales CSV not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Normalize column header lookup
        header_map = {col.lower(): col for col in reader.fieldnames or []}

        store_col = header_map.get("store")
        dept_col = header_map.get("dept") or header_map.get("department")
        date_col = header_map.get("date")
        sales_col = header_map.get("weekly_sales") or header_map.get("sales")
        holiday_col = header_map.get("isholiday") or header_map.get("is_holiday")

        if not all([store_col, dept_col, date_col, sales_col]):
            raise ValueError(f"CSV missing essential columns. Detected: {reader.fieldnames}")

        for row in reader:
            try:
                store_val = int(row[store_col])
                dept_val = int(row[dept_col])
                date_val = str(row[date_col]).strip()
                sales_val = float(row[sales_col])
                
                is_hol = False
                if holiday_col and holiday_col in row:
                    raw_hol = str(row[holiday_col]).strip().lower()
                    is_hol = raw_hol in ("true", "1", "t", "yes")

                record = {
                    "store": store_val,
                    "department": dept_val,
                    "date": date_val,
                    "weekly_sales": round(sales_val, 2),
                    "is_holiday": is_hol,
                    "ingestion_timestamp": datetime.utcnow().isoformat() + "Z"
                }
                yield record
            except (ValueError, TypeError) as err:
                logger.warning(f"Skipping malformed row: {row} - error: {err}")

def run_producer(file_path, topic, bootstrap_servers, delay_sec=0.01, batch_size=50, max_records=None):
    """
    Produces records to Kafka broker or stages to local queue if Kafka is unreachable.
    """
    logger.info(f"Starting Kafka producer on topic='{topic}' brokers={bootstrap_servers}")
    logger.info(f"Source file: {file_path} | Delay: {delay_sec}s | Batch size: {batch_size}")

    producer = None
    use_mock_fallback = False

    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            retries=3,
            max_block_ms=5000
        )
        # Verify connection
        logger.info("Successfully connected to Apache Kafka cluster.")
    except Exception as exc:
        logger.warning(f"Could not connect to Kafka broker at {bootstrap_servers}: {exc}")
        logger.warning("Operating in fallback simulation mode: storing ingested records to local staging directory.")
        use_mock_fallback = True

    record_generator = load_csv_records(file_path)
    count = 0
    fallback_records = []

    fallback_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data", "processed", "kafka_ingest", f"staged_stream_{int(time.time())}.jsonl"
    )

    for record in record_generator:
        if not RUNNING:
            break
        if max_records and count >= max_records:
            break

        if not use_mock_fallback and producer:
            try:
                producer.send(topic, value=record)
            except Exception as err:
                logger.error(f"Error publishing to Kafka: {err}. Switching to fallback staging.")
                use_mock_fallback = True
                fallback_records.append(record)
        else:
            fallback_records.append(record)

        count += 1

        if count % batch_size == 0:
            if producer and not use_mock_fallback:
                producer.flush()
            elif fallback_records:
                with open(fallback_file, "a", encoding="utf-8") as f:
                    for r in fallback_records:
                        f.write(json.dumps(r) + "\n")
                fallback_records = []

            logger.info(f"Ingested {count} records successfully...")
            if delay_sec > 0:
                time.sleep(delay_sec)

    # Final flush
    if producer and not use_mock_fallback:
        producer.flush()
        producer.close()
    elif fallback_records:
        with open(fallback_file, "a", encoding="utf-8") as f:
            for r in fallback_records:
                f.write(json.dumps(r) + "\n")
        logger.info(f"Staged {len(fallback_records)} remaining events to {fallback_file}")

    logger.info(f"Kafka Producer finished. Total records ingested: {count}")
    return count

def main():
    parser = argparse.ArgumentParser(description="Walmart Sales Kafka Producer")
    parser.add_argument("--file", default="data/raw/train.csv", help="Path to raw CSV file")
    parser.add_argument("--topic", default="retail-sales", help="Kafka topic name")
    parser.add_argument("--servers", default="localhost:9092", help="Comma-separated Kafka bootstrap servers")
    parser.add_argument("--delay", type=float, default=0.005, help="Delay between record batches in seconds")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for flush")
    parser.add_argument("--max-records", type=int, default=None, help="Maximum records to stream (None for all)")
    args = parser.parse_args()

    servers = [s.strip() for s in args.servers.split(",")]
    run_producer(
        file_path=args.file,
        topic=args.topic,
        bootstrap_servers=servers,
        delay_sec=args.delay,
        batch_size=args.batch_size,
        max_records=args.max_records
    )

if __name__ == "__main__":
    main()
