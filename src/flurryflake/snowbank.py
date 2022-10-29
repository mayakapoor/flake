import paho.mqtt.client as mqtt
import sys
import os
import subprocess
import base64
import zlib
import sqlite3
import time
from termcolor import colored

from . import config
from . import queries
from . import flake
from . import client

class Snowbank():
    def __init__(self, filter):
        DB_FILE = str(os.getcwd() + "/" + str(config.initFromConfig('DB_FILE')))
        if DB_FILE is not None:
            self.db_file = DB_FILE
            self.client = client.MQTTClient()
            db_conn = sqlite3.connect(self.db_file)
            cursor = db_conn.cursor()
            cursor.execute(queries.create_type_table())
            cursor.execute(queries.create_node_table())
            cursor.execute(queries.create_edge_table())
            cursor.execute(queries.create_graph_table())
            db_conn.commit()
            cursor.close()
        else:
            print("Could not find database file from configuration.")
            sys.exit()
        self.filter = filter
        self.flakes = {}

    def getFlake(self, id):
        return self.flakes[id]

    def collect_flake(self, action):
        db = sqlite3.connect(self.db_file)
        cursor = db.cursor()
        sql = queries.insert_graph(action)
        cursor.execute(sql)
        db.commit()
        cursor.execute(queries.get_last_row_id())
        id = cursor.fetchall()[0][0]
        currFlake = flake.Snowflake(id)
        self.client.client.user_data_set({'graph': currFlake})
        self.flakes[id] = currFlake
        return id

    def finalize(self, id):
        db_conn = sqlite3.connect(self.db_file)
        save = config.initFromConfig("SAVE_TO_DISK")
        if save == 'yes':
            if id in self.flakes:
                self.flakes[id].save_to_disk(self.db_file)
            else:
                print("ERROR: Flake not found")
        db_conn.commit()

    def on_message(self, client, userdata, msg):
        decoded_msg = zlib.decompress(base64.b64decode(msg.payload.decode('latin-1'))).decode('latin-1')
        self.filter.load_data(decoded_msg, userdata['graph'])

    def connect_client(self):
        topic = config.initFromConfig('MQTT_TOPIC')
        user = config.initFromConfig('MQTT_USERNAME')
        passwd = config.initFromConfig('MQTT_PASSWORD')
        host = config.initFromConfig('MQTT_HOST')
        port = config.initFromConfig('MQTT_PORT')
        camflow = config.initFromConfig('CAMFLOW_TOPIC')
        self.client.connect_client(user, passwd, host, port, self.on_message)
        self.client.subscribe(camflow)
        self.client.subscribe(topic)

    def disconnect_client(self):
        self.client.disconnect_client()
