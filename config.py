import configparser
import os
import sys

config = configparser.ConfigParser()
config.read('/etc/flake.ini')

def initFromConfig(param):
    for section in config.sections():
        if config.has_option(section, param):
            return config[section][param]
    print("Error initializing " + str(param) + "from config. Parameter not found.")
    sys.exit()

OUTPUT_DIR = config['DEFAULT']['OUTPUT_DIR']
INPUT_DIR = config['DEFAULT']['INPUT_DIR']

# MQTT/DB subscriber setting
MQTT_USERNAME = config['MQTT']['MQTT_USERNAME']
MQTT_PASSWORD = config['MQTT']['MQTT_USERNAME']
MQTT_HOST = config['MQTT']['MQTT_HOST']
MQTT_PORT = config['MQTT']['MQTT_PORT']
MQTT_TOPIC = config['MQTT']['MQTT_TOPIC']
