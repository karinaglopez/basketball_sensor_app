#include <WiFi.h>
#include <ArduinoMqttClient.h>
#include <Wire.h>
#include "MAX30105.h"
#include "spo2_algorithm.h"
#include "heartRate.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFiUdp.h>
#include <NTPClient.h>
#include <WiFiClientSecure.h> 

// Constants
#define SENSOR_ID 2
#define MAX_BRIGHTNESS 255
#define ONE_WIRE_BUS 19
#define HEART_RATE_OXYGEN_SENSOR_BUFFER 100
#define RETAIN_MQTT_MESSAGES false
#define QOS 1
#define DUPLICATE_MQTT_MESSAGES false

// Wi-Fi credentials
const char* ssid = "WIFI_NAME";
const char* password = "WIFI_PASSWORD";

// MQTT Broker
const char* mqtt_server = "0.0.0.0";
const int mqtt_port = 8883;
const char* mqtt_user = "sensor";
const char* mqtt_password = "SENSOR_PASSWORD";
const char* ca_cert = R"EOF(
-----BEGIN CERTIFICATE-----
ca_crt here
-----END CERTIFICATE-----
)EOF";

// MQTT topics
const char* oxygenTopic = "/sensor/oxygen";
const char* temperatureTopic = "/sensor/temperature";
const char* heartRateTopic = "/sensor/heart_frequency";

// MQTT client
WiFiClientSecure secureClient;
MqttClient mqttClient(secureClient);

// NTP client
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 0, 60000);

// Sensor objects
MAX30105 particleSensor;
OneWire ourWire(ONE_WIRE_BUS);
DallasTemperature temperatureSensor(&ourWire);

uint32_t irBuffer[HEART_RATE_OXYGEN_SENSOR_BUFFER];
uint32_t redBuffer[HEART_RATE_OXYGEN_SENSOR_BUFFER];
int32_t bufferLength;
int32_t spo2;
int8_t validSPO2;
int32_t heartRate;
int8_t validHeartRate;

char oxygenPayload[128];
char temperaturePayload[128];
char heartRatePayload[128];

void connectToWiFi();
void connectToMQTT();
void initializeSensors();
void readHeartRateAndOxygen();
void readTemperature();
void updateTime();
void preparePayloads(unsigned long timestamp);
void publishData();
void sendMqttMessage(const char* topic, char* payload);

void setup() {
  Serial.begin(115200);

  connectToWiFi();
  connectToMQTT();
  initializeSensors();
  timeClient.begin();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  if (!mqttClient.connected()) {
    connectToMQTT();
  }

  mqttClient.poll();

  readHeartRateAndOxygen();
  readTemperature();
  updateTime();

  unsigned long timestamp = timeClient.getEpochTime();
  preparePayloads(timestamp);
  publishData();

  delay(1000);
}

void connectToWiFi() {
  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi connected");
  Serial.println("IP address: " + WiFi.localIP().toString());
}

void connectToMQTT() {
  secureClient.setCACert(ca_cert); // Configure CA certificate
  mqttClient.setUsernamePassword(mqtt_user, mqtt_password); // Configure user and password

  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT...");
    if (mqttClient.connect(mqtt_server, mqtt_port)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.println(mqttClient.connectError());
      delay(5000);
    }
  }
}

void initializeSensors() {
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("MAX30102 not found. Restarting...");
    delay(5000);
    ESP.restart();
  }

  particleSensor.setup(50, 1, 2, 100, 69, 4096);
  Serial.println("MAX30102 initialized.");

  temperatureSensor.begin();
  Serial.println("Temperature sensor initialized.");
}

void readHeartRateAndOxygen() {
  bufferLength = HEART_RATE_OXYGEN_SENSOR_BUFFER;

  for (byte i = 0; i < bufferLength; i++) {
    while (!particleSensor.available()) {
      particleSensor.check();
    }

    redBuffer[i] = particleSensor.getRed();
    irBuffer[i] = particleSensor.getIR();
    particleSensor.nextSample();
  }

  maxim_heart_rate_and_oxygen_saturation(irBuffer, bufferLength, redBuffer, &spo2, &validSPO2, &heartRate, &validHeartRate);
}

void readTemperature() {
  temperatureSensor.requestTemperatures();
}

void updateTime() {
  timeClient.update();
}

void preparePayloads(unsigned long timestamp) {
  snprintf(oxygenPayload, sizeof(oxygenPayload), "{\"value\":%d,\"isValid\":%d,\"timestamp\":%lu,\"sensor\":%d}", spo2, validSPO2, timestamp, SENSOR_ID);
  snprintf(heartRatePayload, sizeof(heartRatePayload), "{\"value\":%d,\"isValid\":%d,\"timestamp\":%lu,\"sensor\":%d}", heartRate, validHeartRate, timestamp, SENSOR_ID);
  snprintf(temperaturePayload, sizeof(temperaturePayload), "{\"value\":%.2f,\"timestamp\":%lu,\"sensor\":%d}", temperatureSensor.getTempCByIndex(0), timestamp, SENSOR_ID);
}

void publishData() {
  sendMqttMessage(oxygenTopic, oxygenPayload);
  sendMqttMessage(temperatureTopic, temperaturePayload);
  sendMqttMessage(heartRateTopic, heartRatePayload);
}

void sendMqttMessage(const char* topic, char* payload) {
  mqttClient.beginMessage(topic, RETAIN_MQTT_MESSAGES, QOS, DUPLICATE_MQTT_MESSAGES);
  mqttClient.print(payload);
  mqttClient.endMessage();

  Serial.print("Published in: ");
  Serial.print(topic);
  Serial.print(" ");
  Serial.println(payload);
}