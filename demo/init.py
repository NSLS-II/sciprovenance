import os
import time

import bluesky.plans as bp
import dxchange
import numpy as np
import tomopy
from bluesky.run_engine import RunEngine
from bluesky.callbacks import LiveTable
from ophyd.sim import SynSignal, hw, SynSignalWithRegistry
from xpdan.vend.callbacks.zmq import Publisher
from xpdconf.conf import glbl_dict

# create fake hardware (motors and detector)
hw = hw()
fname = os.path.expanduser("tooth.h5")

proj, flat, dark, theta = dxchange.read_aps_32id(fname, sino=(0, 1))

proj = tomopy.normalize(proj, flat, dark)

rot_center = tomopy.find_center(proj, theta, init=290, ind=0, tol=0.5)
proj2 = proj
theta_motor = hw.motor1
theta_motor.kind = "hinted"


class FullField:
    def __call__(self, *args, **kwargs):
        v = theta_motor.get()[0]
        out = proj2[int(v), :, :]
        time.sleep(.5)
        return out

f = FullField()
det = SynSignalWithRegistry(f, name="img", labels={"detectors"},
                            save_path='/home/christopher/dev/provenance-driven-ldrd/demo/raw_data')
det.kind = "hinted"

# create run engine, link with ZMQ system
RE = RunEngine()
p = Publisher(glbl_dict["inbound_proxy_address"], prefix=b"raw")
t = RE.subscribe(p)

# build tomo scan locations
def build_scan():
    l = [0, 90]
    for i in range(8):
        ll = l.copy()
        interval = sorted(set(ll))[1] / 2
        for lll in ll:
            j = lll + interval
            j = round(j, 0)
            if j not in l and j <= 180:
                l.append(j)
    return l

shots = 16
RE(
    bp.list_scan(
        [det],
        theta_motor,
        build_scan()[:shots],
        md={
            "tomo": {
                "type": "full_field",
                "rotation": "motor1",
                "center": rot_center,
            },
            'bt_piLast': 'Wright',
            'analysis_stage': 'raw',
            'sample_type': 'tooth',
            'sample_name': 'sabertooth tiger tooth'
        },
    )
)
RE(
    bp.list_scan(
        [det],
        theta_motor,
        build_scan()[:shots],
        md={
            "tomo": {
                "type": "full_field",
                "rotation": "motor1",
                "center": rot_center,
            },
            'bt_piLast': 'Wright',
            'analysis_stage': 'raw',
            'sample_type': 'tooth',
            'sample_name': 'shark tooth'
        },
    )
)
