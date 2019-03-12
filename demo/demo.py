import os
import time

import bluesky.plans as bp
import dxchange
import numpy as np
import tomopy
from bluesky.run_engine import RunEngine
from ophyd.sim import SynSignal, hw, SynSignalWithRegistry
from xpdan.vend.callbacks.zmq import Publisher
from xpdconf.conf import glbl_dict

hw = hw()
fname = os.path.expanduser("~/Downloads/tooth.h5")

proj, flat, dark, theta = dxchange.read_aps_32id(fname, sino=(0, 1))

proj = tomopy.normalize(proj, flat, dark)

rot_center = tomopy.find_center(proj, theta, init=290, ind=0, tol=0.5)
proj2 = proj
m = hw.motor1
m.kind = "hinted"
mm = hw.motor2
mm.kind = "hinted"


class FullField:
    def __call__(self, *args, **kwargs):
        v = m.get()[0]
        out = proj2[int(v), :, :]
        print(v)
        time.sleep(.5)
        return out


class Pencil:
    def __call__(self, *args, **kwargs):
        v = m.get()[0]
        vv = mm.get()[0]
        out = proj2[int(v), :, int(vv)]
        print(v, vv)
        time.sleep(.1)
        return np.squeeze(out)


f = FullField()
det = SynSignalWithRegistry(f, name="img", labels={"detectors"},
                            save_path='/home/christopher/dev/provenance-driven-ldrd/demo/raw_data')
# det = SynSignal(f, name="img", labels={"detectors"})
det.kind = "hinted"

# g = Pencil()
# det2 = SynSignalWithRegistry(g, name="img", labels={"detectors"})
# det2.kind = "hinted"

RE = RunEngine()
p = Publisher(glbl_dict["inbound_proxy_address"], prefix=b"raw")
t = RE.subscribe(p)
# RE.subscribe(print)
# Build scan
l = [0, 90]
for i in range(8):
    ll = l.copy()
    interval = sorted(set(ll))[1] / 2
    for lll in ll:
        j = lll + interval
        j = round(j, 0)
        if j not in l and j <= 180:
            l.append(j)
# Run Full Field Scans, each scan has more slices, showing how we can minimize
# the number of slices by interleaving them by half
RE(
    bp.list_scan(
        [det],
        m,
        l[:64],
        md={
            "tomo": {
                "type": "full_field",
                "rotation": "motor1",
                "center": rot_center,
            },
            'bt_piLast': 'Wright',
            'analysis_stage': 'raw'
        },
    )
)
RE.abort()

###################
# Plan:
# Bonus points if we can install from CF from scratch (use metachannel?)

# Run data acq with ES server
# Run ES search on data, report headers
# Run data acq with or run header through An pipeline and An ES insert
# Run ES search on An data
# Run replay on An header
# TADA!!

# Bonus points if we can write a parallel Tomo Server (but not mission
# critical)

##################
# TODO: setup elasticsearch server
# TODO: setup elasticsearch dispatcher server
# TODO: make elasticsearch config files
# TODO: make example ES queries
# TODO: make tomo graph plot

# TODO: make provenance tomo pipeline
# TODO: Retrieve data in tomo pipeline
# TODO: make DB insert more pipeline friendly
# TODO: run replay on tomo data
