rm -r an/
rm -r raw/
rm -r raw_data/

mkdir raw_data

import esconverters
raw_es = load_elasticindex('es-raw.yaml')
an_es = load_elasticindex('es-an.yaml')
raw_es.reset()
an_es.reset()
