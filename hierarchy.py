import os, copy
from collections import defaultdict
import networkx as nx

class Hierarchy(object):
    def __init__(self, name):
        self.name = name
        self.clique = set()
        self.high = set()
        self.low = set()
        self.stub = set()
        self.graph = nx.Graph()

        self.provider = defaultdict(set)
        self.customer = defaultdict(set)
        self.peer = defaultdict(set)

        self.get_rel()
        self.cal_hierarchy()

    def get_rel(self):
        with open(self.name) as f:
            for line in f:
                if not line.startswith('#'):
                    [asn1, asn2, rel] = line.strip().split('|')[:3]
                    self.graph.add_edge(asn1, asn2)
                    if rel == '-1':
                        self.customer[asn1].add(asn2)
                        self.provider[asn2].add(asn1)
                    elif rel == '0' or rel == '1':
                        self.peer[asn1].add(asn2)
                        self.peer[asn2].add(asn1)

    def cal_hierarchy(self):
        self.clique = set(['174', '209', '286', '701', '1239', '1299', '2828', '2914', '3257', '3320', '3356', '3491', '5511', '6453', '6461', '6762', '6830', '7018', '12956'])
        allNodes = set()
        for node in self.clique:
            for cus in self.customer[node]:
                if self.graph.degree(cus) > 100:
                    self.high.add(cus)
                    allNodes.add(cus)
            allNodes.add(node)
        for node in self.graph.nodes():
            if node in allNodes:
                continue
            if not self.customer[node]:
                self.stub.add(node)
            else:
                self.low.add(node)
            allNodes.add(node)

    def get_hierarchy(self, AS):
        if AS in self.clique:
            return 0
        if AS in self.high:
            return 1
        if AS in self.low:
            return 2
        if AS in self.stub:
            return 3
        return -1