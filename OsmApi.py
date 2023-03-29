#https://wiki.openstreetmap.org/wiki/RU:API_v0.6
#https://josm.openstreetmap.de/wiki/Ru%3AHelp/RemoteControlCommands

import sys
import json
import requests
from requests_oauthlib import OAuth2Session


class OsmApi:
 def __init__(self,  HTTPBasic=None, OAuth2=None, CreatedBy="OsmApi/1.0", API="https://www.openstreetmap.org/api/0.6", Referer=None):
  self.API = API.strip('/')
  self.Headers = {'user-agent': CreatedBy}
  if Referer:
   self.Headers['referer'] = Referer
  #
  Auth = "https://api.openstreetmap.org/"
  if OAuth2:
   #OAuth2 = {'client_id': "<client_id>", 'client_secret': "<client_secret>", 'scope': ["read_prefs", "write_notes", ...], 'redirect_uri': "<redirect_uri>"}
   #Register an application with application's name, redirect URIs and scope(s).
   #Then, receive client ID and client secret.
   #Typically, these settings are saved on the client application.
   AuthURL = "https://www.openstreetmap.org/oauth2/authorize"
   AccessTokenURL = "https://www.openstreetmap.org/oauth2/token"
   AuthURL = "https://master.apis.dev.openstreetmap.org/oauth2/authorize"
   AccessTokenURL = "https://master.apis.dev.openstreetmap.org/oauth2/token"
   #When users login from the application, they must first log in to OSM
   #to authenticate their identity by calling the Auth URL and the client
   #application redirects to <REDIRECT_URI>?code=AUTHORIZATION_CODE
   #where the application receives authorization code,
   #(<REDIRECT_URI> is specified during the client application registration)
   self.Requests = OAuth2Session(OAuth2['client_id'], scope=OAuth2['scope'], redirect_uri=OAuth2['redirect_uri'])
   RedirectURL, state = self.Requests.authorization_url(AuthURL)
   print('Please go here and authorize,', RedirectURL)
   #An access token is requested by the client application from the
   #Access Token URL by passing the authorization code along with
   #authentication details, including the client secret.
   RedirectResponse = input('Paste the full redirect URL here:')
   #If the authorization is valid, the OSM API will send the access token
   #to the application as a response. The response will look something
   #like this {"access_token":"<ACCESS_TOKEN>","token_type":"Bearer","scope":"read_prefs write_api","created_at":1646669786}
   token = self.Requests.fetch_token(AccessTokenURL, client_secret=OAuth2['client_secret'], authorization_response=RedirectResponse)
   #Now the application is authorized.
   #It may use the token to access OSM APIs, limited to the scope of access,
   #until the token expires or is revoked.
  else:
   #HTTPBasic = (UserName, Password)
   self.Requests = requests.Session()
   self.Requests.auth = HTTPBasic
   self.Auth = self.Requests.post(Auth)


 def Close(self):
  self.Requests.close()


 def GetJson(self, Type, ID, One=False, Parameters=None, Tag='elements'):
  if isinstance(ID, list):
   List = ",".join([str(Item) for Item in ID])
   URI = f"{self.API}/{Type}.json?{Type}={List}"
  elif isinstance(Parameters, dict):
   List = urllib.parse.urlencode(Parameters)
   if ID is None:
    if List:
     URI = f"{self.API}/{Type}.json?{List}"
    else:
     URI = f"{self.API}/{Type}.json"
   else:
    if List:
     URI = f"{self.API}/{Type}/{ID}.json?{List}"
    else:
     URI = f"{self.API}/{Type}/{ID}.json"
  else:
   if Parameters is not None:
    URI = f"{self.API}/{Type}/{ID}/{Parameters}.json"
   else:
    URI = f"{self.API}/{Type}/{ID}.json"
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


 def GetJsonSimple(self, URI, Params={}, Tag=None):
  with self.Requests.get(URI, headers=self.Headers) as Response:
   Response.encoding = Response.apparent_encoding
   OK, Result = Response.ok, Response.json()
#  print(Result)
  if OK:
   if Tag:
    return Result[Tag]
   else:
    return Result
  else:
   return None


 def PostJson(self, URI, Data):
  with self.Requests.post(URI, data=Data, headers=self.Headers) as Response:
   Response.encoding = Response.apparent_encoding
   OK, Result = Response.ok, Response.json()
  if OK:
   return Result
  else:
   return None


 def GetXML(self, URI):
  with self.Requests.get(URI, headers=self.Headers) as Response:
   Response.encoding = Response.apparent_encoding
   OK, Result = Response.ok, Response.text
  print(Result)
  if OK:
   return Result
  else:
   return None



 ##################################################
 # Miscellaneous                                  #
 ##################################################


#Available API versions: GET /api/versions
#Capabilities: GET /api/capabilities


 #Retrieving map data by bounding box: GET /api/0.6/map
 def Map(self, MinLat, MinLon, MaxLat, MaxLon):
  URI = f"{self.API}/map?bbox={MinLon},{MinLat},{MaxLon},{MaxLat}"
  print(URI)
#  response = self._session.request(method, path, data=send)
#  if response.status_code != 200:
#   payload = response.content.strip()
  with urllib.request.urlopen(URI) as URL:
   return json.load(URL)


 #Retrieving permissions: GET /api/0.6/permissions
 def Permissions(self):
  URI = f"{self.API}/permissions.json"
  return self.GetJsonSimple(URI, Tag='permissions')



 ##################################################
 # Changesets                                     #
 ##################################################


#Create: PUT /api/0.6/changeset/create


 #Read: GET /api/0.6/changeset/#id?include_discussion=true
 def ReadChangeset(self, ID, IncludeDiscussion={}):
  return self.GetJson("changeset", ID, True, Parameters=IncludeDiscussion)


#Update: PUT /api/0.6/changeset/#id
#Close: PUT /api/0.6/changeset/#id/close
#Download: GET /api/0.6/changeset/#id/download


 #Query: GET /api/0.6/changesets
 def QueryChangesets(self, BBox=None, UserID=None, UserName=None, ClosedAfter=None, CreatedBefore=None, OnlyOpen=False, OnlyClosed=False):
 # bbox=min_lon,min_lat,max_lon,max_lat
  URI = f"{self.API}/changesets.json"
  Params = {}
  if BBox:
   Params["bbox"] = ",".join([str(BBox[1]), str(BBox[0]), str(BBox[3]), str(BBox[2])])
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
  return self.GetJsonSimple(URI, Params=Parameters, Tag='changesets')


#Diff upload: POST /api/0.6/changeset/#id/upload



 ##################################################
 # Changeset discussion                           #
 ##################################################


#Comment: POST /api/0.6/changeset/#id/comment
#Subscribe: POST /api/0.6/changeset/#id/subscribe
#Unsubscribe: POST /api/0.6/changeset/#id/unsubscribe
#Hide changeset comment: POST /api/0.6/changeset/comment/#comment_id/hide
#Unhide changeset comment: POST /api/0.6/changeset/comment/#comment_id/unhide




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
 # Elements                                       #
 ##################################################


#Create: PUT /api/0.6/[node|way|relation]/create


 #Read: GET /api/0.6/[node|way|relation]/#id
 #Version: GET /api/0.6/[node|way|relation]/#id/#version
 def Read(self, Type, ID, Version=None):
  return self.GetJson(Type, ID, One=True, Parameters=Version)


#Update: PUT /api/0.6/[node|way|relation]/#id
#Delete: DELETE /api/0.6/[node|way|relation]/#id


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


#Redaction: POST /api/0.6/[node|way|relation]/#id/#version/redact?redaction=#redaction_id



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
 # GPS traces                                     #
 ##################################################


#Get GPS Points: Get /api/0.6/trackpoints?bbox=left,bottom,right,top&page=pageNumber
#Create: POST /api/0.6/gpx/create
#Update: PUT /api/0.6/gpx/#id
#Delete: DELETE /api/0.6/gpx/#id
#Download Metadata: GET /api/0.6/gpx/#id/details
#Download Data: GET /api/0.6/gpx/#id/data
#List: GET /api/0.6/user/gpx_files



 ##################################################
 # Methods for user data                          #
 ##################################################


 #Details of a user: GET /api/0.6/user/#id
 def User(self, ID):
  URI = f"{self.API}/user/{ID}.json"
  return self.GetJsonSimple(URI, Tag='user')


 #Details of multiple users: GET /api/0.6/users?users=#id1,#id2,...,#idn
 def Users(self, IDs):
  List = ",".join([str(Item) for Item in IDs])
  URI = f"{self.API}/users.json?users={List}"
  Json = [Item['user'] for Item in self.GetJsonSimple(URI, Tag='users')]
  Result = list(self.Arrange(IDs, Json))
  return Result


 #Details of the logged-in user: GET /api/0.6/user/details
 def Details(self):
  URI = f"{self.API}/user/details.json"
  return self.GetJsonSimple(URI, Tag='user')


 #Preferences of the logged-in user: GET /api/0.6/preferences
 def Preferences(self):
  URI = f"{self.API}/user/preferences.json"
  return self.GetJsonSimple(URI, Tag='preferences')



 ##################################################
 # Map Notes API                                  #
 ##################################################


 #Retrieving notes data by bounding box: GET /api/0.6/notes
 def ReadNotes(self, MinLat, MinLon, MaxLat, MaxLon, Limit=100, Closed=7):
  URI = f"{self.API}/notes.json?bbox={MinLon},{MinLat},{MaxLon},{MaxLat}&limit={Limit}&closed={Closed}"
  return self.GetJsonSimple(URI, Tag='features')


 #Read: GET /api/0.6/notes/#id
 def ReadNote(self, ID):
  URI = f"{self.API}/notes/{ID}.json"
  return self.GetJsonSimple(URI)


 #Create a new note: Create: POST /api/0.6/notes
 def CreateNote(self, Lat, Lon, Text):
  URI = f"{self.API}/notes.json"
  return self.PostJson(URI, Data={'lat': Lat, 'lon': Lon, 'text': Text})


#Create a new comment: Create: POST /api/0.6/notes/#id/comment
#Close: POST /api/0.6/notes/#id/close
#Reopen: POST /api/0.6/notes/#id/reopen


#Search for notes: GET /api/0.6/notes/search
 def SearchNotes(self, Query="", Limit=100, Closed=7, DisplayName=None, User=None, From=None, To=None, Sort="updated_at", Order="updated_at"):
  Params = {}
  if Query:
   Params['q'] = Query
  if Limit:
   Params['limit'] = Limit
  if Closed:
   Params['closed'] = Closed
  if DisplayName:
   Params['display_name'] = DisplayName
  if User:
   Params['user'] = User
  if From:
   Params['from'] = From
  if To:
   Params['to'] = To
  if Sort:
   Params['sort'] = Sort #created_at or updated_at
  if Order:
   Params['order'] = Order #oldest or newest
  Parameters = urllib.parse.urlencode(Params)
  URI = f"{self.API}/notes/search.json?{Parameters}"
  return self.GetJsonSimple(URI)


 #RSS Feed: GET /api/0.6/notes/feed
 def RSS(self, MinLat, MinLon, MaxLat, MaxLon):
  URI = f"{self.API}/notes/feed?bbox={MinLon},{MinLat},{MaxLon},{MaxLat}"
  return self.GetXML(URI)











##################################################
# Other                                          #
##################################################






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
