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
Context['M'] = GetOSM("М", M, "M.csv")
Context['P'] = GetOSM("Р", P, "P.csv")
Context['H'] = GetOSM("Н", H, "H.csv")
Generate(Context)

if GitPush(f"autogenerate 2023-03-14"):
 logger.info("github push Ok")

logger.info("Done")
