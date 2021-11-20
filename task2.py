import socket

#from common_utils.kafka_wrapper import KafkaConsumer, KafkaProducer, KafkaConfig


import json
from dataclasses import dataclass
from typing import Any, List, Optional

from confluent_kafka import Producer
from confluent_kafka import Consumer
import time


def serialize(data):
    return json.dumps(
        data, default=lambda x: x.__dict__
    ).encode("utf-8")


def _on_deliver(err: Any, msg: Any):
    if err is not None:
        print(f"failed to push event : [{msg}]")
        print(f"failed with error : [{err}]")
    else:
        print("OK!")


producer = Producer({"bootstrap.servers": '213.233.179.83:9092', 'client.id': socket.gethostname()})

for i in range(5):
    print(i)
    producer.poll(0)
    producer.produce(
        "raw",
        serialize({1:'a'}),
        callback=_on_deliver,
    )
    producer.flush()


time.sleep(5)

consumer = Consumer(
    {
        'bootstrap.servers': '213.233.179.83:9092',
        'group.id': 'mygroup',
        'auto.offset.reset': 'earliest'
    }
)
consumer.subscribe(["raw"])

while True:
    msg = consumer.poll(1.0)

    if msg is None:
        continue
    if msg.error():
        print("Consumer error: {}".format(msg.error()))
        continue

    print('Received message: {}'.format(msg.value().decode('utf-8')))