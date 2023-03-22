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


logger.add(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".log", "osm.log"))
logger.info("Start")

Context = {}
Context['PravoError'], Context['Pravo'] = GetPravo()
Relations = ReadOSM("М", 1246287) | ReadOSM("Р", 1246288) | ReadOSM("Н", 1246286)
Context['Highway'] = {
 'M': { 'Desc': "Магістральныя аўтамабільныя дарогі", 'List': GetOSM("М", Relations, "M.csv"), },
 'P': { 'Desc': "Рэспубліканскія аўтамабільныя дарогі", 'List': GetOSM("Р", Relations, "P.csv"), },
 'H': { 'Desc': "Мясцовыя аўтамабільныя дарогі", 'List': GetOSM("Н", Relations, "H.csv"), },
}
Context['DateTime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
FileNames = ["index.html", "relation.html", "error.html", "index.csv", "relation.csv", "error.csv", ]
for FileName in FileNames:
 Generate(FileName, Context)

if GitPush(f"autogenerate {datetime.datetime.now().strftime('%Y-%m-%d')}"):
 Diff = repo.git.diff('HEAD~1')
 logger.info(f"Git Push complete\n{Diff}")

logger.info("Done")
