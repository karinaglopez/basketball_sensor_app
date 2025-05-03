from confluent_kafka import Consumer
from sqlalchemy import create_engine, Column, Integer, JSON, String, DateTime, Float, Boolean, BIGINT
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import os 
import logging
import json

logging.basicConfig(level=logging.DEBUG)

#Kafka variables
kafka_host = os.getenv("KAFKA_HOST")
kafka_port = os.getenv("KAFKA_PORT")
oxygen_kafka_topic = os.getenv("OXYGEN_KAFKA_TOPIC") 
heart_frequency_kafka_topic = os.getenv("HEART_FREQUENCY_KAFKA_TOPIC") 
temperature_kafka_topic = os.getenv("TEMPERATURE_KAFKA_TOPIC")

# Database setup
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class Oxygen(Base):
    __tablename__ = 'oxygen_saturation'
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    sensor_id = Column(String)
    value = Column(Integer)
    is_valid = Column(Boolean)
    registered_at = Column(DateTime) 

class HeartRate(Base):
    __tablename__ = 'heart_frequency'
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    sensor_id = Column(String)
    value = Column(Integer)
    is_valid = Column(Boolean)
    registered_at = Column(DateTime) 

class Temperature(Base):
    __tablename__ = 'temperature'
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    sensor_id = Column(String)
    value = Column(Float)
    registered_at = Column(DateTime) 

Base.metadata.create_all(engine)

kafka_url = f"{kafka_host}:{kafka_port}"
# Kafka Consumer setup
c = Consumer({'bootstrap.servers': kafka_url, 'group.id': 'python-consumer', 'auto.offset.reset': 'earliest'})
logging.info('Kafka Consumer has been initiated...')

logging.info(f'Available topics to consume: {c.list_topics().topics}')
c.subscribe([oxygen_kafka_topic, heart_frequency_kafka_topic, temperature_kafka_topic])


def handle_oxygen(data):
    try:
        parsed_data = json.loads(data)
        logging.info(parsed_data)
        oxygen = Oxygen(
            sensor_id=parsed_data["sensor"],
            value=parsed_data["value"],
            is_valid=bool(parsed_data["isValid"]),
            registered_at=datetime.fromtimestamp(parsed_data["timestamp"], tz=timezone.utc) 
        )
        session.add(oxygen)
        session.commit()
        logging.info(f"Oxygen data saved: {str(oxygen)}")
    except Exception as e:
        logging.error(f"Failed to handle oxygen data: {e}")

def handle_heart_rate(data):
    try:
        parsed_data = json.loads(data)
        heart_rate = HeartRate(
            sensor_id=parsed_data["sensor"],
            value=parsed_data["value"],
            is_valid=bool(parsed_data["isValid"]),
            registered_at=datetime.fromtimestamp(parsed_data["timestamp"], tz=timezone.utc) 
        )
        session.add(heart_rate)
        session.commit()
        logging.info(f"Heart rate data saved: {str(heart_rate)}")
    except Exception as e:
        logging.error(f"Failed to handle heart rate data: {e}")

def handle_temperature(data):
    try:
        parsed_data = json.loads(data)
        temperature = Temperature(
            sensor_id=parsed_data["sensor"],
            value=parsed_data["value"],
            registered_at=datetime.fromtimestamp(parsed_data["timestamp"], tz=timezone.utc) 
        )
        session.add(temperature)
        session.commit()
        logging.info(f"Temperature data saved: {str(temperature)}")
    except Exception as e:
        logging.error(f"Failed to handle temperature data: {e}")

def main():
    while True:
        msg = c.poll(1.0)  # timeout
        if msg is None:
            continue
        if msg.error():
            logging.info('Error: {}'.format(msg.error()))
            continue
        data = msg.value().decode('utf-8')
        topic = msg.topic()
        logging.info(f'Received message in {topic}: {data}')
        if topic == oxygen_kafka_topic:
            handle_oxygen(data)
        elif topic == heart_frequency_kafka_topic:
            handle_heart_rate(data)
        elif topic == temperature_kafka_topic:
            handle_temperature(data)
        else:
            logging.info(f"Unknown topic {topic}: {data}")
    c.close()

if __name__ == '__main__':
    main()