#!.venv/bin/python

import os
import sys
import datetime

from loguru import logger

from Pravo import GetPravo
from OSM import ReadOSM, GetOSM
from Jinja import Generate
from Git import GitPush

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

logger.add(os.path.join(".log", "osm.log"))
logger.info("Start")


M = ReadOSM(1246287)
P = ReadOSM(1246288)
H = ReadOSM(1246286)

Context = {}
Context['DateTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
Context['PravoError'], Context['Pravo'] = GetPravo()
Context['Highway'] = {
 'M': { 'Desc': "Магістральныя аўтамабільныя дарогі", 'List': GetOSM("М", M, "M.csv"), },
 'P': { 'Desc': "Рэспубліканскія аўтамабільныя дарогі", 'List': GetOSM("Р", P, "P.csv"), },
 'H': { 'Desc': "Мясцовыя аўтамабільныя дарогі", 'List': GetOSM("Н", H, "H.csv"), },
}
Generate(Context)

if GitPush(f"autogenerate {datetime.datetime.now().strftime('%Y-%m-%d')}"):
 logger.info("Git Push complete")

logger.info("Done")
