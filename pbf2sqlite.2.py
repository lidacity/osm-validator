#https://github.com/osmzoso/osm2sqlite
#https://github.com/ReneNyffenegger/about-Open-Street-Map/blob/master/pbf-parser/pbf2sqlite.py


import os
import sqlite3
import sys
import time

from loguru import logger
from osmiter import iter_from_osm


def Insert(DB, Nodes, NodeTags, Ways, WayNodes, WayTags, Relations, RelationMembers, RelationTags):
 Cursor = DB.cursor()
 if Nodes:
  Cursor.executemany("insert into nodes(node_id, lat, lon) values(?, ?, ?);", Nodes)
 if NodeTags:
  Cursor.executemany("insert into node_tags(node_id, key, value) values(?, ?, ?)", NodeTags)
 if Ways:
  Cursor.executemany("insert into ways(way_id) values(?);", Ways)
 if WayNodes:
  Cursor.executemany("insert into way_nodes(way_id, node_id, node_order) values(?, ?, ?);", WayNodes)
 if WayTags:
  Cursor.executemany("insert into way_tags(way_id, key, value) values(?, ?, ?);", WayTags)
 if Relations:
  Cursor.executemany("insert into relations(relation_id) values(?);", Relations)
 if RelationMembers:
  Cursor.executemany("insert into relation_members(relation_id, type, ref, role, member_order) values(?, ?, ?, ?, ?);", RelationMembers)
 if RelationTags:
  Cursor.executemany("insert into relation_tags(relation_id, key, value) values(?, ?, ?);", RelationTags)
 DB.commit()




def Load(FileName, DB):
 logger.info("PBF to SQLite")

 CountNode = 0
 CountWay = 0
 CountRelation = 0
 Count = 65536

 Nodes, NodeTags, Ways, WayNodes, WayTags, Relations, RelationMembers, RelationTags = [], [], [], [], [], [], [], []
 for Index, Feature in enumerate(iter_from_osm(FileName)):
  if Feature['type'] == "node":
   #{'type': 'node', 'id': 6170308816, 'lat': 53.4249643, 'lon': 27.9164162, 'timestamp': '2021-08-10T18:38:58Z', 'version': 2, 'changeset': 109479484, 'user': 'bad_mapper', 'uid': 10532296}
   CountNode += 1
   if CountNode % Count == 0:
    logger.info(f"Nodes: {CountNode}")
   Nodes.append([Feature['id'], Feature['lat'], Feature['lon']])
   for Key, Value in Feature['tag'].items():
    NodeTags.append([Feature['id'], Key, Value])
  elif Feature['type'] == "way":
   #{'type': 'way', 'id': 657068885, 'timestamp': '2023-04-03T06:47:10Z', 'version': 12, 'changeset': 134439462, 'user': 'LidaCity', 'uid': 505124, 'nodes': [6154280924, 2084768608, 6170308810, 6170308811, 1279651179, 6170308812, 6170308813, 6170308814, 6170308815, 6170308816, 1279651126, 6170308817, 6170308818, 4555396470, 2111299740, 2111299742, 8996766379, 8996766400, 8996766398, 8996766399, 1279651227, 4555395687, 8996769479, 8996769480, 2084768613, 8996769478, 1279651177, 6170309140, 2084768615, 6170309141, 8996769482, 2084768620], 'tags': {'highway': 'tertiary', 'lanes': '2', 'name': 'Цэнтральная вуліца', 'name:be': 'Цэнтральная вуліца', 'name:pl': 'ulica Centralna', 'name:ru': 'Центральная улица', 'ref': 'Н9372', 'surface': 'asphalt'}}
   CountWay += 1
   if CountWay % Count == 0:
    logger.info(f"Ways: {CountWay}")
   Ways.append([Feature['id']])
   Order = 0
   for ID in Feature['nd']:
    WayNodes.append([Feature['id'], ID, Order])
    Order += 1
   for Key, Value in Feature['tag'].items():
    WayTags.append([Feature['id'], Key, Value])
  elif Feature['type'] == "relation":
   #{'type': 'relation', 'id': 14417040, 'timestamp': '2023-04-03T06:47:10Z', 'version': 8, 'changeset': 134439462, 'user': 'LidaCity', 'uid': 505124, 'members': [{'type': 'way', 'ref': 411459436, 'role': ''}, {'type': 'way', 'ref': 411459437, 'role': ''}, {'type': 'way', 'ref': 972063823, 'role': ''}, {'type': 'way', 'ref': 657068885, 'role': ''}, {'type': 'way', 'ref': 112618044, 'role': ''}, {'type': 'way', 'ref': 389432734, 'role': ''}], 'tags': {'name': 'Ліпск – Гарэлец – Ліпнікі – Вомельна', 'name:be': 'Ліпск – Гарэлец – Ліпнікі – Вомельна', 'name:ru': 'Липск – Горелец – Липники – Омельно', 'network': 'by:regional', 'official_ref': 'Н-9372', 'ref': 'Н9372', 'route': 'road', 'type': 'route'}}
   CountRelation += 1
   if CountRelation % Count == 0:
    logger.info(f"Relations: {CountRelation}")
   Relations.append([Feature['id']])
   for Order, Member in enumerate(Feature['member']):
    RelationMembers.append([Feature['id'], Member['type'], Member['ref'], Member['role'], Order])
   for Key, Value in Feature['tag'].items():
    RelationTags.append([Feature['id'], Key, Value])
  if (CountNode + CountWay + CountRelation) % Count == 0:
   #logger.info(f"sql")
   Insert(DB, Nodes, NodeTags, Ways, WayNodes, WayTags, Relations, RelationMembers, RelationTags)
   Nodes, NodeTags, Ways, WayNodes, WayTags, Relations, RelationMembers, RelationTags = [], [], [], [], [], [], [], []
 logger.info(f"total Nodes: {CountNode}")
 logger.info(f"total Ways: {CountWay}")
 logger.info(f"total Relations: {CountRelation}")
 Insert(DB, Nodes, NodeTags, Ways, WayNodes, WayTags, Relations, RelationMembers, RelationTags)
 Nodes, NodeTags, Ways, WayNodes, WayTags, Relations, RelationMembers, RelationTags = [], [], [], [], [], [], [], []

#pbf file loaded, took 1541 seconds 1143
#create Index 183 seconds 160
#100x OsmApi 9
#5000x sqlite3 9

#pbf file loaded, took 11255 seconds 10801
#create Index 479 seconds  461
#100x OsmApi 12
#5000x sqlite3 39



def CreateSchema(DB):
 Cursor = DB.cursor()
 Cursor.execute("create table nodes(node_id integer primary key, lat real not null, lon real not null)")
 Cursor.execute("create table node_tags(node_id integer null references nodes deferrable initially deferred, key text not null, value text not null)")
 Cursor.execute("create table ways(way_id integer primary key)")
 Cursor.execute("create table way_nodes(way_id integer not null references ways deferrable initially deferred, node_id integer not null references nodes deferrable initially deferred, node_order integer not null)")
 Cursor.execute("create table way_tags(way_id integer null references ways deferrable initially deferred, key text not null, value text not null)")
 Cursor.execute("create table relations(relation_id integer primary key)")
 Cursor.execute("create table relation_members(relation_id integer not null references relations deferrable initially deferred, type text not null, ref integer null, role text, member_order integer not null)")
 Cursor.execute("create table relation_tags(relation_id integer null references relations deferrable initially deferred, key text not null, value text not null)")
 DB.commit()


def ExecuteSql(DB, SQL):
 Time = time.time()
 Cursor = DB.cursor()
 Cursor.execute(SQL)
 DB.commit()
 Stop = int(time.time() - Time)
 logger.info(f"{Stop} seconds for {SQL}")



logger.add("pbf2sqlite1.log")
#if len(sys.argv) != 3:
# print "pbf2sqlite.py pbf-file sqlite-db-file"
# sys.exit(0)
#pbf_filename = sys.argv[1] # First argument is *.pbf file name
#db_filename = sys.argv[2] # second argument is *.db file name
pbf_filename = ".data/belarus-latest.osm.pbf"
db_filename = ".data/belarus-latest.osm.db"

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
ExecuteSql(DB, "create index node_tags__node_id on node_tags(node_id)")
ExecuteSql(DB, "create index node_tags__key on node_tags(key)")
ExecuteSql(DB, "create index way_tags__way_id on way_tags(way_id)")
ExecuteSql(DB, "create index way_tags__key on way_tags(key)")
ExecuteSql(DB, "create index relation_tags__relation_id on relation_tags(relation_id)")
ExecuteSql(DB, "create index relation_tags__key on relation_tags(key)")
ExecuteSql(DB, "create index way_nodes__way_id on way_nodes(way_id)")
ExecuteSql(DB, "create index way_nodes__node_id on way_nodes(node_id)")
ExecuteSql(DB, "create index relation_members__relation_id on relation_members(relation_id)")
ExecuteSql(DB, "create index relation_members__type on relation_members(type)")
Stop = int(time.time() - Time)
logger.info(f"create Index {Stop} seconds")
DB.close()
