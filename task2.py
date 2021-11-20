import pathlib
import socket
import json
from typing import Any
import csv
from confluent_kafka import Producer
from confluent_kafka import Consumer
import time
import pandas as pd

col_names = ('Account', 'Post Link', 'Caption', 'Post Type', 'Comments', 'View', 'Video Duration')


# Producer sending data on queue
def push(data):
    producer.poll(0)
    producer.produce(
        "rawdata",
        data,
        callback=_on_deliver,
    )
    producer.flush()


# Consumer pulling data
def pull():
    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            print("Consumer error: {}".format(msg.error()))
            continue

        print('Received message: {}'.format(msg.value().decode('utf-8')))


# Check if product is on queue
def _on_deliver(err: Any, msg: Any):
    if err is not None:
        print(f"failed to push event : [{msg}]")
        print(f"failed with error : [{err}]")
    else:
        pass


def read_csv(file, columns):
    reader = csv.DictReader(file, columns)
    for row in reader:
        push(json.dumps(row).encode("utf-8"))


def read_dir(dir_path):
    for path in pathlib.Path(dir_path).iterdir():
        if path.is_file():
            # removing index column :D
            df = pd.read_csv(path, index_col=0)
            df.to_csv(path, index=False)
            csv_file = open(path, "r", encoding='utf-8')
            read_csv(csv_file, columns=col_names)


def start_production(path):
    read_dir(path)


producer = Producer({"bootstrap.servers": '213.233.179.83:9092', 'client.id': socket.gethostname()})

start_production("C:/Users/najaf/Documents/Gitlab/little-crawler/bs_data")


time.sleep(5)

consumer = Consumer(
    {
        'bootstrap.servers': '213.233.179.83:9092',
        'group.id': 'mygroup',
        'auto.offset.reset': 'earliest'
    }
)
consumer.subscribe(["rawdata"])

pull()
