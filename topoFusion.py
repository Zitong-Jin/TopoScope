from collections import defaultdict
import numpy as np
import os

class TopoFusion(object):
    def __init__(self, fileNum, dir_name):
        self.fileNum = fileNum
        self.dir = dir_name
        self.prob = defaultdict(lambda: np.array([0.0, 0.0, 0.0]))
        self.linknum = defaultdict(int)

    def getTopoProb(self):
        for i in range(self.fileNum):
            _filename = self.dir + 'fullVPRel' + str(i) + '.txt'
            with open(_filename) as f:
                for line in f:
                    if line.startswith('#'):
                        continue
                    [asn1, asn2, rel] = line.strip().split('|')
                    asn1, asn2 = int(asn1), int(asn2)
                    if rel == '0' or rel == '1':
                        self.prob[(asn1, asn2)] += np.array([1.0, 0.0, 0.0])
                        self.prob[(asn2, asn1)] += np.array([1.0, 0.0, 0.0])
                    elif rel == '-1':
                        self.prob[(asn1, asn2)] += np.array([0.0, 1.0, 0.0])
                        self.prob[(asn2, asn1)] += np.array([0.0, 0.0, 1.0])
                    
                    self.linknum[(asn1, asn2)] += 1
                    self.linknum[(asn2, asn1)] += 1
        self.writeProb()
        self.writeResult(0.8, self.fileNum * 0.8, self.fileNum * 0.2)

    def writeProb(self):
        alllink = set()
        fout = open(self.dir + 'asrel_prime_prob.txt', 'w')
        for link in self.prob:
            if link in alllink:
                continue
            prob = self.prob[link]
            reverse_link = (link[1], link[0])
            seenNum = prob.sum()
            p2p, p2c, c2p = prob / seenNum

            if (p2p == p2c and p2p > c2p):
                if self.linknum[link] > self.fileNum / 2:
                    p2c += 0.001
                else:
                    p2p += 0.001
            if (p2p == c2p and p2p > p2c):
                if self.linknum[link] > self.fileNum / 2:
                    c2p += 0.001
                else:
                    p2p += 0.001
            if (p2c == c2p and p2c > p2p):
                p2c += 0.001
            if (p2c == c2p and p2c == p2p):
                if self.linknum[link] > self.fileNum / 2:
                    p2c += 0.001
                else:
                    p2p += 0.001
            
            if p2c > p2p and p2c > c2p:
                fout.write(str(link[0]) + '|' + str(link[1]) + '|-1|' + str(p2p) + '|' + str(p2c) + '|' + str(c2p) + '|' + str(self.linknum[link]) + '\n')
            elif c2p > p2p and c2p > p2c:
                fout.write(str(link[1]) + '|' + str(link[0]) + '|-1|' + str(p2p) + '|' + str(c2p) + '|' + str(p2c) + '|' + str(self.linknum[link]) + '\n')
            elif p2p > p2c and p2p > c2p:
                if link[0] < link[1]:
                    fout.write(str(link[0]) + '|' + str(link[1]) + '|0|' + str(p2p) + '|' + str(p2c) + '|' + str(c2p) + '|' + str(self.linknum[link]) + '\n')
                else:
                    fout.write(str(link[1]) + '|' + str(link[0]) + '|0|' + str(p2p) + '|' + str(c2p) + '|' + str(p2c) + '|' + str(self.linknum[link]) + '\n')

            alllink.add(link)
            alllink.add(reverse_link)
        fout.close()

    def writeResult(self, lowprob = 0.8, maxseen = 10, minseen = 4):
        alllink = set()
        fout = open(self.dir + 'asrel_prime_prime.txt', 'w')
        for link in self.prob:
            if link in alllink:
                continue
            prob = self.prob[link]
            reverse_link = (link[1], link[0])
            seenNum = prob.sum()
            p2p, p2c, c2p = prob / seenNum
            if not (p2p > lowprob or p2c > lowprob or c2p > lowprob):
                continue
            if seenNum >= maxseen:
                if p2c > p2p and p2c > c2p:
                    fout.write(str(link[0]) + '|' + str(link[1]) + '|-1\n')
                elif c2p > p2p and c2p > p2c:
                    fout.write(str(link[1]) + '|' + str(link[0]) + '|-1\n')
            if seenNum <= minseen:
                if p2p > p2c and p2p > c2p:
                    if link[0] < link[1]:
                        fout.write(str(link[0]) + '|' + str(link[1]) + '|0\n')
                    else:
                        fout.write(str(link[1]) + '|' + str(link[0]) + '|0\n')

            alllink.add(link)
            alllink.add(reverse_link)
        fout.close()
