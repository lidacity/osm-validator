import os


from SQLite3 import OsmPbf


class Validator:
 def __init__(self, Download=True):
  self.Path = os.path.dirname(os.path.abspath(__file__))
  self.OSM = OsmPbf(Download=Download)
  self.CountParse = 0

 
 def __del__(self):
  print("!")
  self.OSM.Close()


 #


 def RelationsForWay(self, ID):
  return self.OSM.RelationsForWay(ID)


 def ReadNodes(self, List):
  return self.OSM.ReadNodes(List)


 def GetNodeKey(self, Key, Values=[]):
  return self.OSM.GetNodeKey(Key, Values=Values)


 def GetWayKey(self, Key, Values=[]):
  return self.OSM.GetWayKey(Key, Values=Values)


 def GetRelationKey(self, Key, Values=[]):
  return self.OSM.GetRelationKey(Key, Values=Values)


 def GetRelationMembers(self, ID):
  return self.OSM.GetRelationMembers(ID)


 def ReadNode(self, ID):
  return self.OSM.ReadNode(ID)


 def ReadWay(self, ID):
  return self.OSM.ReadWay(ID)


 def ReadRelation(self, ID):
  return self.OSM.ReadRelation(ID)


 def GetDateTime(self):
  return self.OSM.GetDateTime()
 


 #


 def Island(self, Ways):
  Limits = self.GetLimits(Ways)
  Result = []
  while len(Limits) > 1:
   for Item in Limits[1:]:
    if Limits[0][0] == Item[0]:
     Limits[0][0] = Item[1]
     Limits.remove(Item)
     break
    if Limits[0][0] == Item[1]:
     Limits[0][0] = Item[0]
     Limits.remove(Item)
     break
    if Limits[0][1] == Item[1]:
     Limits[0][1] = Item[0]
     Limits.remove(Item)
     break
    if Limits[0][1] == Item[0]:
     Limits[0][1] = Item[1]
     Limits.remove(Item)
     break
   else:
    Result.append(Limits[0])
    Limits.pop(0)
  Result.append(Limits[0])
  Limits.pop(0)
  #
  if len(Result) == 1:
   if len(set(Result[0])) == 1:
    Result = []
  return Result


 def IslandLine(self, Ways):
  Limits = self.GetLimits(Ways)
  Result = []
  Index = -1
  while len(Limits) > 1:
   for Item in Limits[1:]:
    #
    if Index == -1:
     if Limits[0][0] in Item:
      Index = 0
     elif Limits[0][1] in Item:
      Index = 1
    #
    if Limits[0][Index] == Item[0]:
     Limits[0][Index] = Item[1]
     Limits.remove(Item)
     break
    elif Limits[0][Index] == Item[1]:
     Limits[0][Index] = Item[0]
     Limits.remove(Item)
     break
    #
    Result.append(Limits[0])
    Limits.pop(0)
    Index = -1
   else:
    Result.append(Limits[0])
    Limits.pop(0)
  #
  if Limits:
   Result.append(Limits[0])
   Limits.pop(0)
  #
  if len(Result) == 1:
   if len(set(Result[0])) == 1:
    Result = []
  return Result


 def GetAllNodes(self, Relation):
  Result = []
  List = [ Member['ref'] for Member in Relation['members'] if Member['type'] == "way" ]
  Result = [ ID for Way in self.OSM.ReadWays(List) for ID in Way['nodes'] ]
  return Result


 def GetWays(self, Relation, Role=[]):
  Result = []
  List = [ Member['ref'] for Member in Relation['members'] if Member['type'] == "way" and (not Role or Member['role'] in Role) ]
  Result = self.OSM.ReadWays(List)
  return Result


 def GetRelations(self, Relation, Role=[]):
  Result = []
  List = [ Member['ref'] for Member in Relation['members'] if Member['type'] == "relation" and (not Role or Member['role'] in Role) ]
  Result = self.OSM.ReadRelations(List)
  return Result


 def GetLimits(self, Ways):
  return [ [Way['nodes'][0], Way['nodes'][-1]] for Way in Ways ]


 def GetNodes(self, Ways):
  return [ [Node for Node in Way['nodes']] for Way in Ways ]


 def GetListNodes(self, Ways):
  return [ Node for Way in Ways for Node in Way['nodes'] ]


 def GetCoord(self, Ways):
  Nodes = self.IslandLine(Ways)
  List = [ID for Row in Nodes for ID in Row]
  Result = { Node['id']: (Node['lat'], Node['lon']) for Node in self.OSM.ReadNodes(List) }
  return [ [ Result[ID] for ID in Row ] for Row in Nodes ]


 def GetNameLang(self, TagName):
  S = TagName + ':'
  Result = S.split(":")
  return Result[:2]


 def SplitName(self, S, TagName='name'):
  Name, Lang = self.GetNameLang(TagName)
  Result = {}
  #
  while len(S) > 0:
   Count = 253 if Result else 254
   T = S[:Count]
   if Result:
    T = f"…{T}"
   if len(T) == 254:
    T = f"{T}…"
   S = S[Count:]
   #
   if Result:
    Index = len(Result) + 1
    if Lang:
     Key = f"{Name}#{Index}:{Lang}"
    else:
     Key = f"{Name}#{Index}"
   else:
    Key = f"{Name}"
   # 
   Result[Key] = T
  return Result


 def JoinName(self, Tag, TagName='name', Default=""):
  Name, Lang = self.GetNameLang(TagName)
  Result = Tag.get(TagName, Default)
  i = 2
  while f"{Name}#{i}:{Lang}" in Tag:
   Result += Tag[f"{Name}#{i}:{Lang}"]
   i += 1
  return Result.replace("……", "")

