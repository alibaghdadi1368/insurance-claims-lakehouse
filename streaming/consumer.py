"""
Read claim events from Kafka and drop them in S3 as small JSON files.

    python -m streaming.consumer                     # runs until Ctrl+C
    python -m streaming.consumer --stop-when-idle 20 # stops after 20 s without messages

Messages are collected in memory and written as one file every BATCH_SIZE
messages or FLUSH_SECONDS seconds, whichever comes first. Offsets are only
committed after the file is safely in S3: if the consumer crashes in
between, the same messages are read again (at-least-once). Silver removes
the duplicates that can cause.
"""

import argparse
import json
import os
import time
from datetime import datetime, timezone
import boto3
from confluent_kafka import Consumer, KafkaException
from pipeline.settings import env

TOPIC = "claim-events"
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
BATCH_SIZE = 200
FLUSH_SECONDS = 30

def batch_key(now=None) -> str:
    now = now or datetime.now(timezone.utc)
    return f"landing/claim_events/stream/claim_events_{now:%Y%m%dT%H%M%S%f}.jsonl"

def to_jsonl(values) -> bytes:
    # validate each message is JSON before it reaches the warehouse
    return "".join(json.dumps(json.loads(v)) + "\n" for v in values).encode("utf-8")

def run(stop_when_idle=None):
    s3 = boto3.client("s3", region_name=env("AWS_DEFAULT_REGION"))
    bucket = env("S3_BUCKET")
    consumer = Consumer({
        "bootstrap.servers": BOOTSTRAP,
        "group.id": "bronze-leader",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe([TOPIC])
    buffer, last_flush, last_message = [], time.time(), time.time()

    def flush():
        nonlocal buffer, last_flush
        if buffer:
            key = batch_key()
            s3.put_object(Bucket=bucket, Key=key, Body=to_jsonl(buffer))
            consumer.commit(asynchronous=False)
            print(f"  wrote {len(buffer):>4} events -> s3://{bucket}/{key}")
        buffer, last_flush = [], time.time()
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                if stop_when_idle and time.time() - last_message > stop_when_idle:
                    break
            elif msg.error():
                raise KafkaException(msg.error())
            else:
                buffer.append(msg.value().decode("utf-8"))
                last_message = time.time()
            if len(buffer) >= BATCH_SIZE or time.time() - last_flush > FLUSH_SECONDS:
                flush()
    except KeyboardInterrupt:
        pass
    finally:
        flush()
        consumer.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stop-when-idle", type=int, help="stop after this many seconds without messages")
    run(parser.parse_args().stop_when_idle)


