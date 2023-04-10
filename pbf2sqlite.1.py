#https://github.com/ReneNyffenegger/about-Open-Street-Map/blob/master/pbf-parser/pbf2sqlite.py

import os
import sqlite3
import sys
import time

from loguru import logger
from osmiter import iter_from_osm




def Load(FileName, DB):
 logger.info("PBF to SQLite")

 Cursor = DB.cursor()

 CountNode = 0
 CountWay = 0
 CountRelation = 0
 Count = 65536

 for Index, Feature in enumerate(iter_from_osm(FileName)):
#  Cursor.execute('SELECT * FROM way')
#  S = Cursor.fetchall()
#  print(S)
#  ID  = 65536
#  Cursor.execute("insert or replace into way(id) values (?)", [ID])
#  DB.commit()
#  Cursor.execute('SELECT * FROM way')
#  S = Cursor.fetchall()
#  print(S)
#  DB.close()
#  sys.exit()
  if Feature['type'] == "node":
   #{'type': 'node', 'id': 6170308816, 'lat': 53.4249643, 'lon': 27.9164162, 'timestamp': '2021-08-10T18:38:58Z', 'version': 2, 'changeset': 109479484, 'user': 'bad_mapper', 'uid': 10532296}
   CountNode += 1
   if CountNode % Count == 0:
    logger.info(f"Nodes: {CountNode}")
    DB.commit()
   Cursor.execute("insert into node(id, lat, lon) values(?, ?, ?)", [Feature['id'], Feature['lat'], Feature['lon']])
   for Key, Value in Feature['tag'].items():
    Cursor.execute("insert into tag(node_id, k, v) values(?, ?, ?)", [Feature['id'], Key, Value])
  elif Feature['type'] == "way":
   #{'type': 'way', 'id': 657068885, 'timestamp': '2023-04-03T06:47:10Z', 'version': 12, 'changeset': 134439462, 'user': 'LidaCity', 'uid': 505124, 'nodes': [6154280924, 2084768608, 6170308810, 6170308811, 1279651179, 6170308812, 6170308813, 6170308814, 6170308815, 6170308816, 1279651126, 6170308817, 6170308818, 4555396470, 2111299740, 2111299742, 8996766379, 8996766400, 8996766398, 8996766399, 1279651227, 4555395687, 8996769479, 8996769480, 2084768613, 8996769478, 1279651177, 6170309140, 2084768615, 6170309141, 8996769482, 2084768620], 'tags': {'highway': 'tertiary', 'lanes': '2', 'name': 'Цэнтральная вуліца', 'name:be': 'Цэнтральная вуліца', 'name:pl': 'ulica Centralna', 'name:ru': 'Центральная улица', 'ref': 'Н9372', 'surface': 'asphalt'}}
   CountWay += 1
   if CountWay % Count == 0:
    logger.info(f"Ways: {CountWay}")
    DB.commit()
   Cursor.execute("insert into way(id) values(?)", [Feature['id']])
   Order = 0
   for ID in Feature['nd']:
    Cursor.execute("insert into node_in_way(way_id, node_id, order_) values(?, ?, ?)", [Feature['id'], ID, Order])
    Order += 1
   for Key, Value in Feature['tag'].items():
    Cursor.execute("insert into tag(way_id, k, v) values(?, ?, ?)", [Feature['id'], Key, Value])
  elif Feature['type'] == "relation":
   #{'type': 'relation', 'id': 14417040, 'timestamp': '2023-04-03T06:47:10Z', 'version': 8, 'changeset': 134439462, 'user': 'LidaCity', 'uid': 505124, 'members': [{'type': 'way', 'ref': 411459436, 'role': ''}, {'type': 'way', 'ref': 411459437, 'role': ''}, {'type': 'way', 'ref': 972063823, 'role': ''}, {'type': 'way', 'ref': 657068885, 'role': ''}, {'type': 'way', 'ref': 112618044, 'role': ''}, {'type': 'way', 'ref': 389432734, 'role': ''}], 'tags': {'name': 'Ліпск – Гарэлец – Ліпнікі – Вомельна', 'name:be': 'Ліпск – Гарэлец – Ліпнікі – Вомельна', 'name:ru': 'Липск – Горелец – Липники – Омельно', 'network': 'by:regional', 'official_ref': 'Н-9372', 'ref': 'Н9372', 'route': 'road', 'type': 'route'}}
   CountRelation += 1
   if CountRelation % Count == 0:
    logger.info(f"Relations: {CountRelation}")
    DB.commit()
   Cursor.execute("insert into relation(id) values(?)", [Feature['id']])
   for Member in Feature['member']:
    if Member['type'] == 'node':
     Cursor.execute("insert into member_in_relation(id_of_relation, node_id, role) values(?, ?, ?)", [Feature['id'], Member['ref'], Member['role']])
    elif Member['type'] == 'way':
     Cursor.execute("insert into member_in_relation(id_of_relation, way_id, role) values(?, ?, ?)", [Feature['id'], Member['ref'], Member['role']])
    elif Member['type'] == 'relation': 
     Cursor.execute("insert into member_in_relation(id_of_relation, relation_id, role) values(?, ?, ?)", [Feature['id'], Member['ref'], Member['role']])
    else:
     logger.error(f"unexpected type: {Member['type']}")
   for Key, Value in Feature['tag'].items():
    Cursor.execute("insert into tag(relation_id, k, v) values(?, ?, ?)", [Feature['id'], Key, Value])
 logger.info(f"total Nodes: {CountNode}")
 logger.info(f"total Ways: {CountWay}")
 logger.info(f"total Relations: {CountRelation}")
 DB.commit()


def CreateSchema(DB):
 Cursor = DB.cursor()
 Cursor.execute("create table node(id integer primary key, lat real not null, lon real not null)")
 Cursor.execute("create table way(id integer primary key)")
 Cursor.execute("create table relation(id integer primary key)")
 Cursor.execute("create table node_in_way(way_id integer not null references way deferrable initially deferred, node_id integer not null references node deferrable initially deferred, order_ integer not null)")
 Cursor.execute("create table member_in_relation(id_of_relation integer not null references relation deferrable initially deferred, node_id integer null references node deferrable initially deferred, way_id integer null references way deferrable initially deferred,relation_id integer null references relation deferrable initially deferred, role text)")
 Cursor.execute("create table tag(node_id integer null references node deferrable initially deferred, way_id integer null references way deferrable initially deferred, relation_id integer null references relation deferrable initially deferred, k text not null, v text not null)")
 DB.commit()


def ExecuteSql(DB, SQL):
 Time = time.time()
 Cursor = DB.cursor()
 Cursor.execute(SQL)
 DB.commit()
 Stop = int(time.time() - Time)
 logger.info(f"{Stop} seconds for {SQL}")



logger.add("pbf2sqlite.log")
#if len(sys.argv) != 3:
# print "pbf2sqlite.py pbf-file sqlite-db-file"
# sys.exit(0)
#pbf_filename = sys.argv[1] # First argument is *.pbf file name
#db_filename = sys.argv[2] # second argument is *.db file name
pbf_filename = ".data/belarus-latest.osm.pbf"
db_filename = ".data/belarus-latest.osm.sqlite"

# delete db if exists
if os.path.isfile(db_filename):
 os.remove(db_filename)

DB = sqlite3.connect(db_filename)
DB.text_factory = str

# Makes inserts slower, so comment it:
# db.execute('pragma foreign_keys=on')


CreateSchema(DB)

Time = time.time()
Load(pbf_filename, DB)
Stop = int(time.time() - Time)
logger.info(f"pbf file loaded, took {Stop} seconds")


Time = time.time()
ExecuteSql(DB, "create index node_in_way__way_id on node_in_way(way_id)")
ExecuteSql(DB, "create index node_in_way__node_id on node_in_way(node_id)")
ExecuteSql(DB, "create index tag__v on tag(v)")
ExecuteSql(DB, "create index tag__k_v on tag(k, v)")
ExecuteSql(DB, "create index tag__node_id on tag(node_id)")
ExecuteSql(DB, "create index tag__way_id on tag(way_id)")
ExecuteSql(DB, "create index tag__relation_id on tag(relation_id)")
ExecuteSql(DB, "create index member_in_relation__node_id on member_in_relation(node_id)")
ExecuteSql(DB, "create index member_in_relation__way_id on member_in_relation(way_id)")
ExecuteSql(DB, "create index member_in_relation__relation_id on member_in_relation(relation_id)")
Stop = int(time.time() - Time)
logger.info(f"create Index {Stop} seconds")
DB.close()
