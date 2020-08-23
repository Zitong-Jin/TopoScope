from basicAtts import BasicAtts
import math
from sklearn.cluster import KMeans

ba = BasicAtts('asrel.txt')
fullVP = set(open('fullVP.txt', 'r').read().split('\n'))

X = []
asn = []
for node in ba.graph.nodes():
    tmp = []
    asn.append(node)
    tmp.append(math.log10(ba.graph.degree(node)))
    tmp.append(ba.distance[node])
    tmp.append(ba.getHierarchy(node))
    tmp.extend([math.log10(len(ba.customer[node])+1), math.log10(len(ba.peer[node])+1), math.log10(len(ba.provider[node])+1)])
    X.append(tmp)

cluster = 10
estimator = KMeans(n_clusters=cluster)
estimator.fit(X)
pred = estimator.labels_
res = [set() for _ in range(cluster)]
for i in range(len(pred)):
    for j in range(cluster):
        if pred[i] == j:
            res[j].add(asn[i])
fout = open('chooseAS.txt', 'w')
for i in range(cluster):
    if len(res[i] & fullVP) / len(res[i]) > 0.1:
        fout.write(str(res[i]))
fout.close()