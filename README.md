## To execute backend
docker compose up
docker compose down

docker compose logs -f kafka_producer
docker compose logs -f kafka_consumer

docker compose up -d --build
docker compose down


## To execute Redash
https://github.com/getredash/redash/wiki/Local-development-setup

make up
make down

http://localhost:5001/setup


o