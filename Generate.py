#!.venv/bin/python

import os
import sys
from datetime import datetime

from loguru import logger

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

Path = os.path.dirname(os.path.abspath(__file__))
logger.add(os.path.join(Path, ".log", "osm.log"))
logger.info("Start")


from Pravo import GetPravo
from OSM import LoadDesc, ReadOSM, GetOSM, GetPlace, GetMissing, GetDateTime
from Jinja import Generate
from Git import GitPush


Directory = os.path.join(Path, ".data")
if not os.path.exists(Directory):
 os.makedirs(Directory)

Context = {}
Context['PravoError'], Context['Pravo'] = GetPravo()
Highways = LoadDesc("M.csv") | LoadDesc("P.csv") | LoadDesc("H.csv")
Relations = ReadOSM("М", 1246287) | ReadOSM("Р", 1246288) | ReadOSM("Н", 1246286)
Place = GetPlace()
Context['Highway'] = {
 'M': { 'Desc': "Магістральныя аўтамабільныя дарогі", 'List': GetOSM("М", Relations, "M.csv", Place, Highways), },
 'P': { 'Desc': "Рэспубліканскія аўтамабільныя дарогі", 'List': GetOSM("Р", Relations, "P.csv", Place, Highways), },
 'H': { 'Desc': "Мясцовыя аўтамабільныя дарогі", 'List': GetOSM("Н", Relations, "H.csv", Place, Highways), },
}
Context['Missing'] = GetMissing()
Context['DateTime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
Context['PBFDateTime'] = GetDateTime()
FileNames = ["index.html", "relation.html", "error.html", "missing.html", "index.csv", "relation.csv", "error.csv", "missing.csv", ]
for FileName in FileNames:
 Generate(FileName, Context)

Diff = GitPush(f"autogenerate {datetime.now().strftime('%Y-%m-%d')}")
if Diff: 
 logger.info(f"git push complete:\n{Diff}")
else:
 logger.error(f"Git error")

logger.info("Done")

#python -m cProfile -s time ./Generate.py
