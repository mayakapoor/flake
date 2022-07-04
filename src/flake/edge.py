"""
The edge class represents a single relation in the network.
\param[in] type the assigned type to the edge.
\param[in] src_node the node serial of the source node of the directed edge.
\param[in] dst_node the node serial of the destination node of the directed edge.
\param[in] index the edge index which will serve to serialize it.
"""

class Edge():
    def __init__(self, type, src_node, dst_node, jiffies, index):
        self.index = index
        # edge type
        self.type = type
        # features of the edge
        self.features = None
        # source node of the edge
        self.src_node = src_node
        # dest node of the edge
        self.dst_node = dst_node
        #jiffies when captured
        self.jiffies = jiffies

    def id(self):
        return self.index

    def getJiffies(self):
        return self.jiffies

    def getType(self):
        return self.type

    def getSrcNode(self):
        return self.src_node

    def getDstNode(self):
        return self.dst_node

    def hasFeatures(self):
        return self.features != None

    def getFeatures(self):
        return self.features

    def add_features(self, features):
        self.features = features
