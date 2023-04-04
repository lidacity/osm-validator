#https://wiki.openstreetmap.org/wiki/API_v0.6
#https://josm.openstreetmap.de/wiki/Ru%3AHelp/RemoteControlCommands

import sys
import json
import requests
from requests_oauthlib import OAuth1Session
from requests_oauthlib import OAuth2Session


class OsmApi:
 def __init__(self,  Auth=None, CreatedBy="OsmApi/1.0", API="https://api.openstreetmap.org/api/0.6", Referer=None):
  self.API = API.strip('/')
  self.Headers = {'user-agent': CreatedBy}
  if Referer:
   self.Headers['referer'] = Referer
  #
  if Auth:
   match Auth['Type']:
    case "OAuth1":
     #OAuth1 = {'client_key': "<client_key>", 'client_secret': "<client_secret>", }
     self.Requests = OAuth1Session(Auth['client_key'], client_secret=Auth['client_secret'])
     FetchResponse = self.Requests.fetch_request_token(Auth['RequestTokenURL'])
     ResourceOwnerKey = FetchResponse.get('oauth_token')
     ResourceOwnerSecret = FetchResponse.get('oauth_token_secret')
     AuthorizationURL = self.Requests.authorization_url(Auth['AuthorizeURL'])
     print("Please go here and authorize,", AuthorizationURL)
     RedirectResponse = input('Paste the full redirect URL here: ')
     OAuthResponse = self.Requests.parse_authorization_response(RedirectResponse)
     Verifier = OAuthResponse.get('oauth_token') #oauth_verifier
     self.Requests = OAuth1Session(Auth['client_key'], client_secret=Auth['client_secret'], resource_owner_key=ResourceOwnerKey, resource_owner_secret=ResourceOwnerSecret, verifier=Verifier)
     OAuthTokens = self.Requests.fetch_access_token(Auth['AccessTokenURL'])
     ResourceOwnerKey = OAuthTokens.get('oauth_token')
     ResourceOwnerSecret = OAuthTokens.get('oauth_token_secret')
     self.Requests = OAuth1Session(Auth['client_key'], client_secret=Auth['client_secret'], resource_owner_key=ResourceOwnerKey, resource_owner_secret=ResourceOwnerSecret)
    case "OAuth2":
     #OAuth2 = {'client_id': "<client_id>", 'client_secret': "<client_secret>", 'scope': ["read_prefs", "write_notes", ...], 'redirect_uri': "<redirect_uri>", }
     self.Requests = OAuth2Session(Auth['client_id'], scope=Auth['scope'], redirect_uri=Auth['redirect_uri'])
     RedirectURL, state = self.Requests.authorization_url(Auth['AuthURL'])
     print("Please go here and authorize,", RedirectURL)
     RedirectResponse = input('Paste the full redirect URL here:')
     token = self.Requests.fetch_token(Auth['AccessTokenURL'], client_secret=Auth['client_secret'], authorization_response=RedirectResponse)
    case "HTTPBasic":
     #HTTPBasic = {'UserName': "<username>", 'Password': "<password>", )
     self.Requests = requests.Session()
     self.Requests.auth = (Auth['UserName'], Auth['Password'])
     self.Auth = self.Requests.post(Auth['AuthURL'])
    case "PasswordFile":
     #PasswordFile = {'FileName': "<filename>", <<'UserName': "<username>">>, )
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
     self.Requests = requests.Session()
     self.Requests.auth = (UserName, Password)
     self.Auth = self.Requests.post(Auth['AuthURL'])
  else:
   self.Requests = requests.Session()


 def Close(self):
  self.Requests.close()


 def GetError(self, Response):
  return {'code': Response.status_code, 'error': Response.text, 'url': Response.url}
  #Response.raise_for_status()


 def GetJson(self, URI, Params={}, Single=False, Tag=None):
  with self.Requests.get(URI, params=Params, headers=self.Headers) as Response:
   Response.encoding = Response.apparent_encoding
   #print(Response.request.url)
   #print(Result)
   if Response.ok:
    Result = Response.json()
    if Tag:
     return Result[Tag][0] if Single else Result[Tag]
    else:
     return Result
   else:
    return self.GetError(Response)


 def PostJson(self, URI, Data={}):
  with self.Requests.post(URI, data=Data, headers=self.Headers) as Response:
   Response.encoding = Response.apparent_encoding
   return Response.json() if Response.ok else self.GetError(Response)


 def GetXML(self, URI, Params={}):
  with self.Requests.get(URI, params=Params, headers=self.Headers) as Response:
   Response.encoding = Response.apparent_encoding
   OK, Result = Response.ok, Response.text
   #print(Result)
  if OK:
   return Result
  else:
   return None


 def GetBBox(self, Box):
  """
  Convert human bbox to osm bbox
  (min_lat,min_lon,max_lat,max_lon -> min_lon,min_lat,max_lon,max_lat)
  """
  return ",".join([str(Box[i]) for i in [1, 0, 3, 2]])


 ##################################################
 # Miscellaneous                                  #
 ##################################################


#Available API versions: GET /api/versions
#Capabilities: GET /api/capabilities


 #Retrieving map data by bounding box: GET /api/0.6/map
 def Map(self, BBox):
  """
  === Retrieving map data by bounding box: GET /api/0.6/map.json ===
  The following command returns:
  * All nodes that are inside a given bounding box and any relations that
    reference them.
  * All ways that reference at least one node that is inside a given bounding
    box, any relations that reference them [the ways], and any nodes outside
    the bounding box that the ways may reference.
  * All relations that reference one of the nodes, ways or relations included
    due to the above rules. (Does '''not''' apply recursively, see explanation
    below.)

  GET /api/0.6/map?bbox.json=left,bottom,right,top
  where:
  * left is the longitude of the left (westernmost) side of the bounding box.
  * bottom is the latitude of the bottom (southernmost) side of the bounding
    box.
  * right is the longitude of the right (easternmost) side of the bounding box.
  * top is the latitude of the top (northernmost) side of the bounding box.

  Note that, while this command returns those relations that reference the
  aforementioned nodes and ways, the reverse is not true: it does not
  (necessarily) return all of the nodes and ways that are referenced by these
  relations. This prevents unreasonably-large result sets.
  For example, imagine the case where:
  * There is a relation named "England" that references every node in England.
  * The nodes, ways, and relations are retrieved for a bounding box that covers
    a small portion of England.

  While the result would include the nodes, ways, and relations as specified by
  the rules for the command, including the "England" relation, it would
  (fortuitously) 'not' include 'every' node and way in England.
  If desired, the nodes and ways referenced by the "England" relation could be
  retrieved by their respective IDs.

  Also note that ways which intersect the bounding box but have no nodes within
  the bounding box will not be returned.

  ==== Error codes ====
  ; HTTP status code 400 (Bad Request) : When any of the node/way/relation
    limits are exceeded, in particular if the call would return more than
    50'000 nodes.
    See above for other uses of this code.
  ; HTTP status code 509 (Bandwidth Limit Exceeded) : "Error:  You have
    downloaded too much data. Please try again later."
  """
  Parameters = {}
  Parameters['bbox'] = self.GetBBox(BBox)
  URI = f"{self.API}/map.json"
  return self.GetJson(URI, Params=Parameters, Tag='elements')


 #Retrieving permissions: GET /api/0.6/permissions
 def Permissions(self):
  """
  === Retrieving permissions: GET /api/0.6/permissions.json ===
  Returns the permissions granted to the current API connection.
  * If the API client is not authorized, an empty list of permissions will be
    returned.
  * If the API client uses Basic Auth, the list of permissions will contain
    all permissions.
  * If the API client uses OAuth 1.0a, the list will contain the permissions
    actually granted by the user.
  * If the API client uses OAuth 2.0, the list will be based on the granted
    scopes.

  Note that for compatibility reasons, all OAuth 2.0 scopes will be prefixed by
  "allow_", e.g. scope "read_prefs" will be shown as permission
  "allow_read_prefs".

  ==== Response ====
  GET /api/0.6/permissions.json
  Returns the single permissions element containing the permission tags
  {
   'version': "0.6",
   'generator': "OpenStreetMap server",
   'permissions': ["allow_read_prefs", ..., "allow_read_gpx", "allow_write_gpx"]
  }

  ==== Notes ====
  Currently the following permissions can appear in the result, corresponding
  directly to the ones used in the OAuth 1.0a application definition:
  * allow_read_prefs (read user preferences)
  * allow_write_prefs (modify user preferences)
  * allow_write_diary (create diary entries, comments and make friends)
  * allow_write_api (modify the map)
  * allow_read_gpx (read private GPS traces)
  * allow_write_gpx (upload GPS traces)
  * allow_write_notes (modify notes)
  """
  URI = f"{self.API}/permissions.json"
  return self.GetJson(URI, Tag='permissions')



 ##################################################
 # Changesets                                     #
 ##################################################


#Create: PUT /api/0.6/changeset/create


 #Read: GET /api/0.6/changeset/#id?include_discussion=true
 def ReadChangeset(self, ID, IncludeDiscussion=None):
  """
  === Read: GET /api/0.6/changeset/#id.json?include_discussion=true ===
  Returns the changeset with the given #id in JSON format.

  ==== Parameters ====
  ; id : The id of the changeset to retrieve
  ; include_discussion : Indicates whether the result should contain the
    changeset discussion or not. If this parameter is set to anything, the
    discussion is returned. If it is empty or omitted, the discussion will
    not be in the result.

  ==== Response ====
  Returns the single changeset element containing the changeset tags with a
  content type of application/json
  GET /api/0.6/changeset/#id.json?include_discussion=true
  {
   'version': "0.6",
   'generator': "CGImap 0.8.8 (3466634 spike-08.openstreetmap.org)",
   'elements':
   [
    {
     'type': "changeset",
     'id': 10,
     'created_at': "2005-05-01T16:09:37Z",
     'closed_at': "2005-05-01T17:16:44Z",
     'open': False,
     'user': "Petter Reinholdtsen",
     'uid': 24,
     'minlat': 59.9513092,
     'minlon': 10.7719727,
     'maxlat': 59.9561501,
     'maxlon': 10.7994537,
     'comments_count': 1,
     'changes_count': 10,
     'discussion':
     [
      {
       'date': "2022-03-22T20:58:30Z",
       'uid': 15079200,
       'user': "Ethan White of Cheriton",
       'text': "wow no one have said anything here 3/22/2022\n"
      }
     ]
    }
   ]
  }

  ==== Error codes ====
  ; HTTP status code 404 (Not Found) : When no changeset with the given id
    could be found

  ==== Notes ====
  * The uid might not be available for changesets auto generated by the API
    v0.5 to API v0.6 transition?
  * The bounding box attributes will be missing for an empty changeset.
  * The changeset bounding box is a rectangle that contains the bounding boxes
    of all objects changed in this changeset. It is not necessarily the
    smallest possible rectangle that does so.
  * This API call only returns information about the changeset itself but not
    the actual changes made to elements in this changeset. To access this
    information use the 'download' API call.
  """
  Parameters = {}
  if IncludeDiscussion:
   Parameters['include_discussion'] = IncludeDiscussion
  URI = f"{self.API}/changeset/{ID}.json"
  return self.GetJson(URI, Params=Parameters, Tag='elements')


#Update: PUT /api/0.6/changeset/#id
#Close: PUT /api/0.6/changeset/#id/close
#Download: GET /api/0.6/changeset/#id/download


 #Query: GET /api/0.6/changesets
 def QueryChangesets(self, BBox=None, UserID=None, UserName=None, ClosedAfter=None, CreatedBefore=None, OnlyOpen=False, OnlyClosed=False):
  """
  === Query: GET /api/0.6/changesets.json ===
  This is an API method for querying changesets. It supports querying by
  different criteria.

  Where multiple queries are given the result will be those which match all of
  the requirements.
  The contents of the returned document are the changesets and their tags.
  To get the full set of changes associated with a changeset, use the
  'download' method on each changeset ID individually.

  Modification and extension of the basic queries above may be required to
  support rollback and other uses we find for changesets.

  This call returns at most 100 changesets matching criteria, it returns latest
  changesets ordered by created_at.

  ==== Parameters ====
  ; bbox=min_lon,min_lat,max_lon,max_lat (W,S,E,N) : Find changesets within the
    given bounding box
  ; user=#uid 'or' display_name=#name : Find changesets by the user with the
    given user id or display name. Providing both is an error.
  ; time=T1 : Find changesets 'closed' after T1
  ; time=T1,T2 : Find changesets that were 'closed' after T1 and 'created'
    before T2. In other words, any changesets that were open 'at some time'
    during the given time range T1 to T2.
  ; open=true : Only finds changesets that are still 'open' but excludes
    changesets that are closed or have reached the element limit for a
    changeset (10.000 at the moment)
  ; closed=true : Only finds changesets that are 'closed' or have reached the
    element limit
  ; changesets=#cid{,#cid} : Finds changesets with the specified ids
    Time format:
    Anything that this Ruby function will parse.
    The default str is ’-4712-01-01T00:00:00+00:00’; this is Julian Day Number
    day 0.

  ==== Response ====
  Returns a list of all changeset ordered by creation date.
  The json element may be empty if there were no results for the query.
  The response is sent with a content type of application/json

  ==== Error codes ====
  ; HTTP status code 400 (Bad Request) - text/plain : On misformed parameters.
    A text message explaining the error is returned. In particular, trying to
    provide both the UID and display name as user query parameters will result
    in this error.
  ; HTTP status code 404 (Not Found) : When no user with the given uid or
    display_name could be found.

  ==== Notes ====
  * Only changesets by public users are returned.
  * Returns at most 100 changesets
  """
  URI = f"{self.API}/changesets.json"
  Parameters = {}
  if BBox:
   Parameters["bbox"] = self.GetBBox(BBox)
  if UserID:
   Parameters["user"] = UserID
  if UserName:
   Parameters["display_name"] = UserName
  if ClosedAfter and not CreatedBefore:
   Parameters["time"] = ClosedAfter
  if CreatedBefore:
   if not ClosedAfter:
    ClosedAfter = "1970-01-01T00:00:00Z"
   Parameters["time"] = f"{ClosedAfter},{CreatedBefore}"
  if OnlyOpen:
   Parameters["open"] = 1
  if OnlyClosed:
   Parameters["closed"] = 1
  return self.GetJson(URI, Params=Parameters, Tag='changesets')


#Diff upload: POST /api/0.6/changeset/#id/upload



 ##################################################
 # Changeset discussion                           #
 ##################################################


 #Comment: POST /api/0.6/changeset/#id/comment
 def CommentChangeset(self, ID, Text):
  """
  === Comment: POST /api/0.6/changeset/#id/comment.json ===
  Add a comment to a changeset. The changeset must be closed.

  ==== Requests ====
  POST /api/0.6/changeset/#id/comment.json
  Body content: {'test': "Test"}

  Return type: application/json
  {
   'version': "0.6",
   'generator': "OpenStreetMap server",
   'changeset':
   {
    'id': 257934,
    'created_at': "2023-03-29T17:26:28Z",
    'open': False,
    'comments_count': 1,
    'changes_count': 2,
    'closed_at': "2023-03-29T17:26:30Z",
    'min_lat': -22.5779486,
    'min_lon': 18.5373289,
    'max_lat': 75.2958681,
    'max_lon': 134.8229272,
    'uid': 14235,
    'user': "OrganicMapsTestUser",
    'tags':
    {
     'created_by': "OMaps Unit Test",
     'comment': "For test purposes only (updated)."
    }
   }
  }

  This request needs to be done as an authenticated user.

  ==== Parameters ====
  ; text : The comment text.
    The content type is "application/x-www-form-urlencoded".

  ==== Error codes ====
  ; HTTP status code 400 (Bad Request) : if the text field was not present
  ; HTTP status code 409 (Conflict) : The changeset is not closed
  """
  URI = f"{self.API}/changeset/{ID}/comment.json"
  Data = {'text': Text}
  return self.PostJson(URI, Data=Data, Tag='changeset')


 #Subscribe: POST /api/0.6/changeset/#id/subscribe
 def SubscribeChangeset(self, ID):
  """
  === Subscribe: POST /api/0.6/changeset/#id/subscribe.json ===
  Subscribe to the discussion of a changeset to receive notifications
  for new comments.

  ==== Requests ====
  POST /api/0.6/changeset/#id/subscribe.json

  Return type: application/json
  {
   'version': "0.6",
   'generator': "OpenStreetMap server",
   'changeset':
   {
    'id': 257934,
    'created_at': "2023-03-29T17:26:28Z",
    'open': False,
    'comments_count': 1,
    'changes_count': 2,
    'closed_at': "2023-03-29T17:26:30Z",
    'min_lat': -22.5779486,
    'min_lon': 18.5373289,
    'max_lat': 75.2958681,
    'max_lon': 134.8229272,
    'uid': 14235,
    'user': 'OrganicMapsTestUser',
    'tags':
    {
     'created_by': "OMaps Unit Test",
     'comment': "For test purposes only (updated)."
    }
   }
  }

  This request needs to be done as an authenticated user.

  ==== Error codes ====
  ; HTTP status code 409 (Conflict) : if the user is already subscribed to this
    changeset
  """
  URI = f"{self.API}/changeset/{ID}/subscribe.json"
  return self.PostJson(URI, Tag='changeset')


 #Unsubscribe: POST /api/0.6/changeset/#id/unsubscribe
 def UnsubscribeChangeset(self, ID):
  """
  === Unsubscribe: POST /api/0.6/changeset/#id/unsubscribe.json ===
  Unsubscribe from the discussion of a changeset to stop receiving
  notifications.

  ==== Requests ====
  POST /api/0.6/changeset/#id/subscribe.json

  Return type: application/json
  {
   'version': "0.6",
   'generator': "OpenStreetMap server",
   'changeset':
   {
    'id': 257934,
    'created_at': "2023-03-29T17:26:28Z",
    'open': False,
    'comments_count': 1,
    'changes_count': 2,
    'closed_at': "2023-03-29T17:26:30Z",
    'min_lat': -22.5779486,
    'min_lon': 18.5373289,
    'max_lat': 75.2958681,
    'max_lon': 134.8229272,
    'uid': 14235,
    'user': "OrganicMapsTestUser",
    'tags':
    {
     'created_by': "OMaps Unit Test",
     'comment': "For test purposes only (updated)."
    }
   }
  }

  This request needs to be done as an authenticated user.

  ==== Error codes ====
  ; HTTP status code 404 (Not Found) : if the user is not subscribed to this
    changeset
  """
  URI = f"{self.API}/changeset/{ID}/unsubscribe.json"
  return self.PostJson(URI, Tag='changeset')


 #Hide changeset comment: POST /api/0.6/changeset/comment/#comment_id/hide
 def HideComment(self, ID):
  """
  === Hide changeset comment: POST /api/0.6/changeset/comment/#comment_id/hide.json ===
  Sets visible flag on changeset comment to false. 

  POST /api/0.6/changeset/comment/#comment_id/hide.json
  Return type: application/json

  This request needs to be done as an authenticated user with moderator role.

  Note that the changeset comment id differs from the changeset id.

  ==== Error codes ====
  ; HTTP status code 403 (Forbidden) : if the user is not a moderator
  ; HTTP status code 404 (Not Found) : if the changeset comment id is unknown
  """
  URI = f"{self.API}/changeset/comment/{ID}/hide.json"
  return self.PostJson(URI)


 #Unhide changeset comment: POST /api/0.6/changeset/comment/#comment_id/unhide
 def UnhideComment(self, ID):
  """
  === Unhide changeset comment: POST /api/0.6/changeset/comment/#comment_id/unhide.json ===
  Sets visible flag on changeset comment to true.

  POST /api/0.6/changeset/comment/#comment_id/unhide.json
  Return type: application/json

  This request needs to be done as an authenticated user with moderator role.

  Note that the changeset comment id differs from the changeset id.

  ==== Error codes ====
  ; HTTP status code 403 (Forbidden) : if the user is not a moderator
  ; HTTP status code 404 (Not Found) : if the changeset comment id is unknown
  """
  URI = f"{self.API}/changeset/comment/{ID}/unhide.json"
  return self.PostJson(URI)



 ##################################################
 # Elements                                       #
 ##################################################


#Create: PUT /api/0.6/[node|way|relation]/create


 #Read: GET /api/0.6/[node|way|relation]/#id
 def Read(self, Type, ID):
  """
  === Read: GET /api/0.6/[node|way|relation]/#id.json ===
  Returns the JSON representation of the element.

  ==== Response ====
  GET /api/0.6/[node|way|relation]/#id.json
  JSON representing the element, wrapped in an <json> element:
  {
   'version': "0.6",
   'elements':
   [
    {
     'type': "node",
     'id': 4326396331,
     'lat': 31.9016302,
     'lon': -81.5990471,
     'timestamp': '2016-07-31T00:08:11Z',
     'version': 2,
     'changeset': 41136027,
     'user': 'maven149',
     'uid': 136601
    }
   ]
  }

  ==== Error codes ====
  ; HTTP status code 404 (Not Found) : When no element with the given id could
    be found
  ; HTTP status code 410 (Gone) : If the element has been deleted
  """
  URI = f"{self.API}/{Type}/{ID}.json"
  return self.GetJson(URI, Single=True, Tag='elements')


#Update: PUT /api/0.6/[node|way|relation]/#id
#Delete: DELETE /api/0.6/[node|way|relation]/#id


 #History: GET /api/0.6/[node|way|relation]/#id/history
 def History(self, Type, ID):
  """
  === History: GET /api/0.6/[node|way|relation]/#id/history.json ===
  Retrieves all old versions of an element.

  ==== Error codes ====
  ; HTTP status code 404 (Not Found) : When no element with the given id could
    be found
  """
  URI = f"{self.API}/{Type}/{ID}/history.json"
  return self.GetJson(URI, Tag='elements')


 #Version: GET /api/0.6/[node|way|relation]/#id/#version
 def Version(self, Type, ID, Version):
  """
  === Version: GET /api/0.6/[node|way|relation]/#id/#version.json ===
  Retrieves a specific version of the element.

  ==== Error codes ====
  ; HTTP status code 403 (Forbidden) : When the version of the element is not
    available (due to redaction)
  ; HTTP status code 404 (Not Found) : When no element with the given id could
    be found
  """
  URI = f"{self.API}/{Type}/{ID}/{Version}.json"
  return self.GetJson(URI, Single=True, Tag='elements')


 def Arrange(self, List, Dict):
  for ID in List:
   for Item in Dict:
    if Item['id'] == ID:
     yield Item
     break


 #Multi fetch: GET /api/0.6/[nodes|ways|relations]?#parameters
 def MultiFetch(self, Types, IDs):
  """
  === Multi fetch: GET /api/0.6/[nodes|ways|relations].json?#parameters ===
  Allows a user to fetch multiple elements at once.

  ==== Parameters ====
  ; [nodes|ways|relations]=comma separated list : The parameter has to be the
    same in the URL (e.g. /api/0.6/nodes.json?nodes=123,456,789)
    Version numbers for each object may be optionally provided following a
    lowercase "v" character, e.g. /api/0.6/nodes?nodes=421586779v1,421586779v2

  ==== Error codes ====
  ; HTTP status code 400 (Bad Request) : On a malformed request (parameters
    missing or wrong)
  ; HTTP status code 404 (Not Found) : If one of the elements could not be
    found (By "not found" is meant never existed in the database, if the object
    was deleted, it will be returned with the attribute visible="false")
  ; HTTP status code 414 (Request-URI Too Large) : If the URI was too long
    (tested to be > 8213 characters in the URI, or > 725 elements for 10 digit
    IDs when not specifying versions)

  ==== Notes ====
  As the multi fetch call returns deleted objects it is the practical way to
  determine the version at which an object was deleted (useful for example for
  conflict resolution), the alternative to using this would be the history call
  that however may potentially require 1000's of version to be processed.
  """
  URI = f"{self.API}/{Types}.json"
  List = ",".join([str(Item) for Item in IDs])
  Parameters = {f'{Types}': List}
  Json = self.GetJson(URI, Params=Parameters, Tag='elements')
  Result = list(self.Arrange(IDs, Json))
  return Result


 #Relations for element: GET /api/0.6/[node|way|relation]/#id/relations
 def RelationsForElement(self, Type, ID):
  """
  === Relations for element: GET /api/0.6/[node|way|relation]/#id/relations.json ===
  Returns a JSON document containing all (not deleted) relations in which the
  given element is used.

  ==== Notes ====
  * There is no error if the element does not exist.
  * If the element does not exist or it isn't used in any relations an empty
    JSON document is returned (apart from the {} elements)
  """
  URI = f"{self.API}/{Type}/{ID}/relations.json"
  return self.GetJson(URI, Tag='elements')


 #Full: GET /api/0.6/[way|relation]/#id/full
 def Full(self, Type, ID):
  URI = f"{self.API}/{Type}/{ID}/full.json"
  return self.GetJson(URI, Tag='elements')


#Redaction: POST /api/0.6/[node|way|relation]/#id/#version/redact?redaction=#redaction_id



 ##################################################
 # Node                                           #
 ##################################################


 #Read: GET /api/0.6/[node|way|relation]/#id
 def ReadNode(self, ID):
  return self.Read("node", ID)


 #History: GET /api/0.6/[node|way|relation]/#id/history
 def HistoryNode(self, ID):
  return self.History("node", ID)


 #Version: GET /api/0.6/[node|way|relation]/#id/#version
 def VersionNode(self, ID, Version):
  return self.Version("node", ID, Version)


 #Relations for element: GET /api/0.6/[node|way|relation]/#id/relations
 def RelationsForNode(self, ID):
  return self.RelationsForElement("node", ID)


 #Ways for node: GET /api/0.6/node/#id/ways
 def WaysForNode(self, ID):
  URI = f"{self.API}/node/{ID}/ways.json"
  return self.GetJson(URI, Tag='elements')


 #Multi fetch: GET /api/0.6/[nodes|ways|relations]?#parameters
 def ReadNodes(self, IDs):
  return self.MultiFetch("nodes", IDs)



 ##################################################
 # Way                                            #
 ##################################################


 #Read: GET /api/0.6/[node|way|relation]/#id
 def ReadWay(self, ID):
  return self.Read("way", ID)


 #History: GET /api/0.6/[node|way|relation]/#id/history
 def HistoryWay(self, ID):
  return self.History("way", ID)


 #Version: GET /api/0.6/[node|way|relation]/#id/#version
 def VersionWay(self, ID, Version):
  return self.Version("way", ID, Version)


 #Multi fetch: GET /api/0.6/[nodes|ways|relations]?#parameters
 def ReadWays(self, IDs):
  return self.MultiFetch("ways", IDs)


 #Relations for element: GET /api/0.6/[node|way|relation]/#id/relations
 def RelationsForWay(self, ID):
  return self.RelationsForElement("way", ID)


 #Full: GET /api/0.6/[way|relation]/#id/full
 def FullWay(self, ID):
  return self.Full("way", ID)



 ##################################################
 # Relation                                       #
 ##################################################


 #Read: GET /api/0.6/[node|way|relation]/#id
 def ReadRelation(self, ID):
  return self.Read("relation", ID)


 #History: GET /api/0.6/[node|way|relation]/#id/history
 def HistoryRelation(self, ID):
  return self.History("relation", ID)


 #Version: GET /api/0.6/[node|way|relation]/#id/#version
 def VersionRelation(self, ID, Version):
  return self.Version("relation", ID, Version)


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
  """
  === Details of a user: GET /api/0.6/user/#id.json ===
  You can get the home location and the displayname of the user, by using

  ==== Response ====
  GET /api/0.6/user/#id.json
  {
   'version': "0.6",
   'generator': "OpenStreetMap server",
   'user':
   {
    'id': 12023,
    'display_name': "jbpbis",
    'account_created': "2007-08-16T01:35:56Z",
    'description': "",
    'contributor_terms': {'agreed': False},
    'roles': [],
    'changesets': {'count': 1},
    'traces': {'count': 0},
    'blocks': {'received': {'count': 0, 'active': 0}}
   }
  }
  or an empty file if no user found for given identifier.

  Note that user accounts which made edits may be deleted.
  Such users are listed at
  https://planet.osm.org/users_deleted/users_deleted.txt
  """
  URI = f"{self.API}/user/{ID}.json"
  return self.GetJson(URI, Tag='user')


 #Details of multiple users: GET /api/0.6/users?users=#id1,#id2,...,#idn
 def Users(self, IDs):
  """
  === Details of multiple users: GET /api/0.6/users.json?users=#id1,#id2,...,#idn ===
  You can get the details of a number of users via

  ==== Response ====
  GET /api/0.6/users.json?users=#id1,#id2,...,#idn
  {
   'version': "0.6",
   'generator': "OpenStreetMap server",
   'users':
   [
    {
     'user':
     {
      'id': 12023,
      'display_name': "jbpbis",
      'account_created': "2007-08-16T01:35:56Z",
      'description': "", 
      'contributor_terms': {'agreed': False},
      'roles': [],
      'changesets': {'count': 1},
      'traces': {'count': 0},
      'blocks': {'received': {'count': 0, 'active': 0}}
     }
    },
    {
     'user':
     {
      'id': 210447,
      'display_name': "siebh",
      'account_created': "2009-12-20T10:11:42Z",
      'description': "",
      'contributor_terms': {'agreed': True},
      'roles': [],
      'changesets': {'count': 363},
      'traces': {'count': 1},
      'blocks': {'received': {'count': 0, 'active': 0}}
     }
    }
   ]
  }
  or an empty file if no user found for given identifier.
  """
  URI = f"{self.API}/users.json"
  List = ",".join([str(Item) for Item in IDs])
  Parameters = {'users': List}
  Json = [Item['user'] for Item in self.GetJson(URI, Params=Parameters, Tag='users')]
  Result = list(self.Arrange(IDs, Json))
  return Result


 #Details of the logged-in user: GET /api/0.6/user/details
 def Details(self):
  """
  === Details of the logged-in user: GET /api/0.6/user/details.json ===
  You can get the home location and the displayname of the user, by using

  ==== Response ====
  GET /api/0.6/user/details.json
  this returns an JSON document of the from
  {
   'version': "0.6",
   'generator': 'OpenStreetMap server',
   'user':
   {
    'id': 1234,
    'display_name': "Max Muster",
    'account_created': "2006-07-21T19:28:26Z",
    'description': "The description of your profile",
    'contributor_terms': {'agreed': True, 'pd': True},
    'img': {'href': "https://www.openstreetmap.org/attachments/users/images/000/000/1234/original/someLongURLOrOther.JPG"},
    'roles': [],
    'changesets': {'count': 4182},
    'traces': {'count': 513},
    'blocks': {'received': {'count': 0, 'active': 0}},
    'home': {'lat': 49.4733718952806, 'lon': 8.89285988577866, 'zoom': 3},
    'languages': ['de-DE', 'de', 'en-US', 'en'],
    'messages': {'received': {'count': 1, 'unread': 0}, 'sent': {'count': 0}}
   }
  }

  The messages section has been available since mid-2013.
  It provides a basic counts of received, sent, and unread osm messages.
  """
  URI = f"{self.API}/user/details.json"
  return self.GetJson(URI, Tag='user')


 #Preferences of the logged-in user: GET /api/0.6/preferences
 def Preferences(self):
  """
  === Preferences of the logged-in user: GET /api/0.6/user/preferences.json ===
  The OSM server supports storing arbitrary user preferences.
  This can be used by editors, for example, to offer the same configuration
  wherever the user logs in, instead of a locally-stored configuration.

  You can retrieve the list of current preferences using

  ==== Response ====
  GET /api/0.6/user/preferences.json
  this returns an JSON document of the form
  {
   'version': "0.6",
   'generator': "OpenStreetMap server",
   'preferences': {'somekey': "somevalue", ...}
  }
  """
  URI = f"{self.API}/user/preferences.json"
  return self.GetJson(URI, Tag='preferences')


#PUT /api/0.6/user/preferences
#GET /api/0.6/user/preferences/[your_key]
#PUT /api/0.6/user/preferences/[your_key]
#DELETE /api/0.6/user/preferences/[your_key]



 ##################################################
 # Map Notes API                                  #
 ##################################################


 #Retrieving notes data by bounding box: GET /api/0.6/notes
 def ReadNotes(self, BBox, Limit=None, Closed=None):
  """
  === Retrieving notes data by bounding box: GET /api/0.6/notes.json ===
  Returns the existing notes in the specified bounding box.
  The notes will be ordered by the date of their last change,
  the most recent one will be first.
  The list of notes can be returned in several different forms
  (e.g. as executable JavaScript, XML, RSS, json and GPX) depending
  on the file extension. 

  ==== Note ====
  the XML format returned by the API is different from the,
  equally undocumented, format used for "osm" format files,
  available from https://planet.openstreetmap.org/notes/,
  and as output from JOSM and Vespucci.

  Return type: application/json

  ==== Parameters ====
  ; bbox : Coordinates for the area to retrieve the notes from Floating point
    numbers in degrees, expressing a valid bounding box, not larger than the
    configured size limit, 25 square degrees, not overlapping the dateline.
    Default value is none, parameter required
  ; limit : Specifies the number of entries returned at max
    A value of between 1 and 10000 is valid
    100 is the default
  ; closed : Specifies the number of days a note needs to be closed to no
    longer be returned 
    A value of 0 means only open notes are returned.
    A value of -1 means all notes are returned.
    7 is the default

  You can specify the format you want the results returned as by specifying a
  file extension.
  E.g. https://api.openstreetmap.org/api/0.6/notes.json?bbox=-0.65,51.3,0.35,51.6
  example to get results in json. Currently the format RSS, XML, json and gpx
  are supported.

  The comment properties [uid, user, user_url] will be omitted if the comment
  was anonymous.

  ==== Response ====
  GET /api/0.6/notes.json
  {
   'type': "FeatureCollection",
   'features':
   [
    {
     'type': "Feature",
     'geometry':
     {
      'type': "Point",
      'coordinates': [0.1000000, 51.0000000]
     },
     'properties':
     {
      'id': 16659,
      'url': "https://www.openstreetmap.org/api/0.6/notes/16659.json",
      'comment_url': "https://www.openstreetmap.org/api/0.6/notes/16659/comment.json",
      'close_url': "https://www.openstreetmap.org/api/0.6/notes/16659/close.json",
      'date_created': "2019-06-15 08:26:04 UTC",
      'status': "open",
      'comments':
      [
       {
        'date': "2019-06-15 08:26:04 UTC",
        'uid': 1234,
        'user': "userName",
        'user_url': "https://master.apis.dev.openstreetmap.org/user/userName",
        'action': "opened",
        'text': 'ThisIsANote',
        'html': '<p>ThisIsANote</p>'
       },
       ...
      ]
     }
    }
   ]
  }

  ==== Error codes ====
  ; HTTP status code 400 (Bad Request) : When any of the limits are crossed
  """
  URI = f"{self.API}/notes.json"
  Parameters = {}
  Parameters["bbox"] = self.GetBBox(BBox)
  if Limit:
   Parameters["limit"] = Limit
  if Closed:
   Parameters["closed"] = Closed
  return self.GetJson(URI, Params=Parameters, Tag='features')


 #Read: GET /api/0.6/notes/#id
 def ReadNote(self, ID):
  """
  === Read: GET /api/0.6/notes/#id.json ===
  Returns the existing note with the given ID.
  The output can be in several formats (e.g. XML, RSS, json or GPX)
  depending on the file extension.

  ==== Response ====
  GET /api/0.6/notes/#id.json
  Return type: application/json

  ==== Error codes ====
  ; HTTP status code 404 (Not Found) : When no note with the given id could be
    found
  """
  URI = f"{self.API}/notes/{ID}.json"
  return self.GetJson(URI)


 #Create a new note: Create: POST /api/0.6/notes
 def CreateNote(self, Lat, Lon, Text):
  """
  === Create a new note: POST /api/0.6/notes.json ===

  ==== Response ====
  POST /api/0.6/notes.json
  Return type: application/json
  {
   'lat': 51.00,
   'lon': 0.1&,
   'text': "This is a note\n\nThis is another line"
  }

  A JSON-file with the details of the note will be returned

  ==== Parameters ====
  ; lat : Specifies the latitude of the note floatingpoint number in degrees
    No default, needs to be specified
  ; lon : Specifies the longitude of the note floatingpoint number in degrees
    No default, needs to be specified
  ; text : A text field with arbitrary text containing the note
    No default, needs to be present

  If the request is made as an authenticated user, the note is associated to
  that user account.

  ==== Error codes ====
  ; HTTP status code 400 (Bad Request) : if the text field was not present
  ; HTTP status code 404 (Not found) : This applies, if the request is not a
    HTTP POST request
  """
  URI = f"{self.API}/notes.json"
  return self.PostJson(URI, Data={'lat': Lat, 'lon': Lon, 'text': Text})


#Create a new comment: Create: POST /api/0.6/notes/#id/comment
#Close: POST /api/0.6/notes/#id/close
#Reopen: POST /api/0.6/notes/#id/reopen


 #Search for notes: GET /api/0.6/notes/search
 def SearchNotes(self, Query, Limit=None, Closed=None, DisplayName=None, User=None, From=None, To=None, Sort=None, Order=None):
  """
  === Search for notes: GET /api/0.6/notes/search.json ===
  Returns the existing notes matching either the initial note text or any
  of the comments. The notes will be ordered by the date of their last change,
  the most recent one will be first.
  If no query was specified, the latest notes are returned.
  The list of notes can be returned in several different forms
  (e.g. XML, RSS, json or GPX) depending on file extension given.

  GET /api/0.6/notes/search.json?q=SearchTerm
  (URL: https://api.openstreetmap.org/api/0.6/notes/search.json?q=Spam example)
  Return type: application/json

  ==== Parameters ====
  ; q : Specifies the search query
    Allowed values : String. 
    none, parameter required
  ; limit : Specifies the number of entries returned at max
    A value of between 1 and 10000 is valid
    100 is the default
  ; closed : Specifies the number of days a note needs to be closed to no
    longer be returned 
    Allowed values : A value of 0 means only open notes are returned.
    A value of -1 means all notes are returned.
    7 is the default
  ; display_name : Specifies the person involved in actions of the returned
    notes, query by the display name. Does not work together with the 'user'
    parameter (Returned are all where this user has taken some action - opened
    note, commented on, reactivated, or closed)
    Allowed values : A valid user name
    none, optional  parameter
  ; user : Specifies the creator of the returned notes by the id of the user.
    Does not work together with the display_name parameter
    Allowed values : A valid user id
    none, optional parameter
  ; from : Specifies the beginning of a date range to search in for a note
    Allowed values : A valid ISO 8601 date
    none, optional parameter
  ; to : Specifies the end of a date range to search in for a note
    Allowed values : A valid ISO 8601 date.
    the date of today is the default, optional parameter
  ; sort : Specifies the value which should be used to sort the notes.
    It is either possible to sort them by their creation date or the date of
    the last update.
    Allowed values : "created_at" or "updated_at"
    Default value : "updated_at"
  ; order : Specifies the order of the returned notes. It is possible to order
    them in ascending or descending order.
    Allowed values : "oldest" or "newest"
    Default value : "newest"

  ==== Error codes ====
  ; HTTP status code 400 (Bad Request) : When any of the limits are crossed
  """
  URI = f"{self.API}/notes/search.json"
  Parameters = {}
  Parameters['q'] = Query
  if Limit:
   Parameters['limit'] = Limit
  if Closed:
   Parameters['closed'] = Closed
  if DisplayName:
   Parameters['display_name'] = DisplayName
  if User:
   Parameters['user'] = User
  if From:
   Parameters['from'] = From
  if To:
   Parameters['to'] = To
  if Sort:
   Parameters['sort'] = Sort #created_at or updated_at
  if Order:
   Parameters['order'] = Order #oldest or newest
  return self.GetJson(URI, Params=Parameters)


 #RSS Feed: GET /api/0.6/notes/feed
 def RSS(self, BBox):
  """
  === RSS Feed: GET /api/0.6/notes/feed ===
  Gets an RSS feed for notes within an area.

  ==== Response ====
  GET /api/0.6/notes/feed?bbox=left,bottom,right,top
  Return type: application/xml
  """
  Parameters = {}
  Parameters['bbox'] = self.GetBBox(BBox)
  URI = f"{self.API}/notes/feed"
  return self.GetXML(URI, Params=Parameters)



##################################################
# Other                                          #
##################################################


class CacheIterator:

 # захаваць прамежуткавыя значэнні
 def __init__(self, Count, Array, Type=["node", "way", "relation"], Role=[]):
  self.OSM = OsmApi()
  self.Count = Count
  self.Array = Array
  self.IncludeType = Type
  self.IncludeRole = Role # [] = All
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
   if Item['type'] == Type and (not self.IncludeRole or Item['role'] in self.IncludeRole):
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
