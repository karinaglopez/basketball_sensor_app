# Basketball Sensors App

Este proyecto implementa una arquitectura IoT para la recolección, procesamiento y almacenamiento de datos de sensores de baloncesto usando MQTT, Kafka y PostgreSQL, todo orquestado con Docker Compose.

## Arquitectura

- **Arduino/ESP32**: Recoge datos de sensores (oxígeno, frecuencia cardíaca, temperatura) y los publica vía MQTT.
- **Mosquitto**: Broker MQTT seguro para la ingesta de mensajes.
- **Kafka**: Broker de mensajes para streaming de datos escalable y confiable.
- **Kafka Producer**: Suscribe a tópicos MQTT y reenvía los mensajes a tópicos de Kafka, particionando por sensor.
- **Kafka Consumer**: Lee de Kafka y almacena los datos en PostgreSQL.
- **PostgreSQL**: Almacena los datos procesados para consultas y analítica.

## Estructura del repositorio

```
.
├── arduino/                # Firmware Arduino/ESP32
├── certs/                  # Certificados SSL para Mosquitto
├── env_files/              # Archivos de variables de entorno
├── kafka_consumer/         # Código Python del consumidor de Kafka
├── kafka_producer/         # Código Python del productor de Kafka
├── mqtt/                   # Configuración de Mosquitto
├── postgres/               # Volumen de datos de PostgreSQL
├── queries/                # Consultas SQL para dashboards
├── docker-compose.yml      # Orquestación de servicios
└── README.md               # Documentación del proyecto
```

## Puesta en marcha

### Requisitos
- Docker & Docker Compose
- Python 3.9 (para desarrollo local)
- Arduino IDE (para firmware)

### Instalación y ejecución
1. **Clona el repositorio**
   ```bash
   git clone <repo-url>
   cd basketball-sensors-app
   ```
2. **Configura las variables de entorno**
   - Edita los archivos en `env_files/` según tus necesidades (`mqtt.env`, `kafka.env`, `postgres.env`).
3. **Genera los certificados SSL**
   - Coloca tus certificados en el directorio `certs/`.
4. **Levanta la infraestructura**
   ```bash
   docker-compose up --build
   ```
5. **Carga el firmware en Arduino/ESP32**
   - Sube el código de `arduino/final_sketch.ino` a tu dispositivo, actualizando credenciales Wi-Fi y MQTT.

## Seguridad
- La comunicación MQTT está asegurada con TLS (ver `mqtt/config/mosquitto.conf` y `certs/`).
- Mosquitto utiliza autenticación de usuario/contraseña y ACLs.

## Comandos útiles
- **Ver particiones de un tópico Kafka:**
  ```bash
  docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --describe --topic <topic_name>
  ```
- **Ver logs de Mosquitto:**
  ```bash
  docker exec -it mosquitto tail -f /mosquitto/log/mosquitto.log
  ```
- **Acceder a PostgreSQL:**
  ```bash
  docker exec -it db psql -U <POSTGRES_USER> -d <POSTGRES_DB>
  ```

## Troubleshooting
- Verifica que todas las variables de entorno estén correctamente configuradas.
- Revisa los logs de cada servicio con `docker logs <container_name>`.
- Para problemas de SSL/TLS, revisa rutas y permisos de los certificados.

## Licencia
MIT License

---
**Autor:** Karina Lopez
