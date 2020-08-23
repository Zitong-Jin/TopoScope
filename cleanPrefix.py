import sys, random, json, sqlite3, argparse
from collections import defaultdict
class UniquePrefix(object):
    def __init__(self, peering_name):
        self.ixp = set()
        self.vp_group = [set(), set()]
        self.path_group = [set(), set()]
        self.prefix_group = [set(), set()]
        self.vp = defaultdict(set)
        self.getIXP(peering_name)

    def getIXP(self, peeringdb_file):
        if peeringdb_file.endswith('json'):
            with open(peeringdb_file) as f:
                data = json.load(f)
            for i in data['net']['data']:
                if i['info_type'] == 'Route Server':
                    self.ixp.add(str(i['asn']))

        elif peeringdb_file.endswith('sqlite'):
            conn = sqlite3.connect(peeringdb_file)
            c = conn.cursor()
            for row in c.execute("SELECT asn, info_type FROM 'peeringdb_network'"):
                asn, info_type = row
                if info_type == 'Route Server':
                    self.ixp.add(str(asn))

        else:
            raise TypeError('PeeringDB file must be either a json file or a sqlite file.')

    def ASNAllocated(self, asn):
        if asn == 23456 or asn == 0:
            return False
        elif asn > 399260:
            return False
        elif asn > 64495 and asn < 131072:
            return False
        elif asn > 141625 and asn < 196608:
            return False
        elif asn > 210331 and asn < 262144:
            return False
        elif asn > 270748 and asn < 327680:
            return False
        elif asn > 328703 and asn < 393216:
            return False
        else:
            return True

    def groupPrefix(self, name):
        with open(name) as f:
            for line in f:
                if line.strip() == '':
                    continue
                [path, prefix] = line.strip().split('&')
                asn_list = path.split('|')
                for asn in asn_list:
                    if asn in self.ixp:
                        asn_list.remove(asn)
                asn_list = [v for i, v in enumerate(asn_list)
                            if i == 0 or v != asn_list[i-1]]
                asn_set = set(asn_list)
                if len(asn_set) <= 1 or not len(asn_list) == len(asn_set):
                    continue
                for asn in asn_list:
                    if not self.ASNAllocated(int(asn)):
                        break
                else:
                    vp = asn_list[0]
                    for AS in asn_list:
                        self.vp[vp].add(AS)
                    if vp not in self.vp_group[0] and vp not in self.vp_group[1]:
                        self.vp_group[random.randint(0, 1)].add(vp)
                    if vp in self.vp_group[0]:
                        self.path_group[0].add('|'.join(asn_list))
                        self.prefix_group[0].add('|'.join(asn_list) + '&' + prefix)
                    if vp in self.vp_group[1]:
                        self.path_group[1].add('|'.join(asn_list))
                        self.prefix_group[1].add('|'.join(asn_list) + '&' + prefix)
                continue

    def writePrefix(self):
        for choose in [0, 1]:
            fout = open('chooseVP' + str(choose) + '.txt', 'w')
            for vp in self.vp_group[choose]:
                fout.write(vp + '\n')
            fout.close()

            fout = open('aspaths' + str(choose) + '.txt', 'w')
            for path in self.path_group[choose]:
                fout.write(path + '\n')
            fout.close()

            fout = open('asprefix' + str(choose) + '.txt', 'w')
            for prefix in self.prefix_group[choose]:
                fout.write(prefix + '\n')
            fout.close()
        fout = open('fullVP.txt', 'w')
        for vp in self.vp.keys():
            if 65000*0.8 < len(self.vp[vp]):
                fout.write(vp + '\n')
        fout.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='clean prefix')
    parser.add_argument('-i', '--input_name', required=True)
    parser.add_argument('-p', '--peering_name', required=True)
    args = parser.parse_args()
    
    prefix = UniquePrefix(args.peering_name)
    prefix.groupPrefix(args.input_name)
    prefix.writePrefix()