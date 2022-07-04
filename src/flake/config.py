import configparser
import os
import sys

configp = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flake.ini')
configp.read(config_path)

# check if the path is to a valid file
if not os.path.isfile(config_path):
    print("Invalid configuration path provided.")
    raise BadConfigError # not a standard python exception

def initFromConfig(param):
    for section in configp.sections():
        if configp.has_option(section, param):
            return configp[section][param]
    print("Error initializing " + str(param) + "from config. Parameter not found.")
    sys.exit()

OUTPUT_DIR = configp['DEFAULT']['OUTPUT_DIR']
INPUT_DIR = configp['DEFAULT']['INPUT_DIR']

# MQTT/DB subscriber setting
MQTT_USERNAME = configp['MQTT']['MQTT_USERNAME']
MQTT_PASSWORD = configp['MQTT']['MQTT_USERNAME']
MQTT_HOST = configp['MQTT']['MQTT_HOST']
MQTT_PORT = configp['MQTT']['MQTT_PORT']
MQTT_TOPIC = configp['MQTT']['MQTT_TOPIC']
