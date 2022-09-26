import os
import json

import dgl
import networkx as nx
from collections import defaultdict

from . import flake
from . import config

#######################
#        helpers      #
#######################
def one_hot_encode(idx, len):
    ret = [0] * len
    ret[idx] = 1
    return ret

#######################
#    output funcs     #
#######################

def print_flake_info(G, id):
    print("Statistics for graph: " + str(id))
    print("Actions taken: " + ",".join(G.getActions()))
    print("number of nodes: " + str(G.num_nodes()))
    print("number of node types: " + str(G.num_node_types()))
    for type in G.nodetypes:
        print(type + " - " + str(len(G.nodetypes[type])))
    print("number of edges: " + str(G.num_edges()))
    print("number of edge types: " + str(G.num_edge_types()))
    for type in G.edgetypes:
        print(type + " - " + str(len(G.edgetypes[type])))
    print("number of distinct edge schemas: " + str(G.num_schemas()))
    for schema in G.get_schemas():
        print(schema)

# make a graph with whatever has been loaded into our storage.
def flake_to_networkx_graph_with_attributes(G):
    print("Making NetworkX Graph...")
    nxG = nx.MultiDiGraph()
    nxG.add_nodes_from(G.get_nodes_with_attributes())
    nxG.add_edges_from(G.get_edges_with_attributes())
    print("Graph constructed.")
    return nxG

def flake_to_networkx_graph(G):
    print("Making NetworkX Graph...")
    nxG = nx.MultiDiGraph()
    nxG.add_nodes_from(G.get_nodes_for_networkx())
    nxG.add_edges_from(G.get_edges_for_networkx())
    print("Graph constructed.")
    return nxG

def flake_to_dgl_graph(G):
    print("Making DGL Graph...")
    DG = dgl.graph(G.get_graph_dictionary(), idtype=int)
    print("Graph constructed.")
    return DG

def flake_to_labeled_networkx_graph(G):
    print("Making NetworkX Graph...")
    nxG = nx.DiGraph()
    nxG.add_nodes_from(G.get_nodes_for_networkx())
    nxG.add_edges_from(G.get_edges_for_networkx())
    nx.draw_networkx_labels(nxG, pos=nx.spring_layout(nxG), labels=G.get_nodes_with_types())
    nx.draw_networkx_edge_labels(nxG, pos=nx.spring_layout(nxG), edge_labels=G.get_edges_with_types())
    print("Graph constructed.")
    return nxG

# serialize the graph with a default path name.
def flake_to_pickle(G):
    print("converting graph to pickle...")
    OUTPUT_DIR = str(os.getcwd()) + "/" + config.initFromConfig('OUTPUT_DIR')
    out = OUTPUT_DIR + "/graph{}/graph{}.gpickle".format(str(G.getIndex()), str(G.getIndex()))
    NG = flake_to_networkx_graph(G)
    nx.write_gpickle(NG, out)
    print("Graph pickle outputted to " + out + ".")

def flake_to_png(G):
    NG = nx.DiGraph()
    NG.add_nodes_from(G.get_nodes_for_networkx())
    reNG = nx.relabel_nodes(NG, G.get_nodes_with_types())
    for edge in G.get_edges():
        reNG.add_edge(edge.getSrcNode().getType(), edge.getDstNode().getType(), label=edge.getType(), data=edge.getType())
    print("Drawing graph...")
    OUTPUT_DIR = str(os.getcwd()) + "/" + config.initFromConfig('OUTPUT_DIR')
    out = OUTPUT_DIR + "/graph{}".format(str(G.getIndex()))
    if not os.path.exists(out):
        os.makedirs(out)
    out += "/graph{}.png".format(str(G.getIndex()))

    A = nx.nx_agraph.to_agraph(reNG)
    A.draw(out, format="png", prog="dot", args="-Goverlap=scale -Efont_size=8")
    print("Graph drawn to " + out + ".")

#output a JSON-formatted dictionary where key = node type, value = list of nodes
def encoded_node_types(G):
    print("outputting node types to JSON format...")
    type_dict = {}
    types = list(G.nodetypes.keys())
    for node in G.nodes:
        type_dict[G.nodes[node].id()] = one_hot_encode(types.index(G.nodes[node].getType()), len(types))
    OUTPUT_DIR = str(os.getcwd()) + "/" + config.initFromConfig('OUTPUT_DIR')
    out = OUTPUT_DIR + "/graph{}".format(str(G.getIndex()))
    if not os.path.exists(out):
        os.makedirs(out)
    out += "/nodetypes{}.json".format(str(G.getIndex()), str(G.getIndex()))
    with open(f'{out}', 'w') as f:
        f.write(str(types))
        json.dump(type_dict, f, indent=2)
    print("Node types outputted to " + out + ".")


#output a JSON-formatted dictionary where key = edge type, value = list of nodes
def encoded_edge_types(G):
    print("outputting edge types to JSON format...")
    type_dict = {}
    types = list(G.edgetypes.keys())
    for edge in G.edges:
        type_dict[G.edges[edge].id()] = one_hot_encode(types.index(G.edges[edge].getType()), len(types))

    OUTPUT_DIR = str(os.getcwd()) + "/" + config.initFromConfig('OUTPUT_DIR')
    out = OUTPUT_DIR + "/graph{}".format(str(G.getIndex()))
    if not os.path.exists(out):
        os.makedirs(out)
    out += "/edgetypes{}.json".format(str(G.getIndex()), str(G.getIndex()))
    with open(f'{out}', 'w') as f:
        f.write(str(types))
        json.dump(type_dict, f, indent=2)
    print("Edge types outputted to " + out + ".")

#return a python dictionary of the graph
def flake_to_dictionary(G):
    return G.get_graph_dictionary()

# output a JSON-formatted dictionary where key = edge_schema, value = src node list and dest node list where src[i]-edge-dest[i]
def flake_to_json(G):
    print("outputting graph to JSON format...")
    output_dict = G.get_graph_dictionary()
    OUTPUT_DIR = str(os.getcwd()) + "/" + config.initFromConfig('OUTPUT_DIR')
    out = OUTPUT_DIR + "/graph{}".format(str(G.getIndex()))
    if not os.path.exists(out):
        os.makedirs(out)
    out += "/graph{}.json".format(str(G.getIndex()), str(G.getIndex()))
    with open(f'{out}', 'w') as f:
        json.dump(output_dict, f)
    print("Graph outputted to " + out + ".")

# print graph info to a file
def flake_info_to_file(G):
    OUTPUT_DIR = str(os.getcwd()) + "/" + config.initFromConfig('OUTPUT_DIR')
    out = OUTPUT_DIR + "/graph{}".format(str(G.getIndex()))
    if not os.path.exists(out):
        os.makedirs(out)
    out += "/stats{}.txt".format(str(G.getIndex()), str(G.getIndex()))
    with open(f'{out}', 'w') as f:
        f.write("Statistics for graph: " + str(G.getIndex()) + "\n")
        f.write("Actions taken: " + ",".join(G.getActions()))
        f.write("number of nodes: " + str(G.num_nodes()) + "\n")
        f.write("number of node types: " + str(G.num_node_types()) + "\n")
        for type in G.nodetypes:
            f.write(type + " - " + str(len(G.nodetypes[type])) + "\n")
        f.write("number of edges: " + str(G.num_edges()) + "\n")
        f.write("number of edge types: " + str(G.num_edge_types()) + "\n")
        for type in G.edgetypes:
            f.write(type + " - " + str(len(G.edgetypes[type])) + "\n")
        f.write("number of distinct edge schemas: " + str(G.num_schemas()) + "\n")
        for schema in G.get_schemas():
            str_schema = '-'.join(schema)
            f.write(str(str_schema) + " - " + str(len(G.schemas[schema])) + "\n")
