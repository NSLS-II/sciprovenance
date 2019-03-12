#!/usr/bin/env xonsh

# xterm -e "source activate dp_dev; bluesky-0MQ-proxy 5567 5568" &
for c in [
  'viz_server',
#   'portable_db_server /home/christopher/dev/provenance-driven-ldrd/demo',
   'tomo_server',
#    'qoi_server',
]:
    terminator -p xonsh -e @(f"source activate dp_dev; {c}") &
#xterm -e "source activate dp_dev; viz_server" &
#xterm -e "source activate dp_dev; save_server" &
#xterm -e "source activate dp_dev; python analysis.py" &
