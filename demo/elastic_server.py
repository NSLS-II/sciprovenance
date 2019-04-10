from databroker_elasticsearch.elasticcallback import ElasticCallback

from xpdan.vend.callbacks.core import RunRouter
from xpdan.vend.callbacks.zmq import RemoteDispatcher
from xpdconf.conf import glbl_dict

from databroker_elasticsearch.converters import register_converter


def filtertype(seq, tp):
    return (o for o in seq if isinstance(o, tp))


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
        nodes.append(e)
    return nodes


raw_config = {"databroker-elasticsearch":
                  {"host": "localhost",
    "index": "demo-raw",
        "docmap": [
            ["uid", "_id", "str"],
            ["comment"],
            ["cycle", "cycle", "int"],
            ["detectors"],
            ["e0"],
            ["edge"],
            ["element"],
            ["element_full"],
            ["experiment"],
            ["group"],
            ["name"],
            ["num_points"],
            ["plan_name"],
            ["PI", "pi"],
            ["PROPOSAL", "proposal"],
            ["SAF", "saf"],
            ["scan_id"],
            ["time"],
            ["trajectory_name"],
            ["uid"],
            ["year", "year", "int"],
            ["time", "date", "toisoformat"],
            ['sample_name']
        ]
    },
}

es_raw = ElasticCallback.from_config(raw_config)

an_config = {
"databroker-elasticsearch":{
    "host": "localhost",
    "index": "demo-an",
        "docmap": [
            ['uid', '_id'],
            ['uid'],
            ['parent_uids', 'puid', 'listofstrings'],
            ['analysis_stage'],
            ['graph', 'usednodes', 'tomo_usednodes'],
        ]
    },
}

es_an = ElasticCallback.from_config(an_config)


def run_server(
    outbound_proxy_address=glbl_dict["outbound_proxy_address"], **kwargs
):
    """Server for performing tomographic reconstructions

    Parameters
    ----------
    outbound_proxy_address : str, optional
        The outbound ip address for the ZMQ server. Defaults to the value
        from the global dict

    """
    print(kwargs)
    rr = RunRouter(
        [
            lambda x: es_raw if x["analysis_stage"] == "raw" else None,
            lambda x: es_an if x["analysis_stage"] != "raw" else None,
        ]
    )

    d = RemoteDispatcher(outbound_proxy_address)

    d.subscribe(rr)
    print("Starting Elastic Ingest Server")
    d.start()


def run_main():
    import fire

    fire.Fire(run_server)


if __name__ == "__main__":
    run_main()
