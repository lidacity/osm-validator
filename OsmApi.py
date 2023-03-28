#https://wiki.openstreetmap.org/wiki/RU:API_v0.6
#https://josm.openstreetmap.de/wiki/Ru%3AHelp/RemoteControlCommands

import sys
import json
import requests


class OsmApi:
 def __init__(self, UserName=None, Password=None, OAuth=None, CreatedBy="OsmApi/1.0", API="https://openstreetmap.org/api/0.6", Referer=None):
  self.API = API.strip('/')
  self.Headers = {'user-agent': CreatedBy}
  if Referer:
   self.Headers['referer'] = Referer
  #
  self.Requests = requests.Session()
  if OAuth:
   self.OAuth = OAuth
  else:
   self.OAuth = None
   self.UserName, self.Password = UserName, Password

#  self.Requests = requests



 def Close(self):
  self.Requests.close()


 def GetJson(self, Type, ID, One=False, Parameters=None, Tag='elements'):
  API = self.API
  if isinstance(ID, list):
   List = ",".join([str(Item) for Item in ID])
   URI = f"{API}/{Type}.json?{Type}={List}"
  elif isinstance(Parameters, dict):
   List = urllib.parse.urlencode(Parameters)
   if ID is None:
    if List:
     URI = f"{API}/{Type}.json?{List}"
    else:
     URI = f"{API}/{Type}.json"
   else:
    if List:
     URI = f"{API}/{Type}/{ID}.json?{List}"
    else:
     URI = f"{API}/{Type}/{ID}.json"
  else:
   if Parameters is not None:
    URI = f"{API}/{Type}/{ID}/{Parameters}.json"
   else:
    URI = f"{API}/{Type}/{ID}.json"
  #print(URI)
  with self.Requests.get(URI, headers=self.Headers) as Response:
   Response.encoding = Response.apparent_encoding
   OK, Result = Response.ok, Response.json()
  if OK:
   if One:
    return Result[Tag][0]
   else:
    return Result[Tag]
  else:
   return None


 ##################################################
 # Capabilities                                   #
 ##################################################


 #def Capabilities():
 # uri = "/api/capabilities"


 ##################################################
 # Node|Way|Relation                              #
 ##################################################


 #Read: GET /api/0.6/[node|way|relation]/#id
 #Version: GET /api/0.6/[node|way|relation]/#id/#version
 def Read(self, Type, ID, Version=None):
  return self.GetJson(Type, ID, One=True, Parameters=Version)


 #History: GET /api/0.6/[node|way|relation]/#id/history
 def History(self, Type, ID):
  return self.GetJson(Type, ID, Parameters="history")


 def Arrange(self, List, Dict):
  for ID in List:
   for Item in Dict:
    if Item['id'] == ID:
     yield Item
     break


 #Multi fetch: GET /api/0.6/[nodes|ways|relations]?#parameters
 def MultiFetch(self, Type, IDs):
  Json = self.GetJson(Type, IDs)
  Result = list(self.Arrange(IDs, Json))
  return Result


 #Relations for element: GET /api/0.6/[node|way|relation]/#id/relations
 def RelationsForElement(self, Type, ID):
  return self.GetJson(Type, ID, Parameters="relations")


 #Full: GET /api/0.6/[way|relation]/#id/full
 def Full(self, Type, ID):
  return self.GetJson(Type, ID, Parameters="full")


 ##################################################
 # Node                                           #
 ##################################################


 #Read: GET /api/0.6/[node|way|relation]/#id
 #Version: GET /api/0.6/[node|way|relation]/#id/#version
 def ReadNode(self, ID, Version=None):
  return self.Read("node", ID, Version=Version)


 #History: GET /api/0.6/[node|way|relation]/#id/history
 def HistoryNode(self, ID):
  return self.History("node", ID)


 #Multi fetch: GET /api/0.6/[nodes|ways|relations]?#parameters
 def ReadNodes(self, IDs):
  return self.MultiFetch("nodes", IDs)


 #Relations for element: GET /api/0.6/[node|way|relation]/#id/relations
 def RelationsForNode(self, ID):
  return self.RelationsForElement("node", ID)


 #Ways for node: GET /api/0.6/node/#id/ways
 def WaysForNode(self, ID):
  return self.GetJson("node", ID, Parameters="ways")


 #def NodeCreate(self, NodeData):
 # return self._do("create", "node", NodeData)

 #def NodeUpdate(self, NodeData):
 # return self._do("modify", "node", NodeData)

 #def NodeDelete(self, NodeData):
 # return self._do("delete", "node", NodeData)



 ##################################################
 # Way                                            #
 ##################################################


 #Read: GET /api/0.6/[node|way|relation]/#id
 #Version: GET /api/0.6/[node|way|relation]/#id/#version
 def ReadWay(self, ID, Version=None):
  return self.Read("way", ID, Version=Version)


 #History: GET /api/0.6/[node|way|relation]/#id/history
 def HistoryWay(self, ID):
  return self.History("way", ID)


 #Multi fetch: GET /api/0.6/[nodes|ways|relations]?#parameters
 def ReadWays(self, IDs):
  return self.MultiFetch("ways", IDs)


 #Relations for element: GET /api/0.6/[node|way|relation]/#id/relations
 def RelationsForWay(self, ID):
  return self.RelationsForElement("way", ID)


 #Full: GET /api/0.6/[way|relation]/#id/full
 def FullWay(self, ID):
  return self.Full("node", ID)


 #def WayCreate(self, WayData):
 # return self._do("create", "way", WayData)

 #def WayUpdate(self, WayData):
 # return self._do("modify", "way", WayData)

 #def WayDelete(self, WayData):
 # return self._do("delete", "way", WayData)



 ##################################################
 # Relation                                       #
 ##################################################


 #Read: GET /api/0.6/[node|way|relation]/#id
 #Version: GET /api/0.6/[node|way|relation]/#id/#version
 def ReadRelation(self, ID, Version=None):
  return self.Read("relation", ID, Version=Version)


 #History: GET /api/0.6/[node|way|relation]/#id/history
 def HistoryRelation(self, ID):
  return self.History("relation", ID)


 #Multi fetch: GET /api/0.6/[nodes|ways|relations]?#parameters
 def ReadRelations(self, IDs):
  return self.MultiFetch("relations", IDs)


 #Relations for element: GET /api/0.6/[node|way|relation]/#id/relations
 def RelationsForRelation(self, ID):
  return self.RelationsForElement("relation", ID)


 #Full: GET /api/0.6/[way|relation]/#id/full
 def FullRelation(self, ID):
  return self.Full("relation", ID)


#def FullRelationRecur(ID):
# Result = []
# Todo, Done = [ID], []
# while Todo:
#  Rid = Todo.pop(0)
#  Done.append(Rid)
#  Temp = FullRelation(Rid)
#  for Item in Temp:
#   if Item["type"] != "relation":
#    continue
#   if Item["data"]["id"] in Done:
#    continue
#   Todo.append(Item["data"]["id"])
#  Result += Temp
# return Result


 #def RelationCreate(self, RelationData):
 # return self._do("create", "relation", RelationData)

 #def RelationUpdate(self, RelationData):
 # return self._do("modify", "relation", RelationData)

 #def RelationDelete(self, RelationData):
 # return self._do("delete", "relation", RelationData)



 ##################################################
 # Changeset                                      #
 ##################################################

 #Retrieving permissions: GET /api/0.6/permissions
 def Permissions(self, Tag='permissions'):
  API = self.API
  URI = f"{API}/permissions.json"
  with self.Requests.get(URI, headers=self.Headers) as Response:
   Response.encoding = Response.apparent_encoding
   OK, Result = Response.ok, Response.json()
  if OK:
   return Result[Tag]
  else:
   return None











 ##################################################
 # Changeset                                      #
 ##################################################
 #Hide changeset comment: POST /api/0.6/changeset/comment/#comment_id/hide (JSON response)
 #Unhide changeset comment: POST /api/0.6/changeset/comment/#comment_id/unhide (JSON response)


 #def Changeset(self, ChangesetTags={}):
 # #Create a new changeset


 #Read: GET /api/0.6/changeset/#id?include_discussion=true
 def ReadChangeset(self, ID, IncludeDiscussion={}):
  return self.GetJson("changeset", ID, True, Parameters=IncludeDiscussion)


 #def ChangesetUpdate(self, ChangesetTags={}):
 # #Updates current changeset with `ChangesetTags`.

 #def ChangesetCreate(self, ChangesetTags={}):
 # Opens a changeset.

 #def ChangesetClose(self):
 # #Closes current changeset.

 #def ChangesetUpload(self, ChangesData):
 # #Upload data with the `ChangesData` list of dicts:

 #def ChangesetDownload(self, ChangesetId):
 # #Download data from changeset `ChangesetId`.


 #Query: GET /api/0.6/changesets
 def QueryChangesets(self, bbox=None, UserID=None, UserName=None, ClosedAfter=None, CreatedBefore=None, OnlyOpen=False, OnlyClosed=False):
 # bbox=min_lon,min_lat,max_lon,max_lat
  Params = {}
  if bbox:
   Params["bbox"] = bbox
  if UserID:
   Params["user"] = UserID
  if UserName:
   Params["display_name"] = UserName
  if ClosedAfter and not CreatedBefore:
   Params["time"] = ClosedAfter
  if CreatedBefore:
   if not ClosedAfter:
    ClosedAfter = "1970-01-01T00:00:00Z"
   Params["time"] = f"{ClosedAfter},{CreatedBefore}"
  if OnlyOpen:
   Params["open"] = 1
  if OnlyClosed:
   Params["closed"] = 1
  return self.GetJson("changesets", None, Parameters=Params, Tag='changesets')


#Comment: POST /api/0.6/changeset/#id/comment (JSON response)
#def CommentChangeset(ChangesetId, comment):
#        params = urllib.parse.urlencode({'text': comment})
#        try:
#            data = self._session._post(
#                "/api/0.6/changeset/%s/comment" % (ChangesetId),
#                params,
#                forceAuth=True
#            )
#        except errors.ApiError as e:
#            if e.status == 409:
#                raise errors.ChangesetClosedApiError(e.status, e.reason, e.payload)
#            else:
#                raise
#        changeset = dom.OsmResponseToDom(data, tag="changeset", single=True)
#        return dom.DomParseChangeset(changeset)


#Subscribe: POST /api/0.6/changeset/#id/subscribe (JSON response)
#    def ChangesetSubscribe(self, ChangesetId):
#        try:
#            data = self._session._post(
#                "/api/0.6/changeset/%s/subscribe" % (ChangesetId),
#                None,
#                forceAuth=True
#            )
#        except errors.ApiError as e:
#            if e.status == 409:
#                raise errors.AlreadySubscribedApiError(e.status, e.reason, e.payload)
#            else:
#                raise
#        changeset = dom.OsmResponseToDom(data, tag="changeset", single=True)
#        return dom.DomParseChangeset(changeset)


#Unsubscribe: POST /api/0.6/changeset/#id/unsubscribe (JSON response)
#    def ChangesetUnsubscribe(self, ChangesetId):
#        try:
#            data = self._session._post(
#                "/api/0.6/changeset/%s/unsubscribe" % (ChangesetId),
#                None,
#                forceAuth=True
#            )
#        except errors.ElementNotFoundApiError as e:
#            raise errors.NotSubscribedApiError(e.status, e.reason, e.payload)
#
#        changeset = dom.OsmResponseToDom(data, tag="changeset", single=True)
#        return dom.DomParseChangeset(changeset)


##################################################
# Notes                                          #
##################################################

#Retrieving notes data by bounding box: GET /api/0.6/notes
#    def NotesGet(min_lon, min_lat, max_lon, max_lat, limit=100, closed=7):
#        uri = (
#            "/api/0.6/notes?bbox=%f,%f,%f,%f&limit=%d&closed=%d"
#            % (min_lon, min_lat, max_lon, max_lat, limit, closed)
#        )
#        data = self._session._get(uri)
#        return parser.ParseNotes(data)

#Read: GET /api/0.6/notes/#id
#    def NoteGet(self, id):
#        uri = "/api/0.6/notes/%s" % (id)
#        data = self._session._get(uri)
#        noteElement = dom.OsmResponseToDom(data, tag="note", single=True)
#        return dom.DomParseNote(noteElement)

#Create a new note: Create: POST /api/0.6/notes
#    def NoteCreate(self, NoteData):
#        uri = "/api/0.6/notes"
#        uri += "?" + urllib.parse.urlencode(NoteData)
#        return self._NoteAction(uri)

#    def NoteComment(self, NoteId, comment):
#        path = "/api/0.6/notes/%s/comment" % NoteId
#        return self._NoteAction(path, comment)

#    def NoteClose(self, NoteId, comment):
#        path = "/api/0.6/notes/%s/close" % NoteId
#        return self._NoteAction(path, comment, optionalAuth=False)

#    def NoteReopen(self, NoteId, comment):
#        path = "/api/0.6/notes/%s/reopen" % NoteId
#        return self._NoteAction(path, comment, optionalAuth=False)

#Search for notes: GET /api/0.6/notes/search
#    def NotesSearch(self, query, limit=100, closed=7):
#        uri = "/api/0.6/notes/search"
#        params = {}
#        params['q'] = query
#        params['limit'] = limit
#        params['closed'] = closed
#        uri += "?" + urllib.parse.urlencode(params)
#        data = self._session._get(uri)
#        return parser.ParseNotes(data)


##################################################
# Other                                          #
##################################################


 #Retrieving map data by bounding box: GET /api/0.6/map
 def Map(self, MinLon, MinLat, MaxLon, MaxLat):
  API = self.API
  URI = f"{API}/map?bbox={MinLon},{MinLat},{MaxLon},{MaxLat}"
  print(URI)
#  response = self._session.request(method, path, data=send)
#  if response.status_code != 200:
#   payload = response.content.strip()
  with urllib.request.urlopen(URI) as URL:
   return json.load(URL)


##################################################
# Internal method                                #
##################################################
#Retrieving permissions: GET /api/0.6/permissions
#Methods for user data
#Details of a user: GET /api/0.6/user/#id
#Details of multiple users: GET /api/0.6/users?users=#id1,#id2,...,#idn
#Details of the logged-in user: GET /api/0.6/user/details
#Preferences of the logged-in user: GET /api/0.6/preferences



##################################################


class CacheIterator:

 # захаваць прамежуткавыя значэнні
 def __init__(self, Count, Array, Type=["node", "way", "relation"], Role=[]):
  self.OSM = OsmApi()
  self.Count = Count
  self.Array = Array
  self.IncludeType = Type
  self.ExcludeRole = Role
  self.Type = ""
  self.Iters = self.GetIters()
  self.i = 0
  self.j = 0
  self.Cache = {}


 # абнавіць значэнне і вярнуць вынік
 def __next__(self):
  i, j = self.i, self.j
  IsCache = self.j == 0
  #
  if self.i > len(self.Iters) - 1:
   self.Iters = self.GetIters()
   i, j = self.i, self.j = 0, 0
  if self.j < len(self.Iters[i]) - 1:
   self.j += 1
  else:
   self.i += 1
   self.j = 0
  #
  if IsCache:
   self.Cache = self.GetCache(self.Iters[i])
  #
  return self.Type, self.Cache[j]
 

 def GetCache(self, IDs):
  if self.Type == "node":
   return self.OSM.ReadNodes(IDs)
  elif self.Type == "way":
   return self.OSM.ReadWays(IDs)
  elif self.Type == "relation":
   return self.OSM.ReadRelations(IDs)
  else:
   raise "Error!"


 def GetIters(self):
  if self.Type == "":
   self.Type = "node"
   if self.Type in self.IncludeType:
    self.Iters = self.GetItems("node")
   else:
    return self.GetIters()
  elif self.Type == "node":
   self.Type = "way"
   if self.Type in self.IncludeType:
    self.Iters = self.GetItems("way")
   else:
    return self.GetIters()
  elif self.Type == "way":
   self.Type = "relation"
   if self.Type in self.IncludeType:
    self.Iters = self.GetItems("relation")
   else:
    return self.GetIters()
  else:
   self.OSM.Close()
   raise StopIteration
  #
  if self.Iters:
   return self.Iters
  else:
   return self.GetIters()


 def GetItems(self, Type):
  Result = []
  Index, Items = 0, []
  for Item in self.Array:
   if Item['type'] == Type and Item['role'] not in self.ExcludeRole:
    Items.append(Item['ref'])
    if Index >= self.Count - 1:
     Result.append(Items)
     Index, Items = 0, []
    else:
     Index += 1
  if Items:
   Result.append(Items)
  return Result


 def __iter__(self):
  return self


#


class ArrayCacheIterator:

 # захаваць прамежуткавыя значэнні
 def __init__(self, Count, Array, Type):
  self.OSM = OsmApi()
  self.Count = Count
  self.Array = Array
  self.Type = Type
  self.Iters = self.GetItems()
  self.i = 0
  self.j = 0
  self.Cache = {}


 # абнавіць значэнне і вярнуць вынік
 def __next__(self):
  i, j = self.i, self.j
  IsCache = self.j == 0
  #
  if self.i > len(self.Iters) - 1:
   self.OSM.Close()
   raise StopIteration
  if self.j < len(self.Iters[i]) - 1:
   self.j += 1
  else:
   self.i += 1
   self.j = 0
  #
  if IsCache:
   self.Cache = self.GetCache(self.Iters[i])
  #
  return self.Cache[j]
 

 def GetCache(self, IDs):
  if self.Type == "node":
   return self.OSM.ReadNodes(IDs)
  elif self.Type == "way":
   return self.OSM.ReadWays(IDs)
  elif self.Type == "relation":
   return self.OSM.ReadRelations(IDs)
  else:
   raise "Error!"


 def GetItems(self):
  Result = []
  Index, Items = 0, []
  for Item in self.Array:
   Items.append(Item)
   if Index >= self.Count - 1:
    Result.append(Items)
    Index, Items = 0, []
   else:
    Index += 1
  if Items:
   Result.append(Items)
  #
  return Result


 def __iter__(self):
  return self
