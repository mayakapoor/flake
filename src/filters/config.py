import configparser
import os
import sys

config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filter.ini')
config.read(config_path)

# check if the path is to a valid file
if not os.path.isfile(config_path):
    print("Invalid configuration path provided.")
    raise BadConfigError # not a standard python exception

def initFromConfig(param):
    for section in config.sections():
        if config.has_option(section, param):
            return config[section][param]
    print("Error initializing " + str(param) + "from config. Parameter not found.")
    sys.exit()
