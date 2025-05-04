FROM python:3.9-slim
WORKDIR /app
COPY ./kafka_consumer/kafka_consumer.py /app
RUN pip install confluent_kafka sqlalchemy psycopg2-binary
CMD ["python", "kafka_consumer.py"]