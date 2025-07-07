import os
import json
import time
import ssl
import logging
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.DEBUG)

def load_config():
    return {
        "mqtt_broker": os.getenv("MQTT_BROKER"),
        "mqtt_port": int(os.getenv("MQTT_PORT")),
        "kafka_host": os.getenv("KAFKA_HOST"),
        "kafka_port": os.getenv("KAFKA_PORT"),
        "mqtt_user": os.getenv("MQTT_USER"),
        "mqtt_password": os.getenv("MQTT_PASSWORD"),
        "ca_cert": os.getenv("CA_CERT"),
        "num_sensors": int(os.getenv("NUM_SENSORS")),
        "mqtt_client_id": os.getenv("CLIENT_ID_KAFKA_PRODUCER"),
        "topics": {
            "mqtt": {
                "oxygen": os.getenv("OXYGEN_MQTT_TOPIC"),
                "heart": os.getenv("HEART_FREQUENCY_MQTT_TOPIC"),
                "temperature": os.getenv("TEMPERATURE_MQTT_TOPIC"),
            },
            "kafka": {
                "oxygen": os.getenv("OXYGEN_KAFKA_TOPIC"),
                "heart": os.getenv("HEART_FREQUENCY_KAFKA_TOPIC"),
                "temperature": os.getenv("TEMPERATURE_KAFKA_TOPIC"),
            }
        }
    }

def create_kafka_producer(kafka_url):
    kafka_config = {
        'bootstrap.servers': kafka_url,
        'enable.idempotence': True,
        'acks': 'all',
        'retries': 5,
        'linger.ms': 5,
        'compression.type': 'snappy'
    }
    return Producer(kafka_config)

def create_kafka_topics(config, kafka_url):
    admin_client = AdminClient({'bootstrap.servers': kafka_url})
    num_partitions = config["num_sensors"]

    topic_names = config["topics"]["kafka"].values()
    topics = [NewTopic(name, num_partitions=num_partitions, replication_factor=1) for name in topic_names]

    fs = admin_client.create_topics(topics)
    for topic, f in fs.items():
        try:
            f.result()
            logging.info(f"Topic '{topic}' created.")
        except Exception as e:
            logging.warning(f"Topic '{topic}' already exists or failed to create: {e}")

def delivery_report(err, msg):
    if err:
        logging.error(f"Message delivery failed: {err}")
    else:
        logging.info(f"Message delivered to {msg.topic()} in partition [{msg.partition()}]")

def on_message_factory(producer, config):
    def on_message(client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            topic = msg.topic
            metric = topic.split('/')[1]
            sensor_id = data['sensor']
            kafka_key = f"{sensor_id}_{metric}_{data['timestamp']}"
            partition = int(sensor_id) - 1

            mqtt_topics = config["topics"]["mqtt"]
            kafka_topics = config["topics"]["kafka"]

            if topic == mqtt_topics["oxygen"]:
                producer.produce(kafka_topics["oxygen"], key=kafka_key, value=json.dumps(data), partition=partition, callback=delivery_report)
            elif topic == mqtt_topics["heart"]:
                producer.produce(kafka_topics["heart"], key=kafka_key, value=json.dumps(data), partition=partition, callback=delivery_report)
            elif topic == mqtt_topics["temperature"]:
                producer.produce(kafka_topics["temperature"], key=kafka_key, value=json.dumps(data), partition=partition, callback=delivery_report)

            producer.poll(1)
        except Exception as e:
            logging.error(f"Error processing MQTT message {msg}: {e}")
    return on_message

def on_connect_factory(config):
    def on_connect(client, userdata, flags, reason_code):
        if reason_code != 0:
            logging.error(f"Failed to connect: {reason_code}")
        else:
            topics = config["topics"]["mqtt"]
            client.subscribe(topics["oxygen"], qos=1)
            client.subscribe(topics["heart"], qos=1)
            client.subscribe(topics["temperature"], qos=1)
            logging.info('Successfully subscribed to topics')
    return on_connect

def setup_mqtt_client(config, on_message_cb, on_connect_cb):
    client = mqtt.Client(client_id=config["mqtt_client_id"], protocol=mqtt.MQTTv311, clean_session=False)
    client.username_pw_set(config["mqtt_user"], config["mqtt_password"])
    client.tls_set(ca_certs=config["ca_cert"], cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2)
    client.enable_logger()
    client.on_message = on_message_cb
    client.on_connect = on_connect_cb
    return client

def main():
    config = load_config()
    kafka_url = f"{config['kafka_host']}:{config['kafka_port']}"
    producer = create_kafka_producer(kafka_url)

    create_kafka_topics(config, kafka_url)

    on_message_cb = on_message_factory(producer, config)
    on_connect_cb = on_connect_factory(config)
    mqtt_client = setup_mqtt_client(config, on_message_cb, on_connect_cb)

    logging.info(f"Connecting to MQTT broker at {config['mqtt_broker']}:{config['mqtt_port']}")
    try:
        mqtt_client.connect(config["mqtt_broker"], config["mqtt_port"], 60)
        mqtt_client.loop_forever()
    except ssl.SSLError as e:
        logging.error(f"SSL error: {e}")
    except Exception as e:
        logging.error(f"Connection error: {e}")

if __name__ == "__main__":
    main()
