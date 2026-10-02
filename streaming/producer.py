"""
Publish one day of claim events to Kafka.

    python -m streaming.producer --date 2026-10-01
    python -m streaming.producer --date 2026-10-01 --delay 0.5   # slow, for a live demo

Reads data/outbox/claim_events_<date>.jsonl (written by the generator) and
sends every event to the claim-events topic. The claim_id is the message
key, so all events of one claim land in the same partition and stay in order.
"""
import argparse
import json
import os
import time
from confluent_kafka import Producer
from pipeline.settings import ROOT

TOPIC = "claim-events"
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")

def publish(day, delay=0.0):
    path = ROOT /"data" /"outbox" / f"claim_events_{day}.jsonl"
    if not path.exists():
        raise SystemExit(f"{path} not found. Run 'python -m generator daily --date {day}' first.")
    producer = Producer({"bootstrap.servers": BOOTSTRAP, "acks": "all"})
    failed = []

    def on_delivery(err, msg):
        if err:
            failed.append(err)

    sent = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            event = json.loads(line)
            producer.produce(TOPIC, key=event["claim_id"], value=line.strip(), on_delivery=on_delivery)
            producer.poll(0) # serve delivery callback
            sent += 1
            if delay:
                print(f"  {event['event_ts']}  {event['event_type']:<15} {event['claim_id']}")
                time.sleep(delay)
    producer.flush(10)
    if failed:
        raise SystemExit(f"{len(failed)} of {sent} message failed: {failed[0]}")
    print(f"Sent {sent} events for {day} to '{TOPIC}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--delay", type=float, default=0.0, help="Seconds between messages")
    args = parser.parse_args()
    publish(args.date, args.delay)
