import paho.mqtt.client as mqtt
import sys
import os
import subprocess
import base64
import zlib
import sqlite3
import time
from termcolor import colored

class MQTTClient():
    def __init__(self):
        self.client = mqtt.Client()
        self.topics = []

    def publish(self, topic, msg):
        self.client.publish(topic, bytes(zlib.compress(bytes(msg, 'utf-8'))))

    def subscribe(self, topic):
        if topic is not None:
            self.client.subscribe(topic, qos=0)
        else:
            print("MQTT topic improperly configured, exiting.")
            sys.exit()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))

    def on_disconnect(self, client, userdata, rc=0):
        print("disconnected with result code "+ str(rc))
        self.client.loop_stop()

    def connect_client(self, user, passwd, host, port, on_message):
        print("Connecting MQTT subscriber...")
        self.client.on_connect = self.on_connect
        self.client.on_message = on_message
        self.client.on_disconnect = self.on_disconnect

        self.client.username_pw_set(user, passwd)
        self.client.connect(host, int(port), 60)
        self.client.loop_start()
        time.sleep(1)

    def disconnect_client(self):
        print("Stopping MQTT subscriber...")
        self.client.loop_stop()
