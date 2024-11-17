from confluent_kafka import Producer
from faker import Faker
import json
import time
import paho.mqtt.client as mqtt
import logging
import os

logging.basicConfig(level=logging.DEBUG)

# UPLOAD ENV VARIABLES
mqtt_broker = os.getenv("MQTT_BROKER") 
mqtt_port = os.getenv("MQTT_PORT")
kafka_host = os.getenv("KAFKA_HOST")
kafka_port = os.getenv("KAFKA_PORT")

oxygen_mqtt_topic = os.getenv("OXYGEN_MQTT_TOPIC") 
heart_rate_mqtt_topic = os.getenv("HEART_RATE_MQTT_TOPIC") 
temperature_mqtt_topic = os.getenv("TEMPERATURE_MQTT_TOPIC") 
oxygen_kafka_topic = os.getenv("OXYGEN_KAFKA_TOPIC") 
heart_rate_kafka_topic = os.getenv("HEART_RATE_KAFKA_TOPIC") 
temperature_kafka_topic = os.getenv("TEMPERATURE_KAFKA_TOPIC")

kafka_url = f"{kafka_host}:{kafka_port}"
p = Producer({'bootstrap.servers': kafka_url})

def delivery_report(err, msg):
    if err is not None:
        logging.info('Message delivery failed: {}'.format(err))
    else:
        logging.info('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    # Since we subscribed only for a single channel, reason_code_list contains
    # a single entry
    if reason_code_list[0].is_failure:
        print(f"Broker rejected you subscription: {reason_code_list[0]}")
    else:
        print(f"Broker granted the following QoS: {reason_code_list[0].value}")

def on_unsubscribe(client, userdata, mid, reason_code_list, properties):
    # Be careful, the reason_code_list is only present in MQTTv5.
    # In MQTTv3 it will always be empty
    if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
        logging.info("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
    else:
        logging.info(f"Broker replied with failure: {reason_code_list[0]}")
    client.disconnect()

def on_message(client, userdata, msg):
    data = msg.payload.decode('utf-8')
    topic = msg.topic
    logging.info(f"Received message on topic {topic}: {data}")
    if topic == oxygen_mqtt_topic:
        logging.info(f'oxygen received: {data}')
        p.produce(oxygen_kafka_topic, key=str(time.time()), value=data, callback=delivery_report)
    elif topic == heart_rate_mqtt_topic:
        logging.info(f'Heart rate received: {data}')
        p.produce(heart_rate_kafka_topic, key=str(time.time()), value=data, callback=delivery_report)
    elif topic == temperature_mqtt_topic:
        logging.info(f'Temperature received: {data}')
        p.produce(temperature_kafka_topic, key=str(time.time()), value=data, callback=delivery_report)
    p.poll(1)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        client.subscribe(oxygen_mqtt_topic)
        client.subscribe(heart_rate_mqtt_topic)
        client.subscribe(temperature_mqtt_topic)

# START MQTT CLIENT
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.enable_logger()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_subscribe = on_subscribe
mqttc.on_unsubscribe = on_unsubscribe

mqttc.user_data_set([])
mqttc.connect(mqtt_broker, mqtt_port, 60)
mqttc.loop_forever()

