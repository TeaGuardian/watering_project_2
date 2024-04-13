#include <Wire.h>
#include <Servo.h>
#include <AHTxx.h>
#include <EEPROM.h>
#include <HardwareSerial.h>
#include <Adafruit_INA219.h>
#include "SparkFun_ENS160.h"

#define SERIAL_1_RX PB11
#define SERIAL_1_TX PB10
#define SERIAL_2_RX PA3
#define SERIAL_2_TX PA2

#define MOLSTURE_1 PA7
#define MOLSTURE_2 PA6
#define ANALOG_S_3 PA5
#define ANALOG_S_4 PA4
#define BUTTON_1 PA1
#define BUTTON_2 PA0
#define VALVE_1 PB12
#define VALVE_2 PB13
#define VALVE_3 PB9
#define RELE_1 PB14
#define RELE_2 PB15
#define SERVO PB8

#define LED_LOAD PA8
#define LED_DATA PA9
#define SPEAKER PA10

#define MODEL_ID 1
#define BAUD_RATE 115200
#define SETUP_DELAY 1000     // задержка между обновлением настроек зависимостей датчиков
#define LED_CLEAR_DELAY 110  // задержка между очистками светодиода 
#define DELIMITER '#'        // разделитель в строке данных
#define END_FLAG '$'         // разделитель записей

unsigned short int local_id = 0;
unsigned long last_time_1 = 0;
unsigned long last_time_2 = 0;
bool led_load_fl;
bool led_data_fl;
bool serial_switch;

/*  A5 - SCL    A4 - SDA   for i2c sensors
    - ENS160 (gas sensor)
    - AHTX (temperature and humidity sensor)
    - INA219 (dc current sensor)
    
    command code list:
    0 - reindex all
    1 - fetch all
    2 - is_exist?
    3 - get model id

    local code list:
    6 - off all load
    7  - set index
    8  - molsture_1
    9  - molsture_2
    10 - button_1
    11 - button_2
    12 - set valve_1
    13 - set valve_2
    14 - set led_load
    15 - set speaker
    16 - AQI (ens160)
    17 - eCO2 (ens160)
    18 - TVOC (ens160)
    19 - temperature (ath2x)
    20 - humidity (ath2x)
    21 - shunt_voltage (ina219)
    22 - bus_voltage (ina219)
    23 - current (ina219)
    24 - valve_3 (с поддержкой шим)
    25 - analog_sensor 3
    26 - analog sensor 4
    27 - rele 1
    28 - rele 2
    29 - servo

*/

struct Package {  // структура для обмена данными
  unsigned short int sender;
  unsigned short int target;
  bool is_com;
  char command_code;
  float data;
  unsigned short int int_data;
};

HardwareSerial serial_1(SERIAL_1_RX, SERIAL_1_TX);
HardwareSerial serial_2(SERIAL_2_RX, SERIAL_2_TX);

Servo servo_1;

SparkFun_ENS160 ens160; // датчик газа
AHTxx aht20(AHTXX_ADDRESS_X38, AHT2x_SENSOR); // датчик температуры и влажности
Adafruit_INA219 ina219; // датчик тока

void writeToEE(int address, unsigned short int value) { // запись в энергонезависимую память
  EEPROM.put(address, value);
}

unsigned short int readFromEE(int address) { // чтение энергонезависимой памяти
  unsigned short int value;
  EEPROM.get(address, value);
  return value;
}

String packageToString(const Package& pkg) { // преобразование пакета данных в строку
  String str = String(pkg.sender) + DELIMITER
              + String(pkg.target) + DELIMITER
              + String(pkg.is_com) + DELIMITER
              + String((int)pkg.command_code) + DELIMITER
              + String(pkg.data) + DELIMITER
              + String(pkg.int_data) + END_FLAG;
  return str;
}

Package stringToPackage(const String& str) { // преобразование строки в пакет данных
  Package pkg;
  int index = 0;
  pkg.sender = str.substring(index, str.indexOf(DELIMITER)).toInt();
  index = str.indexOf(DELIMITER, index) + 1;
  pkg.target = str.substring(index, str.indexOf(DELIMITER, index)).toInt();
  index = str.indexOf(DELIMITER, index) + 1;
  pkg.is_com = str.substring(index, str.indexOf(DELIMITER, index)).toInt();
  index = str.indexOf(DELIMITER, index) + 1;
  pkg.command_code = (char)str.substring(index, str.indexOf(DELIMITER, index)).toInt();
  index = str.indexOf(DELIMITER, index) + 1;
  pkg.data = str.substring(index, str.indexOf(DELIMITER, index)).toFloat();
  index = str.indexOf(DELIMITER, index) + 1;
  pkg.int_data = str.substring(index).toInt();
  return pkg;
}

void S1Send (const Package& pkg) { // функция отправки ответа первого порта
  serial_1.print(packageToString(pkg));
}

void S2Send (const Package& pkg) { // функция отправки ответа второго порта
  serial_2.print(packageToString(pkg));
}

void setup() { // настройка
  Wire.begin();
  serial_1.begin(BAUD_RATE);
  serial_2.begin(BAUD_RATE);
  pinMode(MOLSTURE_1, INPUT);
  pinMode(MOLSTURE_2, INPUT);
  pinMode(ANALOG_S_3, INPUT);
  pinMode(ANALOG_S_4, INPUT);
  pinMode(BUTTON_1, INPUT);
  pinMode(BUTTON_2, INPUT);
  pinMode(VALVE_1, OUTPUT);
  pinMode(VALVE_2, OUTPUT);
  pinMode(LED_DATA, OUTPUT);
  pinMode(LED_LOAD, OUTPUT);
  pinMode(SPEAKER, OUTPUT);
  pinMode(VALVE_3, OUTPUT);
  pinMode(RELE_1, OUTPUT);
  pinMode(RELE_2, OUTPUT);
  servo_1.attach(SERVO);

  digitalWrite(LED_DATA, HIGH);  // начинаем настройку датчиков
  if (readFromEE(1) != 0) {      // запрашиваем внутренний id модуля из памяти
    local_id = readFromEE(1);    // восстанавливаем
    tone(SPEAKER, 1600, 100);
  } else {                       // не найден!
    tone(SPEAKER, 800, 300);
  }
  bool ens = false;
  bool ath = false;
  bool ina = false;
  while (!ens || !ath || !ina) {  // ожидаем инициализацию
    led_data_fl = !led_data_fl;   // поочерёдно пытаемся запустить сенсоры сигнализируя о попытке
    digitalWrite(LED_DATA, led_data_fl ? HIGH : LOW);
    if (!ens) {ens = ens160.begin(); digitalWrite(VALVE_1, HIGH); delay(500); digitalWrite(VALVE_1, LOW);}
    if (!ath) {ath = aht20.begin(); digitalWrite(VALVE_2, HIGH); delay(500); digitalWrite(VALVE_2, LOW);}
    if (!ina) {ina = ina219.begin(); digitalWrite(VALVE_3, HIGH); delay(500); digitalWrite(VALVE_3, LOW);}
    delay(400);
  }
  
  ens160.setOperatingMode(SFE_ENS160_RESET);      // сбрасываем датчик газа
  ens160.setOperatingMode(SFE_ENS160_STANDARD);   // переводим в стандартный режим
  tone(SPEAKER, 400, 300);
  digitalWrite(LED_DATA, LOW);
}

Package buf;    // буфер для анализа команды
Package resp;   // буфер для формирования ответа


void loop() {
  if (last_time_1 > millis()) { // защита от переполнения счётчика
    last_time_1 = millis();
  }
  if (last_time_2 > millis()) { // защита от переполнения счётчика
    last_time_2 = millis();
  }
  if ((millis() - last_time_1) > SETUP_DELAY) {  //обновляем данные датчика для точных показателей
    // для повышения точности измерений важно поддерживать актуальность данных
    ens160.setTempCompensationCelsius(aht20.readTemperature());
    ens160.setRHCompensationFloat(aht20.readHumidity()); 
    analogWrite(LED_DATA, 100);
    last_time_1 = millis();
  }
  if ((millis() - last_time_2) > LED_CLEAR_DELAY) { //сбрасываем светодиод данных
    digitalWrite(LED_DATA, LOW);
    last_time_2 = millis();
  }
  String inp;
  bool catched_data = false;
  if (serial_switch) { // чтение первоо порта
    if (serial_1.available() > 0) {
      inp = serial_1.readString();
      buf = stringToPackage(inp);
      catched_data = true;
      analogWrite(LED_DATA, 400);
      }
  } else { // чтение второго порта
    if (serial_2.available() > 0) {
      inp = serial_2.readString();
      buf = stringToPackage(inp);
      catched_data = true;
      analogWrite(LED_DATA, 400);
      }
  }
  if (catched_data) {
    bool do_resp = true;
    // обработка полученной команды
    if (buf.is_com && (buf.target == local_id || buf.command_code <= 1)){ 
      // если (получена команда и (она для этого модуля или это общая команда))
      resp.sender = local_id;
      resp.target = buf.sender;
      resp.is_com = false;
      resp.command_code = buf.command_code;
      switch(buf.command_code) { // исполнение команды
        case 0:
          local_id = buf.target;
          writeToEE(1, local_id);
          buf.sender = local_id;
          buf.target = local_id + 1;
          if (!serial_switch) {
            S1Send(buf);
          } else {
            S2Send(buf);
          }
          resp.sender = local_id;
          resp.target = 0;
          break;
        case 1:
          if (!serial_switch) {
            S1Send(buf);
          } else {
            S2Send(buf);
          }
          resp.target = 0;
          break;
        case 2:
          break;
        case 3:
          resp.int_data = MODEL_ID;
          break;
        case 6:
          digitalWrite(VALVE_1, LOW);
          digitalWrite(VALVE_2, LOW);
          analogWrite(VALVE_3, 0);
          digitalWrite(RELE_1, LOW);
          digitalWrite(RELE_2, LOW);
          digitalWrite(LED_LOAD, LOW);
          digitalWrite(SPEAKER, LOW);
          break;
        case 7:
          local_id = buf.int_data;
          writeToEE(1, local_id);
          resp.sender = local_id;
          break;
        case 8:
          resp.int_data = analogRead(MOLSTURE_1);
          break;
        case 9:
          resp.int_data = analogRead(MOLSTURE_2);
          break;
        case 10:
          resp.int_data = digitalRead(BUTTON_1) ? 1 : 0;
          break;
        case 11:
          resp.int_data = digitalRead(BUTTON_2) ? 1 : 0;
          break;
        case 12:
          digitalWrite(VALVE_1, buf.int_data == 1 ? HIGH : LOW);
          break;
        case 13:
          digitalWrite(VALVE_2, buf.int_data == 1 ? HIGH : LOW);
          break;
        case 14:
          analogWrite(LED_LOAD, buf.int_data);
          break;
        case 15:
          tone(SPEAKER, buf.int_data, buf.data);
          break;
        case 16:
          resp.int_data = ens160.getAQI();
          break;
        case 17:
          resp.int_data = ens160.getECO2();
          break;
        case 18:
          resp.int_data = ens160.getTVOC();
          break;
        case 19:
          resp.data = aht20.readTemperature();
          break;
        case 20:
          resp.data = aht20.readHumidity();
          break;
        case 21:
          resp.data = ina219.getShuntVoltage_mV();
          break;
        case 22:
          resp.data = ina219.getBusVoltage_V();
          break;
        case 23:
          resp.data = ina219.getCurrent_mA();
          break;
        case 24:
          analogWrite(VALVE_3, buf.int_data);
          break;
        case 25:
          resp.int_data = analogRead(ANALOG_S_3);
          break;
        case 26:
          resp.int_data = analogRead(ANALOG_S_4);
          break;
        case 27:
          digitalWrite(RELE_1, buf.int_data == 1 ? HIGH : LOW);
          break;
        case 28:
          digitalWrite(RELE_2, buf.int_data == 1 ? HIGH : LOW);
          break;
        case 29:
          servo_1.write(buf.int_data);
          break;
        default: // если команда отсутствует - игнорировать
          do_resp = false;
          break;
      }
      if (do_resp) { // ответить на команду
        if (serial_switch) {
          S1Send(resp);
        } else {
          S2Send(resp);
        }
        digitalWrite(LED_DATA, HIGH);
      }
    } else { // передать команду дальше
      if (!serial_switch) {
        serial_1.print(inp);
        digitalWrite(LED_DATA, HIGH);
      } else {
        serial_2.print(inp);
        digitalWrite(LED_DATA, HIGH);
      }
    }
  }
  serial_switch = !serial_switch; // сменить рабочий порт
  
}
