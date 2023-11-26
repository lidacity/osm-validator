#https://github.com/osmzoso/osm2sqlite
#https://github.com/ReneNyffenegger/about-Open-Street-Map/blob/master/pbf-parser/pbf2sqlite.py

import os
import sys
import sqlite3
import hashlib
import json
import re

import requests
from datetime import datetime
from dateutil.parser import parse as parsedate

from loguru import logger
from osmiter import iter_from_osm as IterFromOsm


sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')



class OsmPbf:
 def __init__(self, URL="https://osm-internal.download.geofabrik.de/europe/belarus-latest-internal.osm.pbf", State="https://osm-internal.download.geofabrik.de/europe/belarus-updates/state.txt", Download=True):
  #URL="https://download.geofabrik.de/europe/belarus-latest.osm.pbf"
  #URL="https://osm-internal.download.geofabrik.de/europe/belarus-latest-internal.osm.pbf"
  #URL="http://osmosis.svimik.com/latest/BY.osm.pbf"
  self.Cookie = {}
  self.DateTime = None
  self.UserAgent = {"User-agent": "https://osm-validator.lidacity.by/"}
  PBF = self.GetFileName(URL)
  FileName = self.ChangeExt(PBF, ".db")
  if Download:
   PasswordFile = {'Type': "PasswordFile", 'FileName': os.path.join(".data", ".passwd")}
   self.Cookie = self.GetCookie(Auth=PasswordFile, Header=self.UserAgent)
   #print(self.Cookie)
   StateFileName = os.path.join(".data", "state.txt")
   self.DateTime = self.ReadState(State, StateFileName)
   if self.Download(URL, PBF) and self.CheckMD5(URL, PBF):
    if os.path.isfile(FileName):
     os.remove(FileName)
   if not os.path.isfile(FileName):
    self.DB = sqlite3.connect(FileName)
    self.DB.text_factory = str
    #self.DB.execute('pragma foreign_keys=on') # Makes inserts slower
    logger.info("Start create .db")
    self.CreateSchema()
    self.Convert(PBF)
    self.CreateIndex()
    logger.info(".db is created")
    self.DB.close()
  #
  self.DB = sqlite3.connect(FileName)


 def Close(self):
  self.DB.close()



 def GetDateTime(self):
  return self.DateTime


 def GetFileName(self, URL):
  _, FileName = os.path.split(URL)
  Path = os.path.dirname(os.path.abspath(__file__))
  return os.path.join(Path, ".data", FileName)


 def ChangeExt(self, FileName, Ext):
  Pre, OldExt = os.path.splitext(FileName)
  return f"{Pre}{Ext}"


 def FindAuthenticityToken(self, Response):
  Pattern = r"name=\"csrf-token\" content=\"([^\"]+)\""
  m = re.search(Pattern, Response)
  if m is None:
   logger.error("Could not find the authenticity_token in the website to be scraped.")
  try:
   return m.group(1)
  except IndexError:
   logger.error("ERROR: The login form does not contain an authenticity_token.")
   exit(1)


 #https://pavie.info/2020/08/12/complete-full-history-osm/
 #https://github.com/geofabrik/sendfile_osm_oauth_protector/
 def GetCookie(self, GEO="https://osm-internal.download.geofabrik.de/get_cookie", Auth=None, OSM="https://www.openstreetmap.org/", Header={}):
  if Auth:
   match Auth['Type']:
    case "HTTPBasic":
     #HTTPBasic = {'UserName': "<username>", 'Password': "<password>", )
     UserName, Password = Auth['UserName'], Auth['Password']
    case "PasswordFile":
     #PasswordFile = {'FileName': "<filename>", )
     #PasswordFile = {'FileName': "<filename>", 'UserName': "<username>", )
     if 'UserName' in Auth:
      UserName = Auth['UserName']
     else:
      with open(Auth['FileName'], "r") as File:
       PassLine = next(File).strip()
      UserName = PassLine.split(":")[0].strip()
     for Line in open(Auth['FileName'], "r"):
      Line = Line.strip().split(":", 1)
      if Line[0] == UserName:
       Password = Line[1]
       break
     else:
      Password = ""
    case _:
     return {}
  else:
   logger.error(f"")
  # get request token
  URL = f"{GEO}?action=request_token"
  Requests = requests.post(URL, data={}, headers=Header)
  if Requests.status_code != 200:
   logger.error(f"POST {URL}, received HTTP status code {Requests.status_code} but expected 200")
  Response = json.loads(Requests.text)
  #URL = f"{OSM}/oauth/authorize"
  try:
   OAuthToken = Response["oauth_token"]
   OAuthTokenSecretEncr = Response["oauth_token_secret_encr"]
  except KeyError:
   logger.error("oauth_token was not found in the first response by the consumer")
  # get OSM session
  URL = f"{OSM}/login?cookie_test=true"
  Session = requests.Session()
  Requests = Session.get(URL, headers=Header)
  if Requests.status_code != 200:
   logger.error(f"GET {URL}, received HTTP code {Requests.status_code}")
  # login
  AuthenticityToken = self.FindAuthenticityToken(Requests.text)
  URL = f"{OSM}/login"
  Requests = Session.post(URL, data={"username": UserName, "password": Password, "referer": "/", "commit": "Login", "authenticity_token": AuthenticityToken}, allow_redirects=False, headers=Header)
  if Requests.status_code != 302:
   logger.error(f"POST {URL}, received HTTP code {Requests.status_code} but expected 302")
  # authorize
  URL = f"{OSM}/oauth/authorize?oauth_token={OAuthToken}"
  Requests = Session.get(URL, headers=Header)
  if Requests.status_code != 200:
   logger.error(f"GET {URL}, received HTTP code {Requests.status_code} but expected 200")
  AuthenticityToken = self.FindAuthenticityToken(Requests.text)
  #
  Data = {"oauth_token": OAuthToken, "oauth_callback": "", "authenticity_token": AuthenticityToken, "allow_read_prefs": [0, 1], "commit": "Save changes"}
  URL = f"{OSM}/oauth/authorize"
  Requests = Session.post(URL, data=Data, headers=Header)
  if Requests.status_code != 200:
   logger.error(f"POST {URL}, received HTTP code {Requests.status_code} but expected 200")
  # logout
  URL = f"{OSM}/logout"
  Requests = Session.get(URL, headers=Header)
  if Requests.status_code != 200 and Requests.status_code != 302:
   logger.error(f"POST {URL}, received HTTP code {Requests.status_code} but expected 200 or 302")
  # get final cookie
  URL = f"{GEO}?action=get_access_token_cookie&format=http"
  Requests = requests.post(URL, data={"oauth_token": OAuthToken, "oauth_token_secret_encr": OAuthTokenSecretEncr}, headers=Header)
  #
  Cookie = Requests.text
  Result = {}
  Key = 'gf_download_oauth'
  for Item in Cookie.split(";"):
   if Item[:len(Key)] == Key:
    _, Value = Item.split("=", 1)
    Result[Key] = Value.strip("\"")
  return Result


 def Download(self, URL, FileName):
  #logger.info(f"Check {FileName}")
  Requests = requests.head(URL, headers=self.UserAgent, cookies=self.Cookie)
  #print(Requests.headers)
  if not self.DateTime:
   self.DateTime = parsedate(Requests.headers['Last-Modified'])
  #
  if os.path.isfile(FileName):
   Result = datetime.fromtimestamp(os.path.getmtime(FileName)).astimezone() < self.DateTime
   if Result:
    os.remove(FileName)
  else:
   Result = True
  #
  if Result:
   logger.info(f"Download {URL}")
   Requests = requests.get(URL, headers=self.UserAgent, stream=True, cookies=self.Cookie)
   with open(FileName, 'wb') as File:
    for Buffer in Requests.iter_content(chunk_size=65536):
     File.write(Buffer)
   logger.info(f"Downloaded {URL}; size = {Requests.headers['Content-Length']}")
  #else:
  # logger.info(f"Skip download {URL}")
  Requests.close()
  return Result


 def md5(self, FileName):
  Result = hashlib.md5()
  with open(FileName, "rb") as File:
   for Chunk in iter(lambda: File.read(4096), b""):
    Result.update(Chunk)
  return Result.hexdigest()


 def CheckMD5(self, URL, FileName):
  self.Download(URL + ".md5", FileName + ".md5")
  logger.info(f"check md5")
  Result = ""
  for Line in open(FileName + ".md5", "r"):
   MD5, Name = Line.split()
   if Name == FileName[-len(Name):]:
    Result = self.md5(FileName)
    if MD5 == Result:
     logger.info(f"md5 Ok")
     return True
  logger.error(f"md5 failed: \"{MD5}\" != \"{Result}\"")
  return False


 def ReadState(self, URL, FileName):
  self.Download(URL, FileName)
  Key = 'timestamp'
  for Line in open(FileName, "r"):
   if Line[:len(Key)] == Key:
    _, Value = Line.replace("\\", "").split("=")
    return parsedate(Value)



 ##################################################
 # Create                                         #
 ##################################################


 def CreateSchema(self):
  logger.info("Create Schema")
  Cursor = self.DB.cursor()
  Cursor.execute("create table nodes(node_id integer primary key, lat real not null, lon real not null, uid integer)")
  Cursor.execute("create table node_tags(node_id integer null references nodes deferrable initially deferred, key text not null, value text not null)")
  Cursor.execute("create table ways(way_id integer primary key, uid integer)")
  Cursor.execute("create table way_nodes(way_id integer not null references ways deferrable initially deferred, node_id integer not null references nodes deferrable initially deferred, node_order integer not null)")
  Cursor.execute("create table way_tags(way_id integer null references ways deferrable initially deferred, key text not null, value text not null)")
  Cursor.execute("create table relations(relation_id integer primary key, uid integer)")
  Cursor.execute("create table relation_members(relation_id integer not null references relations deferrable initially deferred, type text not null, ref integer null, role text, member_order integer not null)")
  Cursor.execute("create table relation_tags(relation_id integer null references relations deferrable initially deferred, key text not null, value text not null)")
  self.DB.commit()


 def Convert(self, FileName):
  logger.info("PBF to SQLite3")
  Cursor = self.DB.cursor()
  CountNode, CountWay, CountRelation = 0, 0, 0
  Count = 65536
  #
  n, w, r = True, True, True
  for Feature in IterFromOsm(FileName):
   if Feature['type'] == "node":
    if n:
     print(Feature)
     n = False
    CountNode += 1
    Cursor.execute("insert into nodes(node_id, lat, lon, uid) values(?, ?, ?, ?);", [Feature['id'], Feature['lat'], Feature['lon'], Feature['uid']])
    for Key, Value in Feature['tag'].items():
     Cursor.execute("insert into node_tags(node_id, key, value) values(?, ?, ?);", [Feature['id'], Key, Value])
   elif Feature['type'] == "way":
    if w:
     print(Feature)
     w = False
    CountWay += 1
    Cursor.execute("insert into ways(way_id, uid) values(?, ?);", [Feature['id'], Feature['uid']])
    Order = 0
    for ID in Feature['nd']:
     Cursor.execute("insert into way_nodes(way_id, node_id, node_order) values(?, ?, ?);", [Feature['id'], ID, Order])
     Order += 1
    for Key, Value in Feature['tag'].items():
     Cursor.execute("insert into way_tags(way_id, key, value) values(?, ?, ?);", [Feature['id'], Key, Value])
   elif Feature['type'] == "relation":
    if r:
     print(Feature)
     r = False
    CountRelation += 1
    Cursor.execute("insert into relations(relation_id, uid) values(?, ?);", [Feature['id'], Feature['uid']])
    for Order, Member in enumerate(Feature['member']):
     Cursor.execute("insert into relation_members(relation_id, type, ref, role, member_order) values(?, ?, ?, ?, ?);", [Feature['id'], Member['type'], Member['ref'], Member['role'], Order])
    for Key, Value in Feature['tag'].items():
     Cursor.execute("insert into relation_tags(relation_id, key, value) values(?, ?, ?);", [Feature['id'], Key, Value])
   #
   if (CountNode + CountWay + CountRelation) % Count == 0:
    self.DB.commit()
  #
  self.DB.commit()
  logger.info(f"total Nodes: {CountNode}, Ways: {CountWay}, Relations: {CountRelation}")


 def CreateIndex(self):
  logger.info("Create index")
  Cursor = self.DB.cursor()
  Cursor.execute("create index node_tags__node_id on node_tags(node_id)")
  Cursor.execute("create index node_tags__key on node_tags(key)")
  Cursor.execute("create index way_tags__way_id on way_tags(way_id)")
  Cursor.execute("create index way_tags__key on way_tags(key)")
  Cursor.execute("create index relation_tags__relation_id on relation_tags(relation_id)")
  Cursor.execute("create index relation_tags__key on relation_tags(key)")
  Cursor.execute("create index way_nodes__way_id on way_nodes(way_id)")
  Cursor.execute("create index way_nodes__node_id on way_nodes(node_id)")
  Cursor.execute("create index relation_members__relation_id on relation_members(relation_id)")
  Cursor.execute("create index relation_members__type on relation_members(type)")
  self.DB.commit()


 ##################################################
 # Node                                           #
 ##################################################


 def ReadNode(self, ID):
  Result = {'type': "node", 'id': ID, }
  Result['lat'], Result['lon'], Result['uid'] = self.ExecuteOne("SELECT lat, lon, uid FROM nodes WHERE node_id = ?;", Params=[ID])
  Result['tags'] = { Key: Value for Key, Value in self.Execute("SELECT key, value FROM node_tags WHERE node_id = ?;", Params=[ID]) }
  return Result


 def ReadNodes(self, List):
  return [self.ReadNode(ID) for ID in List]


 def RelationsForNode(self, ID):
  return [self.ReadRelation(ID) for ID, in self.Execute("SELECT relation_id FROM relation_members WHERE ref = ? AND type = 'node' ORDER BY member_order;", Params=[ID])]


 def GetNodeKey(self, Key, Values=[]):
  return [self.ReadNode(ID) for ID, _, Value in self.Execute("SELECT node_id, key, value FROM node_tags WHERE key = ?;", Params=[Key]) if not Values or Value in Values]


# #Ways for node: GET /api/0.6/node/#id/ways
# def WaysForNode(self, ID):
#  URI = f"{self.API}/node/{ID}/ways.json"
#  return self.GetJson(URI, Tag='elements')


 ##################################################
 # Way                                            #
 ##################################################


 def ReadWay(self, ID):
  Result = {'type': "way", 'id': ID, }
  Result['uid'], = self.ExecuteOne("SELECT uid FROM ways WHERE way_id = ?;", Params=[ID])
  Result['tags'] = { Key: Value for Key, Value in self.Execute("SELECT key, value FROM way_tags WHERE way_id = ?;", Params=[ID]) }
  Result['nodes'] = [ Node[0] for Node in self.Execute("SELECT node_id FROM way_nodes WHERE way_id = ? ORDER BY node_order;", Params=[ID]) ]
  return Result


 def ReadWays(self, List):
  return [self.ReadWay(ID) for ID in List]


 def RelationsForWay(self, ID):
  return [self.ReadRelation(ID) for ID, in self.Execute("SELECT relation_id FROM relation_members WHERE ref = ? AND type = 'way' ORDER BY member_order;", Params=[ID])]


 def GetWayKey(self, Key, Values=[]):
  return [self.ReadWay(ID) for ID, _, Value in self.Execute("SELECT way_id, key, value FROM way_tags WHERE key = ?;", Params=[Key]) if not Values or Value in Values]


# #Full: GET /api/0.6/[way|relation]/#id/full
# def FullWay(self, ID):
#  return self.Full("way", ID)


 ##################################################
 # Relation                                       #
 ##################################################


 def ReadRelation(self, ID):
  Result = {'type': "relation", 'id': ID, }
  Result['uid'], = self.ExecuteOne("SELECT uid FROM relations WHERE relation_id = ?;", Params=[ID])
  Result['tags'] = { Key: Value for Key, Value in self.Execute("SELECT key, value FROM relation_tags WHERE relation_id = ?;", Params=[ID]) }
  Result['members'] = [ { 'type': Type, 'ref': Ref, 'role': Role } for Type, Ref, Role in self.Execute("SELECT type, ref, role FROM relation_members WHERE relation_id = ? ORDER BY member_order;", Params=[ID]) ]
  return Result


 def ReadRelations(self, List):
  return [self.ReadRelation(ID) for ID in List]


 def RelationsForRelation(self, ID):
  return [self.ReadRelation(ID) for ID, in self.Execute("SELECT relation_id FROM relation_members WHERE ref = ? AND type = 'relation' ORDER BY member_order;", Params=[ID])]


 def GetRelationKey(self, Key, Values=[]):
  return [self.ReadRelation(ID) for ID, _, Value in self.Execute("SELECT relation_id, key, value FROM relation_tags WHERE key = ?;", Params=[Key]) if not Values or Value in Values]


 def GetRelationMembers(self, ID):
  return self.Execute("SELECT type, ref, role FROM relation_members WHERE relation_id = ? AND type = 'relation' ORDER BY member_order;", Params=[ID])


# def FullRelation(self, ID):
#  return self.Full("relation", ID)


 ##################################################
 # Feature                                        #
 ##################################################


 def RelationsForFeature(self, ID):
  return [self.ReadRelation(ID) for ID, in self.Execute("SELECT relation_id FROM relation_members WHERE ref = ? ORDER BY member_order;", Params=[ID])]


 ##################################################
 # Misc                                           #
 ##################################################


 def Execute(self, SQL, Params=[]):
  Cursor = self.DB.cursor()
  Cursor.execute(SQL, Params)
  return Cursor.fetchall()


 def ExecuteOne(self, SQL, Params=[]):
  Cursor = self.DB.cursor()
  Cursor.execute(SQL, Params)
  return Cursor.fetchone()
