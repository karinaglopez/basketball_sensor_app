FROM python:3.9-slim
WORKDIR /app
COPY ./kafka_producer/kafka_producer.py /app
RUN pip install confluent_kafka faker paho-mqtt
CMD ["python", "kafka_producer.py"]