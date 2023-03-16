#!.venv/bin/python

import os
import sys
import datetime

from loguru import logger

from Pravo import GetPravo
from OSM import GetOSM
from Jinja import Generate
from Git import GitPush

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')


logger.add(os.path.join(".log", "osm.log"))
logger.info("Start")

Context = {}
Context['DateTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
Context['PravoError'], Context['Pravo'] = GetPravo()
Context['Highway'] = {
 'M': { 'Desc': "Магістральныя аўтамабільныя дарогі", 'List': GetOSM("М", 1246287, "M.csv"), },
 'P': { 'Desc': "Рэспубліканскія аўтамабільныя дарогі", 'List': GetOSM("Р", 1246288, "P.csv"), },
 'H': { 'Desc': "Мясцовыя аўтамабільныя дарогі", 'List': GetOSM("Н", 1246286, "H.csv"), },
}
Generate("index.html", Context)
Generate("index.relation.html", Context)
Generate("index.error.html", Context)
Generate("index.csv", Context)
Generate("index.relation.csv", Context)
Generate("index.error.csv", Context)

if GitPush(f"autogenerate {datetime.datetime.now().strftime('%Y-%m-%d')}"):
 logger.info("Git Push complete")

logger.info("Done")
