import copy, random, os
from collections import defaultdict
from hierarchy import Hierarchy

class GetFullVP(object):
    def __init__(self, groupSize, dirs):
        self.groupSize = groupSize
        self.dir = dirs
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
        self.VP2AS = defaultdict(set)
        self.VP2path = defaultdict(set)
        self.fullVP = set()
        self.partialVP = set()
        self.VPGroup = list()
        self.fileNum = -1
        self.tier = Hierarchy('asrel.txt')

    def getFullVP(self):
        with open('aspaths.txt') as f:
            for line in f:
                ASes = line.strip().split('|')
                for AS in ASes:
                    self.VP2AS[ASes[0]].add(AS)
                self.VP2path[ASes[0]].add(line.strip())
        for VP in self.VP2AS.keys():
            if 65000*0.8 < len(self.VP2AS[VP]):
                self.fullVP.add(VP)
            else:
                self.partialVP.add(VP)

    def fullVPGroup(self):
        VP_copy1, VP_copy2 = list(), list()
        for VP in self.fullVP:
            if VP in self.tier.clique or VP in self.tier.high:
                VP_copy1.append(VP)
            else:
                VP_copy2.append(VP)
        
        while len(VP_copy1) >= self.groupSize:
            tmp = list()
            for _ in range(self.groupSize):
                index = random.randint(0, len(VP_copy1) - 1)
                tmp.append(VP_copy1.pop(index))
            self.VPGroup.append(tmp)
        while len(VP_copy2) >= self.groupSize:
            tmp = list()
            for _ in range(self.groupSize):
                index = random.randint(0, len(VP_copy2) - 1)
                tmp.append(VP_copy2.pop(index))
            self.VPGroup.append(tmp)
        tmp = []
        for VP in VP_copy2 + VP_copy1:
            tmp.append(VP)
        if len(tmp) > self.groupSize:
            self.VPGroup.append(tmp[:self.groupSize])
            tmp = tmp[self.groupSize:]
        for VP in self.partialVP:
            tmp.append(VP)
        self.VPGroup.append(tmp)
        self.fileNum = len(self.VPGroup)

    def writeFullVPPath(self):
        for i in range(self.fileNum):
            f = open(self.dir + 'fullVPPath' + str(i) + '.txt', 'w')
            for VP in self.VPGroup[i]:
                for path in self.VP2path[VP]:
                    f.write(path + '\n')
            f.close()

    def inferTopo(self):
        for i in range(self.fileNum):
            os.system("perl asrank.pl " + self.dir + "fullVPPath" + str(i) + ".txt > " + self.dir + "fullVPRel" + str(i) + ".txt")
            
    def run(self):
        self.getFullVP()
        self.fullVPGroup()
        self.writeFullVPPath()
        self.inferTopo()
        
