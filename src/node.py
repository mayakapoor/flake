
"""
The node class represents a single vertex in the network.
\param[in] type the assigned type to the node.
\param[in] index the node index which will serve to serialize it.
"""
class Node():
    def __init__(self, type, index):
        self.index = index
        # node type
        self.type = type
        # features of the node
        self.features = None

    def id(self):
        return self.index

    def getType(self):
        return self.type

    def hasFeatures(self):
        return self.features != None

    def getFeatures(self):
        return self.features

    def add_features(self, features):
        self.features = features
