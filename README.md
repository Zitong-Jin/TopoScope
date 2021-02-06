# Toposcope

## What is TopoScope?

TopoScope is an AS relationship inference algorithm that combines ensemble learning and Bayesian networks. In addition, TopoScope also supports hidden link inference. You can learn more about TopoScope in IMC 2020.

## Quickstart

To get started using TopoScope, clone or download this [GitHub repo](https://github.com/Zitong-Jin/TopoScope).

TopoScope runs with python 3.6.8

__Install Python dependencies__

```sh
$ pip install --user -r requirements.txt
```

__Download AS to Organization Mapping Dataset from CAIDA__

https://www.caida.org/data/as-organizations/

__Download PeeringDB Dataset from CAIDA__

Before March 2016: http://data.caida.org/datasets/peeringdb-v1/

After March 2016: http://data.caida.org/datasets/peeringdb-v2/

__Download Prefix2AS Dataset from CAIDA__

http://data.caida.org/datasets/routing/routeviews-prefix2as/

__Prepare BGP paths from Route Views and RIS__

You can prepare BGP paths from [BGPStream](https://bgpstream.caida.org/) or download rib file from [Route Views](http://archive.routeviews.org/) and [RIS](http://data.ris.ripe.net/). 

Noting that TopoScope only use IPv4 AS paths. Here is an example to extract AS paths from rib file:

```sh
prefix = re.search(r'PREFIX: ([^\n]*)\n', block).group(1).strip()
if prefix:
    aspath = re.search(r'ASPATH: ([^\n]*)\n', block).group(1).strip()
    if '{' in aspath or '(' in aspath:
        continue
    if ":" not in temp_prefix:
        output.append(aspath.replace(' ', '|'))
        #output.append(aspath.replace(' ', '|') + '&' + prefix)
```

__Prepare BGP paths from Isolario__

You can download rib file and extract AS paths from [Isolario](https://www.isolario.it/Isolario_MRT_data/).

Noting that Isolario data is only used for hidden link inference in the IMC paper. But you can also use it for basic inference by yourself.

### Basic inference

The ASes on each BGP path should be delimited by '|' on each line, for example, AS1|AS2|AS3.

__Parse downloaded BGP paths__

```sh
$ python uniquePath.py -i=<aspaths file> -p=<peeringdb file>
# e.g. python uniquePath.py -i=aspaths_2019.txt -p=peeringdb_2019.json
# Output is written to 'aspaths.txt'.
```

__Run AS-Rank algorithm to bootstrap TopoScope__

```sh
$ perl asrank.pl aspaths.txt > asrel.txt
```

__Run Toposcope__ 

```sh
$ python toposcope.py -o=<ASorg file> -p=<peeringdb file> -d=<temporary storage folder name>
#e.g. python toposcope.py -o=asorg_2019.txt -p=peeringdb_2019.json -d=tmp/
# Output is written to 'asrel_toposcope.txt'.
```

__Output data format__

\<provider-as\>|\<customer-as\>|-1 

\<peer-as\>|\<peer-as\>|0 

\<sibling-as\>|\<sibling-as\>|1

### Hidden link inference

The ASes on each BGP path should be delimited by '|' on each line, followed by '&' and prefix, for example, AS1|AS2|AS3&prefix.

__Parse downloaded BGP paths__

```sh
$ python cleanPrefix.py -i=<asprefix file> -p=<peeringdb file>
# e.g. python cleanPrefix.py -i=asprefix_2019.txt -p=peeringdb_2019.json
# Output is written to 'fullVP.txt', 'aspaths0.txt', 'aspaths1.txt', 'asprefix0.txt', 'asprefix1.txt', 'chooseVP0.txt' and 'chooseVP1.txt'.
```

__Run AS-Rank algorithm to bootstrap TopoScope__

```sh
$ perl asrank.pl aspaths0.txt > asrel0.txt
$ perl asrank.pl aspaths1.txt > asrel1.txt
```

You can also use basic inference result of TopoScope instead of ASRank to finish this step.

__Find miss edges and choose ASes similar to full VPs__

```sh
$ python getMissEdge.py
# Output is written to 'triplet_miss0.txt' and 'triplet_miss1.txt'.
$ python chooseAS.py
# Output is written to 'chooseAS.txt'.
```

__Run Toposcope to find hidden links__ 

```sh
$ python newlink.py -f=<prefix2AS file>
# e.g. python newlink.py -f=pfx2as_2019.txt
# Output is written to 'futher0.txt' and 'futher1.txt'.
```

__Infer AS relationships of hidden links__

```sh
$ python linkRel.py
# Output is written to 'asrel_hidden.txt'
```

__Output data format__

\<provider-as\>|\<customer-as\>|-1 

\<peer-as\>|\<peer-as\>|0 

__Example__

You can download AS relationship inference result form 2017 to 2019 in /asrel/.

## Contact 

You can contact us at <jinzt19@mails.tsinghua.edu.cn>.

## Monthly inferred results

We will update them later.