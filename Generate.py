#!.venv/bin/python

import os
import sys
from datetime import datetime

from loguru import logger

from Pravo import GetPravo
from OSM import Validator


sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

Path = os.path.dirname(os.path.abspath(__file__))
logger.add(os.path.join(Path, ".log", "osm.log"))
logger.info("Start")

Directory = os.path.join(Path, ".data")
if not os.path.exists(Directory):
 os.makedirs(Directory)

Check = {
 'M': { 'Cyr': "М", 'Lat': "M", 'ID': 1246287, 'FileName': "M.csv", 'Main': True, 'Desc': "Магістральныя аўтамабільныя дарогі" },
 'P': { 'Cyr': "Р", 'Lat': "P", 'ID': 1246288, 'FileName': "P.csv", 'Main': True, 'Desc': "Рэспубліканскія аўтамабільныя дарогі" },
 'H': { 'Cyr': "Н", 'Lat': "H", 'ID': 1246286, 'FileName': "H.csv", 'Main': False, 'Desc': "Мясцовыя аўтамабільныя дарогі" },
}

List = ["index", "highway", "error", "relation", "separated", "network", "missing"]

Validator = Validator()
Context = {}

#Context['PravoError'], Context['Pravo'] = False, []
#Context['Highway'] = {}
#Context['Relation'] = {}
#Context['Separated'] = []
#Context['Missing'] = { 'Relations': [], 'Ways': {}, 'RelationsForWays': {} }
#Context['Network'] = {}
#Context['PBFDateTime'] = Validator.GetDateTime()
#Context['DateTime'] = Validator.GetNow()

Context['PravoError'], Context['Pravo'] = GetPravo()
Highway = Validator.GetHighway(Check)
Context['Highway'] = Highway
Context['Error'] = Validator.GetError(Highway)
Context['Relation'] = Validator.GetRelation(Highway)
Context['Separated'] = Validator.GetSeparated(Check)
Context['Missing'] = Validator.GetMissing([Item['ID'] for _, Item in Check.items()])
Network = Validator.GetNetwork(Check, False)
NetworkFull = Validator.GetNetwork(Check, True)
Context['Network'] = { 'Рэспубліканскія аўтамабільныя дарогі': Network, 'Мясцовыя аўтамабільныя дарогі': NetworkFull }
Context['PBFDateTime'] = Validator.GetDateTime()
Context['DateTime'] = Validator.GetNow()

Validator.Generate(List, Context)

Diff = Validator.GitPush(f"autogenerate {datetime.now().strftime('%Y-%m-%d')}")
if Diff: 
 pass #logger.info(f"git push complete:\n{Diff}")
else: 
 logger.error(f"Git error")

logger.info("Done")

#python -m cProfile -s time ./Generate.py
