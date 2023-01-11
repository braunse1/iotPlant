# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import adafruit_bme680
import adafruit_si1145
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO

from adafruit_seesaw.seesaw import Seesaw

# Ultraschallsensor GPIO definition
GPIO.setmode(GPIO.BCM)
GPIO_TRIGGER = 23
GPIO_ECHO = 24
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

def entfernung():
    # Trig High setzen
    GPIO.output(GPIO_TRIGGER, True)
 
    # Trig Low setzen (nach 0.01ms)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    startzeit = time.time()
    endzeit = time.time()
 
    # Start/Stop Zeit ermitteln
    while GPIO.input(GPIO_ECHO) == 0:
        startzeit = time.time()
 
    while GPIO.input(GPIO_ECHO) == 1:
        endzeit = time.time()
 
    # Vergangene Zeit
    zeitdifferenz = endzeit - startzeit
	
    # Schallgeschwindigkeit (34300 cm/s) einbeziehen
    entfernung = (zeitdifferenz * 34300) / 2
    return entfernung


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

client = mqtt.Client()
client.on_connect = on_connect
client.connect("localhost", 1883, 60)


# Create sensor object, communicating over the board's default I2C bus
i2c = board.I2C()  # uses board.SCL and board.SDA
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
ss = Seesaw(i2c, addr=0x36)
si1145 = adafruit_si1145.SI1145(i2c)

# change this to match the location's pressure (hPa) at sea level
bme680.sea_level_pressure = 1013.25

# You will usually have to add an offset to account for the temperature of
# the sensor. This is usually around 5 degrees but varies by use. Use a
# separate temperature sensor to calibrate this one.
temperature_offset = -5

while True:

    distanz = entfernung()-2

    touch = ss.moisture_read()
    temp = ss.get_temp()
    vis, ir = si1145.als

    print("\n****Ultraschall****")
    print ("Distanz = %.1f cm" % distanz)
    client.publish('ultrasonic/distance',payload=round(distanz,1), qos=0, retain=False)

    print("\n****si1145****")
    print("Visible: "+str(vis))
    client.publish('si1145/visible', payload=vis, qos=0, retain=False)
    print("Infrared: "+str(ir))
    client.publish('si1145/infrared', payload=ir, qos=0, retain=False)

    print("\n****Seesaw****")
    print("Temperature: " + str(round(temp + temperature_offset, 1)))
    client.publish('seesaw/temperature', payload=(round(temp + temperature_offset, 1)), qos=0, retain=False)
    print("Moisture: " + str(touch))
    client.publish('seesaw/moisture', payload=touch, qos=0, retain=False)

    print("\n****bme680****")
    print("Temperature: %0.1f C" % (bme680.temperature + temperature_offset))
    client.publish('bme680/temperature', payload=round(bme680.temperature + temperature_offset, 1), qos=0, retain=False)
    print("Gas: %d ohm" % bme680.gas)
    client.publish('bme680/gas', payload=round(bme680.gas), qos=0, retain=False)
    print("Humidity: %0.1f %%" % bme680.relative_humidity)
    client.publish('bme680/humidity', payload=round(bme680.relative_humidity), qos=0, retain=False)
    print("Pressure: %0.3f hPa" % bme680.pressure)
    client.publish('bme680/pressure', payload=round(bme680.pressure), qos=0, retain=False)
    print("Altitude = %0.2f meters" % bme680.altitude)
    client.publish('bme680/altitude', payload=round(bme680.altitude), qos=0, retain=False)


    print("\n---------------------------------------------------------")

    time.sleep(1)
