#!.venv/bin/python

import os
import sys
import datetime

from loguru import logger

from Pravo import GetPravo
from OSM import ReadOSM, GetOSM
from CheckPBF import CheckPBF
from Jinja import Generate
from Git import GitPush


sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')


Path = os.path.dirname(os.path.abspath(__file__))
logger.add(os.path.join(Path, ".log", "osm.log"))
logger.info("Start")

Directory = os.path.join(Path, ".data")
if not os.path.exists(Directory):
 os.makedirs(Directory)

Context = {}
Context['Missing'], Place = CheckPBF()
Context['PravoError'], Context['Pravo'] = GetPravo()
Relations = ReadOSM("М", 1246287) | ReadOSM("Р", 1246288) | ReadOSM("Н", 1246286)
Context['Highway'] = {
 'M': { 'Desc': "Магістральныя аўтамабільныя дарогі", 'List': GetOSM("М", Relations, "M.csv", Place), },
 'P': { 'Desc': "Рэспубліканскія аўтамабільныя дарогі", 'List': GetOSM("Р", Relations, "P.csv", Place), },
 'H': { 'Desc': "Мясцовыя аўтамабільныя дарогі", 'List': GetOSM("Н", Relations, "H.csv", Place), },
}
Context['DateTime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
FileNames = ["index.html", "relation.html", "error.html", "missing.html", "index.csv", "relation.csv", "error.csv", "missing.csv", ]
for FileName in FileNames:
 Generate(FileName, Context)

Diff = GitPush(f"autogenerate {datetime.datetime.now().strftime('%Y-%m-%d')}")
if Diff: 
 logger.info(f"git push complete:\n{Diff}")
else:
 logger.error(f"Git error")

logger.info("Done")

#python -m cProfile -s time ./Generate.py
