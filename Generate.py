#!.venv/bin/python

import os
import sys
from datetime import datetime

from loguru import logger

from Pravo import GetPravo
from Route import Generate as GetRouteContext
from Boundary import Generate as GetBoundaryContext
from RouteBus import Generate as GetRouteBusContext

from Jinja2 import Generate
from Git import GitPush


sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

Path = os.path.dirname(os.path.abspath(__file__))
logger.add(os.path.join(Path, ".log", "osm.log"))
logger.info("Start")

Directory = os.path.join(Path, ".data")
if not os.path.exists(Directory):
 os.makedirs(Directory)

# type=boundary
BY = 59065
List = ["boundary"]
Context = GetBoundaryContext(BY)
Generate(List, Context)

# type=master_route
List = ["route"]
Context = GetRouteBusContext()
Generate(List, Context)

# type=route
Route = {
 'M': { 'Cyr': "М", 'Lat': "M", 'ID': 1246287, 'FileName': "M.csv", 'Main': True, 'Desc': "Магістральныя аўтамабільныя дарогі" },
 'P': { 'Cyr': "Р", 'Lat': "P", 'ID': 1246288, 'FileName': "P.csv", 'Main': True, 'Desc': "Рэспубліканскія аўтамабільныя дарогі" },
 'H': { 'Cyr': "Н", 'Lat': "H", 'ID': 1246286, 'FileName': "H.csv", 'Main': False, 'Desc': "Мясцовыя аўтамабільныя дарогі" },
}
Network = {False: 'Рэспубліканскія аўтамабільныя дарогі', True: 'Мясцовыя аўтамабільныя дарогі'}
List = ["index", "highway", "error", "relation", "separated", "network", "missing", "index.old"]
Context = GetRouteContext(Route, Network)
Context['PravoError'], Context['Pravo'] = GetPravo()
Generate(List, Context)

# git

Diff = GitPush(f"autogenerate {datetime.now().strftime('%Y-%m-%d')}")
if Diff:
 pass #logger.info(f"git push complete:\n{Diff}")
else:
 logger.error(f"Git error")

logger.info("Done")

#python -m cProfile -s time ./Generate.py
