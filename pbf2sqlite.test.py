#https://github.com/ReneNyffenegger/about-Open-Street-Map/blob/master/pbf-parser/pbf2sqlite.py
#https://renenyffenegger.blogspot.com/2014/09/openstreetmap-convert-pbf-to-sqlite.html
#https://github.com/osmzoso/osm2sqlite


import os
import sqlite3
import sys
import time

from loguru import logger
from osmiter import iter_from_osm
from OsmApi import OsmApi




def ExecuteSql(DB, SQL):
 Time = time.time()
 Cursor = DB.cursor()
 Cursor.execute(SQL)
 DB.commit()
 Stop = int(time.time() - Time)
 logger.info(f"{Stop} seconds for {SQL}")



logger.add("pbf2sqlite.log")
logger.info(f"Start")
Time = time.time()
OSM = OsmApi()
for x in range(100):
 S = OSM.ReadRelation(78041)
OSM.Close()
Stop = int(time.time() - Time)
logger.info(f"100x OsmApi {Stop}")
#print(S)
#sys.exit()

Time = time.time()
db_filename = ".data/belarus-latest.osm.db"
DB = sqlite3.connect(db_filename)
#DB.text_factory = str
Cursor = DB.cursor()

for x in range(2000):
 ID = 78041
 Result = {'type': "relation", 'id': ID, }
 Cursor.execute("SELECT key, value FROM relation_tags WHERE relation_id = ?;", [ID])
 Result['tags'] = { Key: Value for Key, Value in Cursor.fetchall() }
 Cursor.execute("SELECT type, ref, role FROM relation_members WHERE relation_id = ? ORDER BY member_order;", [ID])
 Result['members'] = [ { 'type': Type, 'ref': Ref, 'role': Role } for Type, Ref, Role in Cursor.fetchall() ]
DB.close()

Stop = int(time.time() - Time)
logger.info(f"5000x sqlite3 {Stop}")
#print(Result)

#{'type': 'relation', 'id': 78041, 'timestamp': '2023-03-28T07:11:21Z', 'version': 345, 'changeset': 134205990, 'user': 'LidaCity', 'uid': 505124, 'members': [{'type': 'way', 'ref': 127025053, 'role': ''}, 
#{'type': 'way', 'ref': 282927316, 'role': ''}], 'tags': {'distance': '611 km', 'int_name': 'Brest (Kazlovičy) — Minsk — miaža Rasijskaj Federacyi (Redźki)', 'loc_name': 'Олимпийка', 'name': 'Брэст (Казловічы) – Мінск – мяжа Расійскай Федэрацыі (Рэдзькі)', 'name:be': 'Брэст (Казловічы) – Мінск – мяжа Расійскай Федэрацыі (Рэдзькі)', 'name:lt': 'Brestas — Minskas — Rusijos Federacijos siena', 'name:pl': 'Brześć (Kozłowicze) — Mińsk — granica Federacji Rosyjskiej', 'name:ru': 'Брест (Козловичи) – Минск – граница Российской Федерации (Редьки)', 'network': 'by:national', 'official_ref': 'М-1/Е 30', 'ref': 'М1', 'route': 'road', 'type': 'route', 'wikidata': 'Q267850', 'wikipedia': 'be:Магістраль М1'}}

