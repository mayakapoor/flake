import paho.mqtt.client as mqtt
import sys
import subprocess
import base64
import zlib
import sqlite3
import time
from termcolor import colored

import flake.queries as queries
import flake.output as output
import flake.config as config
from flake.flake import Flake

provenance_levels = {
    1 : 'whole system',
    2 : 'HTTP server',
    3 : 'MySQL database',
    4 : 'Chrome browser',
}

def print_menu():
    for key in provenance_levels.keys():
        print(colored(str(str(key) + '--' + provenance_levels[key]), 'magenta'))

class ProvDB():
    def __init__(self, filter):
        DB_FILE = config.initFromConfig('DB_FILE')
        if DB_FILE is not None:
            self.db_file = DB_FILE
            self.client = mqtt.Client()
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

    def make_flake(self, actions):
        db_conn = sqlite3.connect(self.db_file)
        cursor = db_conn.cursor()
        sql = queries.insert_graph(actions)
        print(sql)
        cursor.execute(sql)
        db_conn.commit()
        cursor.execute(queries.get_last_row_id())
        id = cursor.fetchall()[0][0]
        cursor.close()
        return id

    #def get_flake(self, id):


    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        topic = config.initFromConfig('MQTT_TOPIC')
        if topic is not None:
            client.subscribe(topic, qos=0)
        else:
            print("MQTT topic improperly configured, exiting.")
            sys.exit()

    def on_message(self, client, userdata, msg):
        decoded_msg = zlib.decompress(base64.b64decode(msg.payload.decode('latin-1'))).decode('latin-1')
        self.filter.load_data(decoded_msg, userdata['graph'])

    def on_disconnect(self, client, userdata, rc=0):
        print("disconnected with result code "+ str(rc))
        self.client.loop_stop()

    def start_capture(self, graph, level):
        print("Connecting MQTT subscriber...")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        user = config.initFromConfig('MQTT_USERNAME')
        passwd = config.initFromConfig('MQTT_PASSWORD')
        host = config.initFromConfig('MQTT_HOST')
        port = config.initFromConfig('MQTT_PORT')

        self.client.username_pw_set(user, passwd)
        self.client.connect(host, int(port), 60)
        self.client.user_data_set({'graph': graph})
        self.client.loop_start()
        time.sleep(1)
        if level == 1:
            subprocess.run(["sudo", "camflow", "-a", "true"])
        elif level == 2:
            subprocess.run(["sudo", "camflow", "--track-file", "/opt/lampp/bin/httpd", "true"])
        elif level == 3:
            subprocess.run(["sudo", "camflow", "--track-file", "/opt/google/chrome/chrome", "true"])
            subprocess.run(["sudo", "camflow", "--track-file", "/usr/bin/chromedriver", "true"])
        elif level == 4:
            subprocess.run(["sudo", "camflow", "--track-file", "/opt/lampp/sbin/mysqld", "true"])
            subprocess.run(["sudo", "camflow", "--track-file", "/opt/lampp/bin/mysqld_safe", "true"])

    def stop_capture(self, graph, level):
        print("Stopping MQTT subscriber...")
        self.client.loop_stop()
        if level == 1:
            subprocess.run(["sudo", "camflow", "-a", "false"])
        elif level == 2:
            subprocess.run(["sudo", "camflow", "--track-file", "/opt/lampp/bin/httpd", "false"])
        elif level == 3:
            subprocess.run(["sudo", "camflow", "--track-file", "/opt/google/chrome/chrome", "false"])
            subprocess.run(["sudo", "camflow", "--track-file", "/usr/bin/chromedriver", "false"])
        elif level == 4:
            subprocess.run(["sudo", "camflow", "--track-file", "/opt/lampp/sbin/mysqld", "false"])
            subprocess.run(["sudo", "camflow", "--track-file", "/opt/lampp/bin/mysqld_safe", "false"])
        db_conn = sqlite3.connect(self.db_file)
        save = config.initFromConfig("SAVE_TO_DISK")
        if save == 'yes':
            graph.save_to_disk(db_conn)
        graph.to_png()
        graph.to_pickle()
        graph.to_file()
        graph.to_edge_type_dictionary()
        graph.to_node_type_dictionary()
        graph.to_json()
