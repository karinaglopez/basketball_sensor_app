from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
from faker import Faker
import json
import time
import paho.mqtt.client as mqtt
import logging
import os
import ssl

logging.basicConfig(level=logging.DEBUG)

# UPLOAD ENV VARIABLES
mqtt_broker = os.getenv("MQTT_BROKER") 
mqtt_port = int(os.getenv("MQTT_PORT"))
kafka_host = os.getenv("KAFKA_HOST")
kafka_port = os.getenv("KAFKA_PORT")
mqtt_user = os.getenv("MQTT_USER")
mqtt_password = os.getenv("MQTT_PASSWORD")  
ca_cert = os.getenv("CA_CERT")
num_sensors = int(os.getenv("NUM_SENSORS"))
mqtt_client_id = os.getenv("CLIENT_ID_KAFKA_PRODUCER")


#UPLOAD TOPICS
oxygen_mqtt_topic = os.getenv("OXYGEN_MQTT_TOPIC") 
heart_frequency_mqtt_topic = os.getenv("HEART_FREQUENCY_MQTT_TOPIC") 
temperature_mqtt_topic = os.getenv("TEMPERATURE_MQTT_TOPIC") 
oxygen_kafka_topic = os.getenv("OXYGEN_KAFKA_TOPIC") 
heart_frequency_kafka_topic = os.getenv("HEART_FREQUENCY_KAFKA_TOPIC") 
temperature_kafka_topic = os.getenv("TEMPERATURE_KAFKA_TOPIC")

kafka_url = f"{kafka_host}:{kafka_port}"
kafka_config = {
    'bootstrap.servers': kafka_url,
    'enable.idempotence': True,
    'acks': 'all',
    'retries': 5,
    'linger.ms': 5,
    'compression.type': 'snappy'
}
p = Producer(kafka_config)

def create_kafka_topic(topic_name, num_partitions=num_sensors, replication_factor=1):
    admin_client = AdminClient({'bootstrap.servers': kafka_url})
    topic = NewTopic(topic_name, num_partitions=num_partitions, replication_factor=replication_factor)
    try:
        admin_client.create_topics([topic])
        logging.info(f"Topic '{topic_name}' created with {num_partitions} partitions.")
    except Exception as e:
        logging.warning(f"Topic '{topic_name}' already exists or failed to create: {e}")

create_kafka_topic(oxygen_kafka_topic, num_partitions=num_sensors)
create_kafka_topic(heart_frequency_kafka_topic, num_partitions=num_sensors)
create_kafka_topic(temperature_kafka_topic, num_partitions=num_sensors)

def delivery_report(err, msg):
    if err is not None:
        logging.error('Message delivery failed: {}'.format(err))
    else:
        logging.info('Message delivered to {} in partition [{}]'.format(msg.topic(), msg.partition()))

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))  # <-- Fix here
        topic = msg.topic
        logging.info(f"Received message on topic {topic}: {data}")
        metric = topic.split('/')[1]
        sensor_id = data['sensor']
        kafka_key = f"{sensor_id}_{metric}_{data['timestamp']}"
        
        partition = int(sensor_id) - 1

        if topic == oxygen_mqtt_topic:
            p.produce(oxygen_kafka_topic, key=kafka_key, value=json.dumps(data), partition=partition, callback=delivery_report)
        elif topic == heart_frequency_mqtt_topic:
            p.produce(heart_frequency_kafka_topic, key=kafka_key, value=json.dumps(data), partition=partition, callback=delivery_report)
        elif topic == temperature_mqtt_topic:
            p.produce(temperature_kafka_topic, key=kafka_key, value=json.dumps(data), partition=partition, callback=delivery_report)

        p.poll(1)
    except Exception as e:
        logging.error(f"Error proccessing MQTT message {msg}: {e}")



def on_connect(client, userdata, flags, reason_code):
    if reason_code != 0:
        logging.error(f"Failed to connect: {reason_code}. Will retry connection")
    else:
        client.subscribe(oxygen_mqtt_topic, qos=1)
        client.subscribe(heart_frequency_mqtt_topic, qos=1)
        client.subscribe(temperature_mqtt_topic, qos=1)
        logging.info('Subscribed succesfully to topics')

mqttc = mqtt.Client(client_id= mqtt_client_id, protocol=mqtt.MQTTv311, clean_session=False)
mqttc.username_pw_set(mqtt_user, mqtt_password)
mqttc.tls_set(ca_certs=ca_cert, cert_reqs=ssl.CERT_REQUIRED,
              tls_version=ssl.PROTOCOL_TLSv1_2)
mqttc.enable_logger()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
#mqttc.on_subscribe = on_subscribe
#mqttc.on_unsubscribe = on_unsubscribe

mqttc.user_data_set([])
logging.info(f"Connecting to MQTT broker at {mqtt_broker}:{mqtt_port}")
try:
    mqttc.connect(mqtt_broker, mqtt_port, 60)
    mqttc.loop_forever()
except ssl.SSLError as e:
    logging.error(f"SSL error: {e}")
except Exception as e:
    logging.error(f"Connection error: {e}")

