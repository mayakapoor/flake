import time
import os
import json
import dgl
import sqlite3
import networkx as nx
from collections import defaultdict

from . import config as cfg
from . import queries
from . import node
from . import edge

"""
Helper function to return a one-hot encoded vector
"""
def one_hot_encode(idx, len):
    ret = [0] * len
    ret[idx] = 1
    return ret

"""
This class represents an internal graph of Nodes and Edges
"""
class Snowflake():
    def __init__(self, id):
        # graph id
        self.id = id
        # descriptive list of the actions performed
        self.actions = ""
        # node serial to Node object
        self.nodes = defaultdict()
        # edge serial to Edge object
        self.edges = defaultdict()
        # type schema (nt-et-nt), to list of node index tuples (src,dst)
        self.schemas = defaultdict(list)
        self.nodetypes = defaultdict(list)
        self.edgetypes = defaultdict(list)

    def getIndex(self):
        return self.id

    def getActions(self):
        return self.actions

    def num_nodes(self):
        return len(self.nodes)

    def num_edges(self):
        return len(self.edges)

    def num_node_types(self):
        return len(self.nodetypes)

    def num_edge_types(self):
        return len(self.edgetypes)

    def num_schemas(self):
        return len(self.schemas)

    def num_nodes_of_type(self, type):
        if type in self.nodetypes:
            return len(self.nodetypes[type])
        return 0

    def num_edges_of_type(self, type):
        if type in self.edgetypes:
            return len(self.edgetypes[type])
        return 0

    def num_edges_of_schema(self, schema):
        if schema in self.schemas:
            return len(self.schemas[schema])
        return 0

    #returns list of node ids
    def get_nodes_for_networkx(self):
        node_list = []
        for node in self.nodes:
            node_list.append(int(self.nodes[node].id()))
        return node_list

    def get_node_types(self):
        return self.nodetypes

    def get_nodes_with_types(self):
        node_dict = {}
        for node in self.nodes:
            node_dict[int(self.nodes[node].id())] = self.nodes[node].getType()
        return node_dict

    def get_nodes_encoded(self):
        type_dict = {}
        types = list(self.nodetypes.keys())
        for node in self.nodes:
            type_dict[self.nodes[node].id()] = one_hot_encode(types.index(self.nodes[node].getType()), len(types))
        return type_dict

    def get_nodes_with_attributes(self):
        node_list = []
        for node in self.nodes:
            node_list.append((self.nodes[node].id(), self.nodes[node].getFeatures()))
        return node_list

    def get_edges(self):
        edge_list = []
        for edge in self.edges:
            edge_list.append(self.edges[edge])
        return edge_list

    def get_edges_for_networkx(self):
        edge_list = []
        for edge in self.edges:
            edge_list.append((int(self.edges[edge].getSrcNode().id()),
                              int(self.edges[edge].getDstNode().id())))
        return edge_list

    def get_edges_with_types(self):
        edge_dict = {}
        for edge in self.edges:
            edge_dict[(int(self.edges[edge].getSrcNode().id()),
                       int(self.edges[edge].getDstNode().id()))] = self.edges[edge].getType()
        return edge_dict

    def get_edges_encoded(self):
        type_dict = {}
        types = list(self.edgetypes.keys())
        for edge in self.edges:
            type_dict[self.edges[edge].id()] = one_hot_encode(types.index(self.edges[edge].getType()), len(types))
        return type_dict

    def get_edges_with_attributes(self):
        edge_list = []
        for edge in self.edges:
            edge_list.append((int(self.edges[edge].getSrcNode().id()),
                              int(self.edges[edge].getDstNode().id()),
                              self.edges[edge].getFeatures()))
        return edge_list

    def get_schemas(self):
        return list(self.schemas.keys())

    def get_schema_node_lists(self, schema):
        return list(map(list, zip(*self.schemas[schema])))

    def get_graph_dictionary(self):
        output_dict = defaultdict(list)
        for schema in self.get_schemas():
            str_schema = '-'.join(schema)
            src_dst = self.get_schema_node_lists(schema)
            output_dict[str_schema] = (src_dst[0], src_dst[1])
        return output_dict

    def add_action(self, action):
        if self.actions != "":
            self.actions += ", "
        self.actions += action

    def add_node(self, type):
        id = len(self.nodes)
        self.nodes[id] = node.Node(type, id)
        self.nodetypes[type].append(id)
        return id

    def add_node(self, type, features):
        id = len(self.nodes)
        self.nodes[id] = node.Node(type, id)
        self.nodetypes[type].append(id)
        self.nodes[id].add_features(features)
        return id

    def add_edge(self, type, src_node, dst_node, jiffies):
        id = len(self.edges)
        self.edges[id] = edge.Edge(type, self.nodes[src_node], self.nodes[dst_node], jiffies, id)
        self.edgetypes[type].append(id)
        return id

    def add_edge(self, type, src_node, dst_node, features, jiffies):
        id = len(self.edges)
        self.edges[id] = edge.Edge(type, self.nodes[src_node], self.nodes[dst_node], jiffies, id)
        self.edgetypes[type].append(id)
        self.edges[id].add_features(features)
        # add edge schema
        self.schemas[(self.nodes[src_node].getType(),
            type,
            self.nodes[dst_node].getType())].append((self.nodes[src_node].id(),
            self.nodes[dst_node].id()))
        return id

    def save_to_disk(self, db_file):
        db = sqlite3.connect(db_file)
        print("Saving flake to database...")
        cursor = db.cursor()
        for type in self.nodetypes.keys():
            sql = queries.insert_type(type)
            cursor.execute(sql)
        for type in self.edgetypes.keys():
            sql = queries.insert_type(type)
            cursor.execute(sql)
        db.commit()
        print("graph ID: " + str(self.id))

        edgefeatures = []
        #cursor.execute("BEGIN TRANSACTION;")
        for edge in self.edges:
            sql = queries.get_type_index(self.edges[edge].getSrcNode().getType())
            cursor.execute(sql)
            src_node_type_id = cursor.fetchone()[0]
            sql = queries.insert_node(src_node_type_id, self.getIndex())
            cursor.execute(sql)
            cursor.execute(queries.get_last_row_id())
            src_node_id = cursor.fetchone()[0]
            sql = queries.get_type_index(self.edges[edge].getDstNode().getType())
            cursor.execute(sql)
            dst_node_type_id = cursor.fetchone()[0]
            sql = queries.insert_node(dst_node_type_id, self.getIndex())
            cursor.execute(sql)
            cursor.execute(queries.get_last_row_id())
            dst_node_id = cursor.fetchone()[0]
            sql = queries.get_type_index(self.edges[edge].getType())
            cursor.execute(sql)
            edge_type_id = cursor.fetchone()[0]

            sql = queries.insert_edge(self.getIndex(),
                edge_type_id,
                src_node_id,
                dst_node_id,
                self.edges[edge].getJiffies())
            cursor.execute(sql)
        db.commit()
        cursor.close()
        print("Graph {} saved.".format(self.id))

    def clear(self):
        self.nodes = defaultdict()
        self.edges = defaultdict()
        self.schemas = defaultdict(list)
        self.nodetypes = defaultdict(list)
        self.edgetypes = defaultdict(list)

##########################
#    Output functions    #
##########################

    def print_info(self):
        print("Statistics for graph: " + str(self.id))
        print("Actions taken: " + str(",".join(self.getActions())))
        print("number of nodes: " + str(self.num_nodes()))
        print("number of node types: " + str(self.num_node_types()))
        for type in self.nodetypes:
            print(type + " - " + str(len(self.nodetypes[type])))
        print("number of edges: " + str(self.num_edges()))
        print("number of edge types: " + str(self.num_edge_types()))
        for type in self.edgetypes:
            print(type + " - " + str(len(self.edgetypes[type])))
        print("number of distinct edge schemas: " + str(self.num_schemas()))
        for schema in self.get_schemas():
            print(schema)

    def to_networkx_graph(self):
        print("Making NetworkX Graph...")
        nxG = nx.MultiDiGraph()
        nxG.add_nodes_from(self.get_nodes_for_networkx())
        nxG.add_edges_from(self.get_edges_for_networkx())
        print("Graph constructed.")
        return nxG

    # make a graph with whatever has been loaded into our storage.
    def to_networkx_graph_with_attributes(self):
        print("Making NetworkX Graph...")
        nxG = nx.MultiDiGraph()
        nxG.add_nodes_from(self.get_nodes_with_attributes())
        nxG.add_edges_from(self.get_edges_with_attributes())
        print("Graph constructed.")
        return nxG

    def to_networkx_graph_with_labels(self):
        print("Making NetworkX Graph...")
        nxG = nx.DiGraph()
        nxG.add_nodes_from(self.get_nodes_for_networkx())
        nxG.add_edges_from(self.get_edges_for_networkx())
        nx.draw_networkx_labels(nxG, pos=nx.spring_layout(nxG), labels=self.get_nodes_with_types())
        nx.draw_networkx_edge_labels(nxG, pos=nx.spring_layout(nxG), edge_labels=self.get_edges_with_types())
        print("Graph constructed.")
        return nxG

    def to_dgl_graph(self):
        print("Making DGL Graph...")
        DG = dgl.graph(self.get_graph_dictionary(), idtype=int)
        print("Graph constructed.")
        return DG

    def to_dictionary(self):
        return self.get_graph_dictionary()

    def to_json(self):
        print("outputting graph to JSON format...")
        output_dict = self.get_graph_dictionary()
        OUTPUT_DIR = cfg.initFromConfig('OUTPUT_DIR')
        out = OUTPUT_DIR + "/graph{}".format(str(self.getIndex()))
        if not os.path.exists(out):
            os.makedirs(out)
        out += "/graph{}.json".format(str(self.getIndex()), str(self.getIndex()))
        with open(f'{out}', 'w') as f:
            json.dump(output_dict, f)
        print("Graph outputted to " + out + ".")

    def to_file(self):
        OUTPUT_DIR = cfg.initFromConfig('OUTPUT_DIR')
        out = OUTPUT_DIR + "/graph{}".format(str(self.getIndex()))
        if not os.path.exists(out):
            os.makedirs(out)
        out += "/stats{}.txt".format(str(self.getIndex()), str(self.getIndex()))
        with open(f'{out}', 'w') as f:
            f.write("Statistics for graph: " + str(self.getIndex()) + "\n")
            f.write("Actions taken: " + ",".join(self.getActions()) + "\n")
            f.write("number of nodes: " + str(self.num_nodes()) + "\n")
            f.write("number of node types: " + str(self.num_node_types()) + "\n")
            for type in self.nodetypes:
                f.write(type + " - " + str(len(self.nodetypes[type])) + "\n")
            f.write("number of edges: " + str(self.num_edges()) + "\n")
            f.write("number of edge types: " + str(self.num_edge_types()) + "\n")
            for type in self.edgetypes:
                f.write(type + " - " + str(len(self.edgetypes[type])) + "\n")
            f.write("number of distinct edge schemas: " + str(self.num_schemas()) + "\n")
            for schema in self.get_schemas():
                str_schema = '-'.join(schema)
                f.write(str(str_schema) + " - " + str(len(self.schemas[schema])) + "\n")

    def to_pickle(self):
        print("converting graph to pickle...")
        OUTPUT_DIR = cfg.initFromConfig('OUTPUT_DIR')
        out = OUTPUT_DIR + "/graph{}".format(str(self.getIndex()))
        if not os.path.exists(out):
            os.makedirs(out)
        out += "/graph{}.gpickle".format(str(self.getIndex()), str(self.getIndex()))
        NG = self.to_networkx_graph()
        nx.write_gpickle(NG, out)
        print("Graph pickle outputted to " + out + ".")

    def to_png(self):
        NG = nx.DiGraph()
        NG.add_nodes_from(self.get_nodes_for_networkx())
        reNG = nx.relabel_nodes(NG, self.get_nodes_with_types())
        for edge in self.get_edges():
            reNG.add_edge(edge.getSrcNode().getType(), edge.getDstNode().getType(), label=edge.getType(), data=edge.getType())
        print("Drawing graph...")
        OUTPUT_DIR = cfg.initFromConfig('OUTPUT_DIR')
        out = OUTPUT_DIR + "/graph{}".format(str(self.getIndex()))
        if not os.path.exists(out):
            os.makedirs(out)
        out += "/graph{}.png".format(str(self.getIndex()))

        A = nx.nx_agraph.to_agraph(reNG)
        A.draw(out, format="png", prog="dot", args="-Goverlap=scale -Efont_size=8")
        print("Graph drawn to " + out + ".")

    def to_edge_type_dictionary(self):
        print("outputting one-hot encoded edge types to JSON format...")
        types = list(self.edgetypes.keys())
        OUTPUT_DIR = cfg.initFromConfig('OUTPUT_DIR')
        out = OUTPUT_DIR + "/graph{}".format(str(self.getIndex()))
        if not os.path.exists(out):
            os.makedirs(out)
        out += "/edgetypes{}.json".format(str(self.getIndex()), str(self.getIndex()))
        with open(f'{out}', 'w') as f:
            f.write(str(types))
            json.dump(self.get_edges_encoded(), f, indent=2)
        print("Edge types outputted to " + out + ".")

    def to_node_type_dictionary(self):
        print("outputting one-hot encoded node types to JSON format...")
        types = list(self.nodetypes.keys())
        OUTPUT_DIR = cfg.initFromConfig('OUTPUT_DIR')
        out = OUTPUT_DIR + "/graph{}".format(str(self.getIndex()))
        if not os.path.exists(out):
            os.makedirs(out)
        out += "/nodetypes{}.json".format(str(self.getIndex()), str(self.getIndex()))
        with open(f'{out}', 'w') as f:
            f.write(str(types))
            json.dump(self.get_nodes_encoded(), f, indent=2)
        print("Node types outputted to " + out + ".")
