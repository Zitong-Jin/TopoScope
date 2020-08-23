import argparse
from writeFullVP import GetFullVP
from topoFusion import TopoFusion
from link import Links
import math, os, resource, copy
import numpy as np
from collections import defaultdict
resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))

def output(final_prob, link):
    link_infer = list(link.edge_infer)
    link_finish = list(link.edge_finish)
    link_all = link_finish + link_infer
    
    outputRel = open('asrel_toposcope.txt', 'w')
    inferredLink = set()
    tier1s = ['174', '209', '286', '701', '1239', '1299', '2828', '2914', '3257', '3320', '3356', '4436', '5511', '6453', '6461', '6762', '7018', '12956', '3549']

    for edge in link_finish:
        final_prob[edge] = link.prob[edge]
    
    for edge in link_all:
        AS1, AS2 = edge
        if AS1 in tier1s and AS2 in tier1s:
            outputRel.write('|'.join((str(AS1), str(AS2), '0')) + '\n')
            continue
        reverseEdge = (AS2, AS1)

        if edge in inferredLink:
            continue
        if edge in link.siblings:
            outputRel.write('|'.join((str(AS1), str(AS2), '1')) + '\n')
            inferredLink.add(edge)
            inferredLink.add(reverseEdge)
            continue
        inferredLink.add(edge)
        inferredLink.add(reverseEdge)
        p2p, p2c, c2p = final_prob[edge]
        if p2p > p2c and p2p > c2p:
            if AS1 < AS2:
                outputRel.write('|'.join((str(AS1), str(AS2), '0')) + '\n')
            else:
                outputRel.write('|'.join((str(AS2), str(AS1), '0')) + '\n')
        elif p2c > p2p and p2c > c2p:
            outputRel.write('|'.join((str(AS1), str(AS2), '-1')) + '\n')
        elif c2p > p2p and c2p > p2c:
            outputRel.write('|'.join((str(AS2), str(AS1), '-1')) + '\n')

def BayesNetwork(link):
    link_infer = list(link.edge_infer)
    link_finish = list(link.edge_finish)
    link_all = link_finish + link_infer

    link_feature = [link.vp, link.nonpath, link.ixp, link.facility, link.degreeRatio, link.distance2Clique, link.tripletRel, link.adjanceTypeRatio, link.vppos]
    link_feature_order = [list() for _ in range(len(link_all))]
    
    for i in range(len(link_feature)):
        f_c = 0
        feature_dict = dict()
        for j in range(len(link_all)):
            if isinstance(link_feature[i][link_all[j]], int):
                f = tuple([link_feature[i][link_all[j]]])
            else:
                f = tuple(link_feature[i][link_all[j]])
            if f not in feature_dict:
                feature_dict[f] = f_c
                f_c += 1
            link_feature_order[j].append(feature_dict[f])
    link_feature_order = np.array(link_feature_order)

    parent = {1:[0, 8], 6:[7], 5:[6, 7]}
    final_prob = dict()
    for edge in link_all:
        final_prob[edge] = list(map(lambda x: math.log10(x), link.init_prob[edge]))

    for i in range(len(link_feature)):
        prob = defaultdict(lambda: [0.0, 0.0, 0.0])
        count_class = defaultdict(lambda: [0.0, 0.0, 0.0])
        for j in range(len(link_all)):
            x = link_feature_order[j][i]
            y = []
            if i in parent:
                for pa in parent[i]:
                    y.append(link_feature_order[j][pa])
            y = tuple(y)
            temp_prob = link.init_prob[link_all[j]]
            prob[(x, y)] = tuple([a + b for a, b in zip(prob[(x, y)], temp_prob)])
            count_class[y] = tuple([a + b for a, b in zip(count_class[y], temp_prob)])
        f_prob = dict()
        for key in prob:
            (x, y) = key
            f_prob[x] = tuple([(a + 1) / (b + len(prob)) for a, b in zip(prob[(x, y)], count_class[y])])
        for j in range(len(link_all)):
            edge = link_all[j]
            x = link_feature_order[j][i]
            temp_prob = (f_prob[x][0] + 1e-10, f_prob[x][1] + 1e-10, f_prob[x][2] + 1e-10)
            final_prob[edge] = tuple(map(lambda x, y: x + y, final_prob[edge], tuple(map(lambda x: math.log10(x), temp_prob))))
    output(final_prob, link)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--org_name', required=True)
    parser.add_argument('-p', '--peering_name', required=True)
    parser.add_argument('-d', '--dir_name', required=True)
    args = parser.parse_args()
    getFullVP = GetFullVP(25, args.dir_name)
    getFullVP.run()
    print('get fullVP finished...')
    fileNum = getFullVP.fileNum
    topoFusion = TopoFusion(fileNum, args.dir_name)
    topoFusion.getTopoProb()
    print('topo fusion finished...')
    link = Links(args.dir_name, args.org_name, args.peering_name)
    link.constructAttributes()
    BayesNetwork(link)
