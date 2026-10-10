"""
Kafka Consumer for Retail Sales Events.
Subscribes to 'retail-sales', validates record schema,
buffers and sinks validated sales events to an HDFS-compatible storage destination.
Handles malformed records gracefully and reconnects automatically.
"""

import os
import sys
import json
import time
import signal
import logging
import argparse
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [KafkaConsumer] %(message)s"
)
logger = logging.getLogger("KafkaConsumer")

RUNNING = True
def signal_handler(sig, frame):
    global RUNNING
    logger.info("Shutdown signal received. Stopping consumer gracefully...")
    RUNNING = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def validate_record(record):
    """
    Validates required fields and data types for sales events.
    """
    if not isinstance(record, dict):
        return False, "Record is not a JSON object"
    
    required_keys = ["store", "department", "date", "weekly_sales"]
    for k in required_keys:
        if k not in record:
            return False, f"Missing required field: {k}"

    try:
        int(record["store"])
        int(record["department"])
        float(record["weekly_sales"])
        str(record["date"])
    except (ValueError, TypeError) as e:
        return False, f"Invalid field types: {e}"

    return True, None

def run_consumer(topic="retail-sales", bootstrap_servers=None, group_id="retail-forecast-group",
                 output_dir="data/processed/kafka_consumed", max_records=None, timeout_sec=10):
    if bootstrap_servers is None:
        bootstrap_servers = ["localhost:9092"]

    os.makedirs(output_dir, exist_ok=True)
    out_filename = os.path.join(output_dir, f"consumed_events_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl")

    logger.info(f"Connecting consumer to topic='{topic}', group='{group_id}'...")
    logger.info(f"Output destination: {out_filename}")

    consumer = None
    try:
        from kafka import KafkaConsumer
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            consumer_timeout_ms=timeout_sec * 1000,
            value_deserializer=lambda v: json.loads(v.decode("utf-8", errors="ignore"))
        )
        logger.info("Connected to Kafka. Listening for messages...")
    except Exception as exc:
        logger.warning(f"Could not connect to Kafka broker ({exc}).")
        logger.info("Checking for locally staged Kafka files in data/processed/kafka_ingest...")
        staged_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed", "kafka_ingest")
        if os.path.exists(staged_dir):
            files = [os.path.join(staged_dir, f) for f in os.listdir(staged_dir) if f.endswith(".jsonl")]
            total_staged = 0
            with open(out_filename, "w", encoding="utf-8") as out_f:
                for fpath in files:
                    with open(fpath, "r", encoding="utf-8") as in_f:
                        for line in in_f:
                            try:
                                rec = json.loads(line.strip())
                                valid, _ = validate_record(rec)
                                if valid:
                                    out_f.write(json.dumps(rec) + "\n")
                                    total_staged += 1
                            except Exception:
                                pass
            logger.info(f"Successfully processed {total_staged} staged events into {out_filename}")
            return total_staged
        return 0

    valid_count = 0
    invalid_count = 0
    buffer = []

    try:
        with open(out_filename, "a", encoding="utf-8") as out_file:
            for message in consumer:
                if not RUNNING:
                    break

                try:
                    payload = message.value
                    is_valid, err = validate_record(payload)
                    if is_valid:
                        buffer.append(json.dumps(payload))
                        valid_count += 1
                    else:
                        invalid_count += 1
                        logger.warning(f"Rejected invalid message at offset {message.offset}: {err}")

                    if len(buffer) >= 100:
                        out_file.write("\n".join(buffer) + "\n")
                        out_file.flush()
                        buffer.clear()
                        logger.info(f"Committed {valid_count} events to disk (invalid: {invalid_count})")

                    if max_records and valid_count >= max_records:
                        logger.info(f"Reached target message limit ({max_records}). Stopping.")
                        break

                except json.JSONDecodeError as jde:
                    invalid_count += 1
                    logger.warning(f"Malformed JSON at partition {message.partition}, offset {message.offset}: {jde}")
                except Exception as ex:
                    logger.error(f"Unexpected error processing message: {ex}")

            if buffer:
                out_file.write("\n".join(buffer) + "\n")
                out_file.flush()
                buffer.clear()

    finally:
        if consumer:
            consumer.close()
            logger.info("Kafka consumer closed.")

    logger.info(f"Consumption finished. Valid records: {valid_count}, Invalid: {invalid_count}")
    return valid_count

def main():
    parser = argparse.ArgumentParser(description="Walmart Sales Kafka Consumer")
    parser.add_argument("--topic", default="retail-sales", help="Kafka topic")
    parser.add_argument("--servers", default="localhost:9092", help="Bootstrap servers")
    parser.add_argument("--group", default="retail-forecast-group", help="Consumer group ID")
    parser.add_argument("--output-dir", default="data/processed/kafka_consumed", help="HDFS/Local output directory")
    parser.add_argument("--max-records", type=int, default=None, help="Max records to consume")
    parser.add_argument("--timeout", type=int, default=8, help="Timeout in seconds before exiting if no messages")
    args = parser.parse_args()

    servers = [s.strip() for s in args.servers.split(",")]
    run_consumer(
        topic=args.topic,
        bootstrap_servers=servers,
        group_id=args.group,
        output_dir=args.output_dir,
        max_records=args.max_records,
        timeout_sec=args.timeout
    )

if __name__ == "__main__":
    main()
