from collections import defaultdict
import networkx as nx
import copy, random, time
import math, os
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
import xgboost, argparse
from basicAtts import BasicAtts

class Newlink(object):
    def __init__(self, part, prefix_name):
        self.part = part
        self.prefix_name = prefix_name
        all_VP = set(open('chooseVP' + self.part + '.txt', 'r').read().split('\n'))
        self.fullVP = set(open('fullVP.txt', 'r').read().split('\n'))
        self.fullAS = eval(open('chooseAS.txt', 'r').read())
        self.fullVP1 = all_VP & self.fullVP
        self.fullAS1 = self.fullAS - self.fullVP

        self.ba = BasicAtts('asrel' + self.part + '.txt')
        self.ba.calPr()
        
        self.ASpfx = defaultdict(int)
        self.edgeamount = defaultdict(int)
        self.triple = set()

        self.getTriple()
        self.getASpfx()
        self.getEdgeAmount()

    def getASpfx(self):
        with open(self.prefix_name) as f:
            for line in f:
                AS = line.strip().split('\t')[-1]
                if '_' not in AS:
                    self.ASpfx[AS] += 1
                else:
                    for ASes in AS.split('_'):
                        self.ASpfx[ASes] += 1

    def getEdgeAmount(self):
        with open('asprefix' + part + '.txt') as f:
            for line in f:
                path = line.strip().split('&')[0].split('|')
                for i in range(len(path) - 1):
                    asn1, asn2 = path[i], path[i + 1]
                    self.edgeamount[(asn1, asn2)] += 1
                    self.edgeamount[(asn2, asn1)] += 1
    
    def getTriple(self):
        with open('triplet_miss' + self.part + '.txt') as f:
            for line in f:
                if line == '\n':
                    continue
                tri = line.strip().split('&')[1].split('#')
                for t in tri:
                    t = t.split('|')
                    if self.ba.graph.degree(t[0]) > self.ba.graph.degree(t[2]) or (self.ba.graph.degree(t[0]) == self.ba.graph.degree(t[2]) and int(t[0]) > int(t[2])):
                        t = (t[2], t[1], t[0])
                    self.triple.add(tuple(t))

    def assignPosition(self):
        self.cnt = defaultdict(int)
        self.prev = defaultdict(lambda: defaultdict(int))
        self.next = defaultdict(lambda: defaultdict(int))
        self.position = defaultdict(lambda: defaultdict(int))
        self.seliver = defaultdict(lambda: defaultdict(set))

        report = 1
        with open('asprefix' + self.part + '.txt') as f:
            for line in f:
                report += 1
                if report % 1000000 == 0:
                    print(report)
                if line == '\n':
                    continue
                path = line.strip().split('&')[0].split('|')
                prefix = line.strip().split('&')[1]
                
                for i in range(len(path) - 2):
                    asn1, asn2, asn3 = path[i], path[i + 1], path[i + 2]
                    if i == 0 and path[0] in self.fullVP1:
                        continue
                    if i == 0:
                        prev = 'null'
                    else:
                        prev = path[i - 1]
                    if i == len(path) - 3:
                        next = 'null'
                    else:
                        next = path[i + 3]
                    p, v = i, len(path) - 3 - i
                    if (asn1 in (self.fullVP | self.fullAS - self.fullVP1) or asn3 in (self.fullVP | self.fullAS - self.fullVP1)) or (asn1, asn2, asn3) in self.triple or (asn3, asn2, asn1) in self.triple:
                        if asn1 not in self.ba.graph.nodes() or asn2 not in self.ba.graph.nodes() or asn3 not in self.ba.graph.nodes():
                            continue
                        if self.ba.graph.degree(asn1) > self.ba.graph.degree(asn3) or (self.ba.graph.degree(asn1) == self.ba.graph.degree(asn3) and int(asn1) > int(asn3)):
                            asn1, asn3 = asn3, asn1
                            prev, next = next, prev
                            p, v = v, p
                        
                        self.cnt[(asn1, asn2, asn3)] += 1
                        self.prev[(asn1, asn2, asn3)][prev] += 1
                        self.next[(asn1, asn2, asn3)][next] += 1
                        self.position[(asn1, asn2, asn3)][(p, v)] += 1
                        self.seliver[(asn1, asn2, asn3)][path[-1]].add(prefix)
        for tri in self.seliver:
            for origin in self.seliver[tri]:
                self.seliver[tri][origin] = len(self.seliver[tri][origin])

    def getNum(self, num):
        if num <= 0:
            return num
        a = int(math.log10(num))
        b = num // (10 ** a)
        return a * 10 + b

    def xgboostInfer(self):
        banVP = set()

        for VP in (self.fullVP | self.fullAS):
            if self.ba.getHierarchy(VP) in [5, 6]:
                banVP.add(VP)
        fullVP = list(self.fullVP - self.fullVP1 - banVP)

        attribute_train = list()
        attribute_test = list()
        attribute_pred = list()
        test = set(fullVP[:int(len(fullVP)*0.3)])

        test_standard = set()
        temp_pred = list()
        temp_pred1 = list()
        pred_order = list()
        
        c1, c2 = 0, 0
        for tri in self.cnt:
            rp = list()
            if (0, 0) in self.position[tri]:
                rp.append(self.position[tri][(0, 0)])
            else:
                rp.append(-1)
            if (0, 1) in self.position[tri]:
                rp.append(self.position[tri][(0, 1)])
            else:
                rp.append(-1)
            if (1, 0) in self.position[tri]:
                rp.append(self.position[tri][(1, 0)])
            else:
                rp.append(-1)
            
            rpn = list()
            if 'null' in self.prev[tri]:
                rpn.append(self.prev[tri]['null'])
            else:
                rpn.append(-1)
            if 'null' in self.next[tri]:
                rpn.append(self.next[tri]['null'])
            else:
                rpn.append(-1)

            seliver_avg = 0.0
            for s in self.seliver[tri]:
                if s in self.ASpfx:
                    seliver_avg += self.seliver[tri][s] / self.ASpfx[s]
                else:
                    seliver_avg += 1
            seliver_avg /= len(self.seliver[tri])
            
            self.prev[tri] = sorted(self.prev[tri].items(),key=lambda x:x[1],reverse=True)
            self.next[tri] = sorted(self.next[tri].items(),key=lambda x:x[1],reverse=True)
            len_prev = len(self.prev[tri])
            prev = self.prev[tri][:3]
            len_next = len(self.next[tri])
            next = self.next[tri][:3]
            edgeamount = [self.edgeamount[(tri[0], tri[1])], self.edgeamount[(tri[1], tri[2])]]
            
            x = []
            if self.ba.getHierarchy(tri[0]) in [6, 5, 4] or self.ba.getHierarchy(tri[2]) in [6, 5, 4]:
                continue
            if tri[2] in fullVP:
                x.append(0)
            else:
                x.append(1)
            x.append(self.cnt[tri])
            x.extend([len(self.ba.provider[tri[0]]), len(self.ba.peer[tri[0]]), len(self.ba.customer[tri[0]])])
            x.extend([len(self.ba.provider[tri[1]]), len(self.ba.peer[tri[1]]), len(self.ba.customer[tri[1]])])
            x.extend([len(self.ba.provider[tri[2]]), len(self.ba.peer[tri[2]]), len(self.ba.customer[tri[2]])])
            x.extend([self.ba.pr[tri[0]]*10000, self.ba.pr[tri[1]]*10000, self.ba.pr[tri[2]]*10000])
            x.extend([self.getNum(edgeamount[0]), self.getNum(edgeamount[1])])
            x.extend([self.ba.getEdgeRelationship(tri[0], tri[1]), self.ba.getEdgeRelationship(tri[1], tri[2])])
            x.extend([self.ba.getHierarchy(tri[0]), self.ba.getHierarchy(tri[1]), self.ba.getHierarchy(tri[2])])
            x.extend([self.ba.getDegree(tri[0]), self.ba.getDegree(tri[1]), self.ba.getDegree(tri[2])])

            x.extend([len(set(self.ba.graph.neighbors(tri[0])) & (self.ba.clique | self.ba.tier2)), len(set(self.ba.graph.neighbors(tri[2])) & (self.ba.clique | self.ba.tier2))])
            x.extend([len_prev, len_next])
            x.extend(rp)
            x.extend(rpn)
            
            for i in range(2):
                if i >= len(prev):
                    x.extend([-1, -1, -1])
                    continue
                x.extend([self.ba.getHierarchy(prev[i][0]), self.ba.getDegree(prev[i][0]), prev[i][1]])
            for i in range(2):
                if i >= len(next):
                    x.extend([-1, -1, -1])
                    continue
                x.extend([self.ba.getHierarchy(next[i][0]), self.ba.getDegree(next[i][0]), next[i][1]])

            x.append(seliver_avg)
            if tri[0] in test or tri[2] in test:
                temp_pred.append(tri)
                if tri in self.triple:
                    x.append(1.0)
                    attribute_test.append(x)
                    temp_pred1.append(tri)
                    test_standard.add((tri[0], tri[2]))
                else:
                    x.append(0.0)
                    attribute_test.append(x)
            elif tri[0] in fullVP or tri[2] in fullVP:
                if tri in self.triple:
                    c1 += 1
                    x.append(1.0)
                    attribute_train.append(x)
                else:
                    c2 += 1
                    x.append(0.0)
                    attribute_train.append(x)
            else:
                attribute_pred.append(x)
                pred_order.append(tri)

        dataset_train = np.array(attribute_train)
        dataset_test = np.array(attribute_test)
        dataset_pred = np.array(attribute_pred)
        
        _, l = dataset_train.shape
        
        X_train = dataset_train[:,0:l-1]
        y_train = dataset_train[:,l-1]

        X_test = dataset_test[:,0:l-1]
        y_test = dataset_test[:,l-1]

        X_pred = dataset_pred

        model = XGBClassifier(eta=0.1, min_child_weight=3, gamma=5, n_estimator=1000, max_depth=8)
        eval_set=[(X_train, y_train), (X_test, y_test)]
        sample_weights_data = list()
        for i in range(len(y_train)):
            if y_train[i] == 1.0:
                sample_weights_data.append(c2/(c1+c2))
            elif y_train[i] == 0.0:
                sample_weights_data.append(c1/(c1+c2))
        eval_set=[(X_train, y_train), (X_test, y_test)]
        model.fit(X_train, y_train, eval_metric=['aucpr', 'error', 'auc'], eval_set=eval_set, sample_weight=sample_weights_data)

        print(model.feature_importances_)
        y_pred_proba = model.predict_proba(X_test)

        predictions = [round(value[1]) for value in y_pred_proba]
        really_pred1 = defaultdict(int)
        really_pred2 = defaultdict(int)
        really_pred = set()
        for i in range(len(predictions)):
            really_pred1[(temp_pred[i][0], temp_pred[i][2])] += 1
            if predictions[i] == 1:
                really_pred2[(temp_pred[i][0], temp_pred[i][2])] += 1
        for key in really_pred1:
            if really_pred2[key] >= really_pred1[key] / 2:
                really_pred.add(key)
        print(len(really_pred), len(test_standard), len(really_pred & test_standard))
        
        y_pred_proba = model.predict_proba(X_pred)
        predictions = [round(value[1]) for value in y_pred_proba]
        
        ftri = open('futher' + self.part + '.txt', 'w')
        for i in range(len(predictions)):
            if predictions[i] == 1:
                ftri.write(pred_order[i][0] + '|' + pred_order[i][1] + '|' + pred_order[i][2] + '\n')
        ftri.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--prefix_name', required=True)
    args = parser.parse_args()

    for part in ['0', '1']:
        newlink = Newlink(part, args.prefix_name)
        newlink.assignPosition()
        newlink.xgboostInfer()