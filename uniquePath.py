import sys, json, sqlite3, argparse

class UniquePath(object):
    def __init__(self, peering_name):
        self.origin_paths = set()
        self.forward_paths = set()
        self.unique_paths = set()
        self.ixp = set()
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

    def getPath(self, name):
        with open(name) as f:
            for line in f:
                if line.strip() == '':
                    continue
                self.origin_paths.add(line.strip())
                asn_list = line.strip().split('|')
                for asn in asn_list:
                    if asn in self.ixp:
                        asn_list.remove(asn)
                asn_list = [v for i, v in enumerate(asn_list)
                            if i == 0 or v != asn_list[i-1]]
                asn_set = set(asn_list)
                if len(asn_set) == 1 or not len(asn_list) == len(asn_set):
                    continue
                for asn in asn_list:
                    if not self.ASNAllocated(int(asn)):
                        break
                else:
                    self.forward_paths.add('|'.join(asn_list))
                continue

    def writePath(self):
        f = open('aspaths.txt', 'w')
        for path in self.forward_paths:
            f.write(path + '\n')
        f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='clean paths')
    parser.add_argument('-i', '--input_name', required=True)
    parser.add_argument('-p', '--peering_name', required=True)
    args = parser.parse_args()
    
    path = UniquePath(args.peering_name)
    path.getPath(args.input_name)
    path.writePath()