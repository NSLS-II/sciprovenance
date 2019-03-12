from pprint import pprint

import yaml
from databroker import Broker
from rapidz.graph import _clean_text, readable_graph
from xpdan.vend.callbacks.core import Retrieve
from xpdan.vend.callbacks.zmq import Publisher
from xpdconf.conf import glbl_dict

dbs = {}
for yaml_file in ['raw', 'an']:
    with open(f'{yaml_file}.yml', 'r') as f:
        dbs[yaml_file] = Broker.from_config(yaml.load(f))

from shed.replay import replay

# load the replay
graph, parents, data, vs = replay(dbs['raw'], dbs['an'][-3])
# make the graph more accessible to humans by renaming things
# these names *should* match the names in the graph plot
for k, v in graph.nodes.items():
    v.update(label=_clean_text(str(v['stream'])).strip())
graph = readable_graph(graph)
graph.nodes['data img FromEventStream']['stream'].visualize()

# print the current reconstruction algorithm
print(graph.nodes['starmap; recon_wrapper']['stream'].kwargs)

# change to filtered back projection
graph.nodes['starmap; recon_wrapper']['stream'].kwargs['algorithm'] = 'art'
print(graph.nodes['starmap; recon_wrapper']['stream'].kwargs)

# setup a publisher to send over to data viz
p = Publisher(glbl_dict['inbound_proxy_address'], prefix=b'tomo')
graph.nodes['img_tomo ToEventStream']['stream'].DBFriendly().starsink(p)
# graph.nodes['img_sinogram ToEventStream']['stream'].DBFriendly().starsink(p)
# graph.nodes['img_tomo ToEventStream']['stream'].sink(print)
# rerun data processing
r = Retrieve(dbs['raw'].reg.handler_reg)
for v in vs:
    d = data[v['uid']]
    dd = r(*d)
    # print(v['uid'])
    parents[v["node"]].update(dd)
