#!/usr/bin/env xonsh
# Script for starting all the servers

# start elasticsearch (the service)
#terminator -p xonsh -e "sh /home/christopher/elasticsearch/elasticsearch-6.6.1/bin/elasticsearch" &

# start zmq proxy
environment = 'dp_dev'
terminator -p xonsh -e f"source activate {environment}; bluesky-0MQ-proxy 5567 5568" &

# start data processing servers
for c in [
  'viz_server --db=raw.yml',
  'portable_db_server /home/christopher/dev/provenance-driven-ldrd/demo',
  'tomo_server --db=raw.yml',
  'python /home/christopher/dev/provenance-driven-ldrd/demo/elastic_server.py'
]:
    terminator -p xonsh -e @(f"source activate {environment}; {c}") &
