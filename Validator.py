import os

import re
re._MAXCACHE = 4096

from collections import Counter
from haversine import haversine

from SQLite3 import OsmPbf


class Validator:
 def __init__(self, Download=True):
  self.Path = os.path.dirname(os.path.abspath(__file__))
  self.OSM = OsmPbf(Download=Download)
  self.CountParse = 0


 def __del__(self):
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


 def GetRelationsForRelation(self, ID):
  return self.OSM.RelationsForRelation(ID)


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


 def GetNodes(self, Relation, Role=[]):
  Result = []
  List = [ Member['ref'] for Member in Relation['members'] if Member['type'] == "node" and (not Role or Member['role'] in Role) ]
  Result = self.OSM.ReadNodes(List)
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


 def GetNodesFromWays(self, Ways):
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
#  return Result[:2]
  return [Result[0], (":" if Result[1] else "") + Result[1]]


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
    Key = f"{Name}#{Index}{Lang}"
   else:
    Key = f"{Name}"
   #
   Result[Key] = T
  return Result


 def JoinName(self, Tag, TagName='name', Default=""):
  Name, Lang = self.GetNameLang(TagName)
  Result = Tag.get(TagName, Default)
  i = 2
  while f"{Name}#{i}{Lang}" in Tag:
   Result += Tag[f"{Name}#{i}{Lang}"]
   i += 1
  if f"alt_{Name}{Lang}" in Tag:
   Result += Tag[f"alt_{Name}{Lang}"]
  return Result.replace("……", "")


#


 # example: Class = { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:national', 'name': None, 'name:be': None, 'name:ru': None, }
 def CheckTag(self, Tag, Class, Note=""):
  Result = []
  for TagName, Value in Class.items():
   if TagName not in Tag:
    Result.append(f"{Note}не знойдзены '{TagName}'")
   elif Value is not None:
    if self.JoinName(Tag, TagName) != Value:
     Result.append(f"{Note}'{TagName}' не роўны \"{Value}\"")
  return Result



 def CheckBe(self, Tag):
  Result = []
  Name = self.JoinName(Tag, 'name')
  Be = self.JoinName(Tag, 'name:be')
  if Name != Be:
   Result.append(f"'name:be' не роўны 'name'")
  return Result



 def CheckOfficialName(self, Tag):
  Result = []
  for TagName in ['official_name', 'official_name:be', 'official_name:ru', 'description', 'description:be', 'description:ru', 'source:ref:date', 'int_name', ]:
   if TagName in Tag:
    Result.append(f"непатрэбны '{TagName}'")
  if 'fixme' in Tag:
   Result.append(f"'fixme' у relation")
  return Result



 Replace = { 'SOS': "СОС", 'XXI': "21", 'III': "3", 'II': "2", 'I': "1", }


 def CheckWrong(self, Tag, Wrong):
  Result = []
  for TagName in ['name:be', 'name:ru']:
   if TagName in Tag:
    S = self.JoinName(Tag, TagName)
    for Key, Value in self.Replace.items():
     S = S.replace(Key, Value)
    for _, Value in Wrong.items():
     R = Value['re'](S)
     if R:
      Result.append(f"у '{TagName}' {Value['Desc']} \"{R[0]}\"")
      #break
  return Result



 Pair = {
  'Split': re.compile("|".join(map(re.escape, "{}()[]\"«»„“")) + "|" + "|".join([r"\B'", r"'\B"])).findall,
  'Replace': re.compile("|".join([re.escape(s) for s in ["{}", "()", "[]", "''", "\"\"", "«»", "„“"]])).sub,
 }


 def CheckPair(self, Tag):
  Result = []
  for TagName in ['name:be', 'name:ru']:
   if TagName in Tag:
    Split = self.Pair['Split']
    Check = "".join(Split(self.JoinName(Tag, TagName)))
    if Check:
     S = ""
     while Check != S:
      Pair = self.Pair['Replace']
      S, Check = Check, Pair("", Check)
    if Check != "":
     Result.append(f"у '{TagName}' непарныя дужкі ці двукоссі \"{Check}\"")
     #break
  return Result



 def CheckLength(self, Tag):
  Result = []
  Be = self.JoinName(Tag, 'name:be')
  Ru = self.JoinName(Tag, 'name:ru')
  if abs(len(Be) - len(Ru)) > 18:
   Result.append(f"розніца паміж даўжынёй 'name:be' і 'name:ru'")
  return Result



 #https://vl2d.livejournal.com/21053.html
 #https://yadro-servis.ru/blog/nevosmosnoe-sochetanie-bukv/
 Impossible = {
  'name:ru': re.compile("|".join(["  ", "ёя", "ёь", "ёэ", "ъж", "эё", "ъд", "цё", "уь", "щч", "чй", "шй", "шз", "ыф", "жщ", "жш", "ыъ", "ыэ", "ыю", "ыь", "жй", "ыы", "жъ", "жы", "ъш", "пй", "ъщ", "зщ", "ъч", "ъц", "ъу", "ъф", "ъх", "ъъ", "ъы", "ыо", "жя", "зй", "ъь", "ъэ", "ыа", "нй", "еь", "цй", "ьй", "ьл", "ьр", "пъ", "еы", "еъ", "ьа", "шъ", "ёы", "ёъ", "ът", "щс", "оь", "къ", "оы", "щх", "щщ", "щъ", "щц", "кй", "оъ", "цщ", "лъ", "мй", "шщ", "ць", "цъ", "щй", "йь", "ъг", "иъ", "ъб", "ъв", "ъи", "ъй", "ъп", "ър", "ъс", "ъо", "ън", "ък", "ъл", "ъм", "иы", "иь", "йу", "щэ", "йы", "йъ", "щы", "щю", "щя", "ъа", "мъ", "йй", "йж", "ьу", "гй", "эъ", "уъ", "аь", "чъ", "хй", "тй", "чщ", "ръ", "юъ", "фъ", "уы", "аъ", "юь", "аы", "юы", "эь", "эы", "бй", "яь", "ьы", "ьь", "ьъ", "яъ", "яы", "хщ", "дй", "фй", ])).search,
  'name:be': re.compile("|".join(["  ", "и", "щ", "ъ", "ї", "жі", "же", "жё", "жя", "жю", "рі", "ре", "рё", "ря", "рю", "чі", "че", "чё", "чя", "чю", "ші", "ше", "шё", "шя", "шю", "ді", "де", "дё", "дя", "дю", "ті", "те", "тё", "тя", "тю", "еу", "ыу", "оу", "яу", "юу", "ёу", "уу", "еь", "ыь", "аь", "оь", "эь", "яь", "іь", "юь", "ёь", "уь", "ўь", "йь", "йў", "цў", "кў", "нў", "гў", "шў", "ўў", "зў", "хў", "фў", "вў", "пў", "рў", "лў", "дў", "жў", "чў", "сў", "мў", "тў", "ьў", "бў", "йй", "цй", "кй", "нй", "гй", "шй", "ўй", "зй", "хй", "фй", "вй", "пй", "рй", "лй", "дй", "жй", "чй", "сй", "мй", "тй", "ьй", "бй", "жш", "ыэ", "ыы", "ыо", "ьр", "ьа", "ёы", "оы", "йу", "йы", "йж", "ьу", "гй", "уы", "юь", "аы", "юы", "эы", "ьы", "ьь", "яы", ])).search,
  #"ау", "іу", "эу", 
 }


 def CheckImpossible(self, Tag):
  Result = []
  for TagName in ['name:ru', 'name:be']:
   if TagName in Tag:
    Line = self.JoinName(Tag, TagName).lower()
    Imp = self.Impossible[TagName](Line)
    if Imp:
     Result.append(f"у '{TagName}' немагчымае спалучэнне \"{Imp[0]}\"")
     #break
  return Result



 def CheckTypes(self, Relation, Type):
  Result = []
  for Member in Relation['members']:
   if Member['type'] != Type:
    Result.append(f"у relation прысутнічае ня толькі {Type}")
    #break
  return Result



 def CheckFixme(self, Ways):
  Result = []
  for Way in Ways:
   if "fixme" in Way['tags']:
    Result.append(f"'fixme' у way")
    #break
  return Result



 def CheckHighway(self, Ways, Highways):
  Result = []
  for Key in Highways:
   for Way in Ways:
    Tag = Way['tags']
    if Key in Tag:
     if Tag[Key] not in Highways[Key]:
      Result.append(f"памылковы '{Key}'=\"{Tag[Key]}\" на way")
      #break
  #
  for Way in Ways:
   Tag = Way['tags']
   Res = [x for x in Highways if x in Tag]
   if not Res:
    Result.append(f"пусты '{Key}' на way")
    #break
  return Result



 def CheckDoubleWay(self, Ways):
  Result = []
  c = Counter([Way['id'] for Way in Ways])
  if max(c.values()) > 1:
   Result.append(f"падвоеныя way")
  return Result



 WayNameBe = ["праспект", "вуліца", "завулак", "плошча", "бульвар", "шаша", "тракт", "алея", "тупік", "сквер", "парк", "праезд", "уезд", "раз'езд", "спуск", "набярэжная", "кальцо", "мікрараён", "квартал", "тэрыторыя", "МКАД", "МКАД-2", "мост", "пуцеправод", "дарога"]
 WayNameRu = ["проспект", "улица", "переулок", "площадь", "бульвар", "шоссе", "тракт", "аллея", "тупик", "сквер", "парк", "проезд", "въезд", "разъезд", "спуск", "набережная", "кольцо", "микрорайон", "квартал", "территория", "МКАД", "МКАД-2", "мост", "путепровод", "дорога"]
 WayName = {
  'name': set(WayNameBe),
  'name:be': set(WayNameBe),
  'name:ru': set(WayNameRu),
 }


 def CheckName(self, Ways):
  Result = []
  for Way in Ways:
   Tag = Way['tags']
   for TagName in ['name', 'name:be', 'name:ru']:
    Name = self.JoinName(Tag, TagName)
    if Name and not set(Name.split()) & self.WayName[TagName]:
     Result.append(f"way змяшчае недапушчальны '{TagName}'")
     return Result
  return Result



 def CheckCross(self, Ways):
  Result = []
  Limits = self.GetLimits(Ways)
  Nodes = [Node for Row in Limits for Node in Row]
  c = Counter(Nodes)
  if max(c.values()) > 2:
   Result.append(f"замкнутая ў пятлю ці перакрыжаваная")
  else:
   Nodes = self.GetNodesFromWays(Ways)
   Nodes1 = [Node for Row in Nodes for Node in Row]
   Nodes2 = [Node for Row in Nodes for Node in Row[1:-1]]
   c = Counter(Nodes1 + Nodes2)
   if max(c.values()) > 2:
    Result.append(f"замкнутая ў пятлю ці перакрыжаваная")
  return Result



 def CheckIsland(self, Ways, IsOneLine=False):
  Result = []
  Island = self.Island(Ways)
  IslandLine = self.IslandLine(Ways)
  if IsOneLine:
   if len(Island) != 1 or len(IslandLine) != 1:
    Result.append(f"way не паслядоўныя")
  else:
   if Island != IslandLine:
    Result.append(f"way не паслядоўныя")
  return Result



 def CheckHaversine(self, Ways, Length=3):
  Result = []
  Coords = self.GetCoord(Ways)
  #
  Lengths = []
  for Coord1 in Coords:
   SubLengths = []
   for Coord2 in Coords:
    if Coord1 != Coord2:
     SubLengths += [ haversine(x, y) for x in Coord1 for y in Coord2 ]
   if SubLengths:
    Lengths.append(min(SubLengths))
  #
  if Lengths:
   if max(Lengths) > Length:
    Result.append(f"way занадта разарваны")
  return Result



 def CheckRoles(self, Members, Roles):
  Result = []
  for Member in Members:
   Type = Member['type']
   if Member['role'] not in Roles[Type]:
    Result.append(f"relation змяшчае недапушчальную role: '{Type}'=\"{Member['role']}\"")
  return Result


