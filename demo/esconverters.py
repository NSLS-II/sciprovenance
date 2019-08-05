#!/usr/bin/env python3


from databroker_elasticsearch.converters import register_converter


def filtertype(seq, tp):
    return (o for o in seq if isinstance(o, tp))

exclude_kwargs = set(('upstream',))

@register_converter
def tomo_usednodes(graph):
    nodes = []
    fmt = '{mod}.{name}'
    for n in graph['nodes']:
        st = n['stream']
        e = dict()
        e['ndtype'] = fmt.format(**st)
        ad = next(filtertype(st['args'], dict), None)
        al = next(filtertype(st['args'], list), None)
        if ad is not None:
            e['ndfunc'] = fmt.format(**ad)
        elif al is not None:
            e['ndfunc'] = next(filtertype(al, str))
        kw = {k: v for k, v in st['kwargs'].items()
              if not k in exclude_kwargs}
        if kw:
            e['ndkwargs'] = kw
        nodes.append(e)
    return nodes
