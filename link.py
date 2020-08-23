import numpy as np
import networkx as nx
import os, copy, math, operator, random, json, scipy, sqlite3, resource
from collections import defaultdict
from itertools import permutations
from hierarchy import Hierarchy
resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))

class Links(object):
    def __init__(self, dir_name, org_name, peering_name):
        self.dir = dir_name
        self.org_name = org_name
        self.peering_name = peering_name
        self.prob = dict()
        self.init_prob = dict()
        self.siblings = set()
        self.edge_infer = set()
        self.edge_finish = set()

        self.provider = defaultdict(set)
        self.peer = defaultdict(set)
        self.customer = defaultdict(set)

        self.tripletRel = dict()
        self.nonpath = dict()
        self.distance2Clique = dict()
        self.vp = dict()
        self.ixp = defaultdict(int)
        self.facility = defaultdict(int)
        self.prevlink = defaultdict(set)
        self.adjanceTypeRatio = dict()
        self.degreeRatio = dict()
        self.vppos = dict()
        self.tier = Hierarchy(self.dir + 'asrel_prime_prob.txt')

        self.ingestProb()
        self.extractSiblings()

    def ingestProb(self):
        self.edge_finish = set()
        with open(self.dir + 'asrel_prime_prime.txt') as f:
            for line in f:
                if not line.startswith('#'):
                    [asn1, asn2, rel] = line.strip().split('|')
                    self.edge_finish.add((asn1, asn2))
                    self.edge_finish.add((asn2, asn1))

        with open(self.dir + 'asrel_prime_prob.txt') as f:
            for line in f:
                if not line.startswith('#'):
                    [asn1, asn2, rel, p2p, p2c, c2p] = line.strip().split('|')[:6]
                    a, b, c = random.uniform(1e-5, 1e-3), random.uniform(1e-5, 1e-3), random.uniform(1e-5, 1e-3)
                    self.init_prob[(asn1, asn2)] = (float(p2p)+a, float(p2c)+b, float(c2p)+c)
                    self.init_prob[(asn2, asn1)] = (float(p2p)+a, float(c2p)+c, float(p2c)+b)
                    if (asn1, asn2) not in self.edge_finish:
                        self.edge_infer.add((asn1, asn2))
                        self.edge_infer.add((asn2, asn1))
                    if rel == '0':
                        self.prob[(asn1, asn2)] = (1.0, 0.0, 0.0)
                        self.prob[(asn2, asn1)] = (1.0, 0.0, 0.0)
                        self.peer[asn1].add(asn2)
                        self.peer[asn2].add(asn1)
                    elif rel == '-1':
                        self.prob[(asn1, asn2)] = (0.0, 1.0, 0.0)
                        self.prob[(asn2, asn1)] = (0.0, 0.0, 1.0)
                        self.customer[asn1].add(asn2)
                        self.provider[asn2].add(asn1)
    
    def parseBGPPaths(self):
        forwardPath, reversePath = set(), set()
        with open('aspaths.txt') as f:
            for line in f:
                if line.strip() == '':
                    continue
                path = line.strip().split("|")
                forwardPath.add("|".join(path))
                reversePath.add("|".join(path[::-1]))
        return forwardPath, reversePath

    def getEdgeClass(self):
        forwardPath, reversePath = self.parseBGPPaths()
        edge2VP = defaultdict(list)
        tripletRel = defaultdict(lambda: [[0 for x in range(4)] for y in range(4)])
        for path in (forwardPath | reversePath):
            flag = 1
            ASes = path.split('|')
            for i in range(len(ASes) - 1):
                if (ASes[i], ASes[i+1]) not in self.prob:
                    flag = 0
            if flag == 1:
                linkList = ['NULL']
                for i in range(len(ASes) - 1):
                    linkList.append((ASes[i], ASes[i+1]))
                linkList.append('NULL')
                
                for i in range(1, len(linkList)-1):
                    prevRel = self.getEdgeRelationship(linkList[i-1])
                    nextRel = self.getEdgeRelationship(linkList[i+1])
                    tripletRel[linkList[i]][prevRel][nextRel] += 1
                    if path in forwardPath:
                        edge2VP[linkList[i]].append(ASes[0])
                    
        for edge in self.prob:
            if edge in edge2VP:
                self.vp[edge] = len(set(edge2VP[edge]))
                tmp = [0, 0, 0, 0]
                for obvp in edge2VP[edge]:
                    tmp[self.tier.get_hierarchy(obvp)] += 1
                vps = sum(tmp)
                for i in range(4):
                    tmp[i] = round(tmp[i]/vps/0.1)
                self.vppos[edge] = copy.deepcopy(tmp)
            else:
                self.vp[edge] = 0
                self.vppos[edge] = [0, 0, 0, 0]
        
        for edge in self.prob:
            trs = float(np.array(tripletRel[edge]).sum())
            tmp = list()
            for i in range(4):
                for j in range(4):
                    tripletRel[edge][i][j] = round(tripletRel[edge][i][j]/trs/0.1)
                    tmp.append(tripletRel[edge][i][j])
            self.tripletRel[edge] = copy.deepcopy(tmp)
    
    def getEdgeRelationship(self, edge):
        if edge == 'NULL':
            return 0
        asn1, asn2 = edge
        if asn1 in self.customer[asn2]:
            return 1
        if asn1 in self.peer[asn2]:
            return 2
        if asn1 in self.provider[asn2]:
            return 3
    
    def extractSiblings(self):
        formatCounter = 0
        orgAsn = defaultdict(list)
        with open(self.org_name) as f:
            for line in f:
                if formatCounter == 2:
                    asn = line.split('|')[0]
                    orgId = line.split('|')[3]
                    orgAsn[orgId].append(asn)
                if line.startswith("# format"):
                    formatCounter += 1
        for _, v in orgAsn.items():
            siblingPerm = permutations(v, 2)
            for i in siblingPerm:
                self.siblings.add(i)

    def assignNonpath(self):
        for link in self.prob:
            PCPP = len(self.peer[link[0]]) + len(self.provider[link[0]])
            prevLink = 0
            for i in range(4):
                prevLink += self.tripletRel[link][8+i]
                prevLink += self.tripletRel[link][12+i]
            if PCPP > 0 and prevLink == 0:
                self.nonpath[link] = PCPP
            else:
                self.nonpath[link] = 0

    def assignIXPFacility(self):
        ixp_dict = {}
        facility_dict = {}

        if self.peering_name.endswith('json'):
            with open(self.peering_name) as f:
                data = json.load(f)
            for i in data['netixlan']['data']:
                AS, ixp = i['asn'], i['ixlan_id']
                if ixp not in ixp_dict:
                    ixp_dict[ixp] = [AS]
                else:
                    ixp_dict[ixp].append(AS)
            for i in data['netfac']['data']:
                AS, facility = i['local_asn'], i['fac_id']
                if facility not in facility_dict:
                    facility_dict[facility] = [AS]
                else:
                    facility_dict[facility].append(AS)

        elif self.peering_name.endswith('sqlite'):
            conn = sqlite3.connect(self.peering_name)
            c = conn.cursor()
            for row in c.execute("SELECT asn, ixlan_id FROM 'peeringdb_network_ixlan'"):
                AS, ixp = row[0], row[1]
                if ixp not in ixp_dict:
                    ixp_dict[ixp] = [AS]
                else:
                    ixp_dict[ixp].append(AS)
            for row in c.execute("SELECT local_asn, fac_id FROM 'peeringdb_network_facility'"):
                AS, facility = row[0], row[1]
                if facility not in facility_dict:
                    facility_dict[facility] = [AS]
                else:
                    facility_dict[facility].append(AS)
        
        else:
            raise TypeError('PeeringDB file must be either a json file or a sqlite file.')
                

        for _, v in ixp_dict.items():
            as_pairs = [(p1, p2) for p1 in v for p2 in v if p1 != p2]
            for pair in as_pairs:
                self.ixp[(pair[0], pair[1])] += 1
        for _, v in facility_dict.items():
            as_pairs = [(p1, p2) for p1 in v for p2 in v if p1 != p2]
            for pair in as_pairs:
                self.facility[(pair[0], pair[1])] += 1

        for link in self.prob:
            if link not in self.ixp:
                self.ixp[link] = 0
        for link in self.prob:
            if link not in self.facility:
                self.facility[link] = 0

    def assignDistance2Clique(self):
        shortestDistanceList = defaultdict(list)
        g = nx.Graph()
        for link in self.prob:
            g.add_edge(link[0], link[1])
        clique = ['174', '209', '286', '701', '1239', '1299', '2828', '2914', '3257', '3320', '3356', '3491', '5511', '6453', '6461', '6762', '6830', '7018', '12956']
        for c in clique:
            if c not in g:
                clique.remove(c)
            else:
                p = nx.shortest_path_length(g, source=c)
                for k, v in p.items():
                    shortestDistanceList[k].append(v)

        for link in self.prob:
            AS1, AS2 = link
            if len(shortestDistanceList[AS1]) == 0:
                disAS1 = 200
            else:
                disAS1 = int(sum(shortestDistanceList[AS1])/float(len(shortestDistanceList[AS1]))/0.1)
            if len(shortestDistanceList[AS2]) == 0:
                disAS2 = 200
            else:
                disAS2 = int(sum(shortestDistanceList[AS2])/float(len(shortestDistanceList[AS2]))/0.1)
            self.distance2Clique[link] = (disAS1, disAS2)

    def assignAdjanceTypeRatio(self):
        for link in self.prob:
            AS1, AS2 = link
            type1 = [len(self.provider[AS1]), len(self.peer[AS1]), len(self.customer[AS1])]
            deg1 = float(sum(type1))
            type2 = [len(self.provider[AS2]), len(self.peer[AS2]), len(self.customer[AS2])]
            deg2 = float(sum(type2))
            ratio1 = list(map(lambda x:round(x/deg1/0.1), type1))
            ratio2 = list(map(lambda x:round(x/deg2/0.1), type2))
            self.adjanceTypeRatio[link] = (ratio1[0], ratio1[1], ratio1[2], ratio2[0], ratio2[1], ratio2[2])
            self.degreeRatio[link] = round(deg1/deg2/0.1)
    
    def constructAttributes(self):
        self.getEdgeClass()
        self.assignNonpath()
        self.assignDistance2Clique()
        self.assignIXPFacility()
        self.assignAdjanceTypeRatio()