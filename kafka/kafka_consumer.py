from confluent_kafka import Consumer
from sqlalchemy import create_engine, Column, Integer, JSON, String
from sqlalchemy.orm import declarative_base, sessionmaker
import os 
import logging

logging.basicConfig(level=logging.DEBUG)


# Database setup
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
oxygen_kafka_topic = os.getenv("OXYGEN_KAFKA_TOPIC") 
heart_rate_kafka_topic = os.getenv("HEART_RATE_KAFKA_TOPIC") 
temperature_kafka_topic = os.getenv("TEMPERATURE_KAFKA_TOPIC")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class Oxygen(Base):
    __tablename__ = 'oxygen'
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(JSON)

class HeartRate(Base):
    __tablename__ = 'heart_rate'
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(JSON)

class Temperature(Base):
    __tablename__ = 'temperature'
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(JSON)

Base.metadata.create_all(engine)

# Kafka Consumer setup
c = Consumer({'bootstrap.servers': 'kafka:9092', 'group.id': 'python-consumer', 'auto.offset.reset': 'earliest'})
logging.info('Kafka Consumer has been initiated...')

logging.info(f'Available topics to consume: {c.list_topics().topics}')
c.subscribe([oxygen_kafka_topic, heart_rate_kafka_topic, temperature_kafka_topic])


def handle_oxygen(data):
    logging.info(f"Oxygen data received: {data}")
    oxygen = Oxygen(data=data)
    session.add(oxygen)
    session.commit()

def handle_heart_rate(data):
    logging.info(f"Heart rate data received: {data}")
    heart_rate = HeartRate(data=data)
    session.add(heart_rate)
    session.commit()

def handle_temperature(data):
    logging.info(f"Temperature data received: {data}")
    temperature = Temperature(data=data)
    session.add(temperature)
    session.commit()

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
        elif topic == heart_rate_kafka_topic:
            handle_heart_rate(data)
        elif topic == temperature_kafka_topic:
            handle_temperature(data)
        else:
            logging.info(f"Unknown topic {topic}: {data}")
    c.close()

if __name__ == '__main__':
    main()