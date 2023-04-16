#https://josm.openstreetmap.de/wiki/Ru%3AHelp/RemoteControlCommands

import os
import sys
import random
import datetime
from collections import Counter

import re
re._MAXCACHE = 4096

from loguru import logger
from haversine import haversine

from SQLite3 import OsmPbf


Path = os.path.dirname(os.path.abspath(__file__))
OSM = OsmPbf()


#

Classes = {
 'М': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:national', 'name': None, 'name:be': None, 'name:ru': None, },
 'Р': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:national', 'name': None, 'name:be': None, 'name:ru': None, },
 'Н': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:regional', 'name': None, 'name:be': None, 'name:ru': None, },
}


def CheckRef(Key):
 Result = []
 if Key[:6] == "error-":
  Result.append(f"несапраўдны 'official_ref'")
 return Result


def CheckRelation(Type):
 Result = []
 if Type != "relation":
  Result.append(f"не relation")
 return Result


def CheckTag(Tag, Class):
 Result = []
 for TagName, Value in Classes[Class].items():
  if TagName not in Tag:
   Result.append(f"не знойдзены '{TagName}'")
  elif Value is not None:
   if Tag[TagName] != Value:
    Result.append(f"'{TagName}' не роўны \"{Value}\"")
 return Result


def CheckClass(Tag, Class):
 Result = []
 Ref, OfficialRef = Tag.get('ref', ""), Tag.get('official_ref', "")
 if Ref and OfficialRef:
  if Ref[0] != Class:
   Result.append(f"'ref' не пачынаецца з \"{Class}\"")
  if OfficialRef[:2] != f"{Class}-":
   Result.append(f"'official_ref' не пачынаецца з \"{Class}-\"")
  if not(Ref[1:] == OfficialRef[2:2+len(Ref[1:])] or Ref == OfficialRef.replace("-", "").replace(" ", "")):
   Result.append(f"'official_ref' не адпавядае 'ref'")
 return Result


def CheckBe(Tag):
 Result = []
 Name = Tag.get('name', None)
 Be = Tag.get('name:be', None)
 if Name != Be:
  Result.append(f"'name:be' не роўны 'name'")
 return Result


def CheckRu(Tag, Name):
 Result = []
 Ru = Tag.get('name:ru', "")
 if Name[:254] != Ru[:254]:
  Result.append(f"'name:ru' не супадае з Законам")
 return Result


def CheckOfficialName(Tag):
 Result = []
 for TagName in ['official_name', 'official_name:be', 'official_name:ru', 'description', 'description:be', 'description:ru', 'source:ref:date', ]:
  if TagName in Tag:
   Result.append(f"непатрэбны '{TagName}'")
 if 'fixme' in Tag:
  Result.append(f"'fixme' у relation")
 return Result


Wrong = {
 'Latin': {'re': re.compile("[a-zA-Z]").search, 'Desc': "лацінскія літары"},
 'Number': {'re': re.compile("[a-zA-Zа-яА-ЯёЁ][0-9]|[0-9][a-zA-Zа-яА-ЯёЁ]").search, 'Desc': "няправільныя лічбы"},
 'Hyphen': {'re': re.compile("[^ ]–|–[^ …]|[ ]-|-[ ]").search, 'Desc': "неправільны злучок"},
 'Bracket': {'re': re.compile("[^ \"(]\(|\)[^ …\")]").search, 'Desc': "неправільныя дужкі"},
 'Special': {'re': re.compile("|".join(map(re.escape, ".:;!_*+#¤%&[]{}$@^\\"))).search, 'Desc': "спецыяльныя знакі"},
 'Abbreviations': {'re': re.compile("|".join([re.escape(s) for s in ["’", "—", "а/д", "г.п.", "г.", "аг.", "п.", "д.", "х.", "ж/д", "ст.", "с/т", "с/с", "хоз.", "Ж/д", "А/д", "С/т", "Ст.", "обл.", "Гр.", "р-на", "вул.", "ул.", ]])).search, 'Desc': "недапушчальны скарот"},
}


Replace = { 'SOS': "СОС", 'III': "3", 'II': "2", 'I': "1", }


def CheckWrong(Tag):
 Result = []
 for TagName in ['name:be', 'name:ru']:
  if TagName in Tag:
   S = Tag[TagName]
   for Key, Value in Replace.items():
    S = S.replace(Key, Value)
   for _, Value in Wrong.items():
    R = Value['re'](S)
    if R:
     Result.append(f"у '{TagName}' {Value['Desc']} \"{R[0]}\"")
     break
 return Result


Pair = {
 'Split': re.compile("|".join(map(re.escape, "{}()[]\"«»")) + "|" + "|".join(["\B'", "'\B"])).findall,
 'Replace': re.compile("|".join([re.escape(s) for s in ["{}", "()", "[]", "''", "\"\"", "«»"]])).sub,
}


def CheckPair(Tag):
 Result = []
 for TagName in ['name:be', 'name:ru']:
  if TagName in Tag:
   Check = "".join(Pair['Split'](Tag[TagName]))
   if Check:
    S = ""
    while Check != S:
     S, Check = Check, Pair['Replace']("", Check)
   if Check != "":
    Result.append(f"у '{TagName}' непарныя дужкі ці двукоссі \"{Check}\"")
    break
 return Result


def CheckLength(Tag):
 Result = []
 Be = len(Tag.get('name:be', ""))
 Ru = len(Tag.get('name:ru', ""))
 if abs(Be - Ru) > 18:
  Result.append(f"розніца паміж даўжынёй 'name:be' і 'name:ru'")
 return Result


#https://vl2d.livejournal.com/21053.html
#https://yadro-servis.ru/blog/nevosmosnoe-sochetanie-bukv/ 
Impossible = {
 'name:ru': re.compile("|".join(["ёя", "ёь", "ёэ", "ъж", "эё", "ъд", "цё", "уь", "щч", "чй", "шй", "шз", "ыф", "жщ", "жш", "ыъ", "ыэ", "ыю", "ыь", "жй", "ыы", "жъ", "жы", "ъш", "пй", "ъщ", "зщ", "ъч", "ъц", "ъу", "ъф", "ъх", "ъъ", "ъы", "ыо", "жя", "зй", "ъь", "ъэ", "ыа", "нй", "еь", "цй", "ьй", "ьл", "ьр", "пъ", "еы", "еъ", "ьа", "шъ", "ёы", "ёъ", "ът", "щс", "оь", "къ", "оы", "щх", "щщ", "щъ", "щц", "кй", "оъ", "цщ", "лъ", "мй", "шщ", "ць", "цъ", "щй", "йь", "ъг", "иъ", "ъб", "ъв", "ъи", "ъй", "ъп", "ър", "ъс", "ъо", "ън", "ък", "ъл", "ъм", "иы", "иь", "йу", "щэ", "йы", "йъ", "щы", "щю", "щя", "ъа", "мъ", "йй", "йж", "ьу", "гй", "эъ", "уъ", "аь", "чъ", "хй", "тй", "чщ", "ръ", "юъ", "фъ", "уы", "аъ", "юь", "аы", "юы", "эь", "эы", "бй", "яь", "ьы", "ьь", "ьъ", "яъ", "яы", "хщ", "дй", "фй", ])).search,
 'name:be': re.compile("|".join(["и", "щ", "ъ", "ї", "жі", "же", "жё", "жя", "жю", "рі", "ре", "рё", "ря", "рю", "чі", "че", "чё", "чя", "чю", "ші", "ше", "шё", "шя", "шю", "ді", "де", "дё", "дя", "дю", "ті", "те", "тё", "тя", "тю", "еу", "ыу", "оу", "яу", "юу", "ёу", "уу", "еь", "ыь", "аь", "оь", "эь", "яь", "іь", "юь", "ёь", "уь", "ўь", "йь", "йў", "цў", "кў", "нў", "гў", "шў", "ўў", "зў", "хў", "фў", "вў", "пў", "рў", "лў", "дў", "жў", "чў", "сў", "мў", "тў", "ьў", "бў", "йй", "цй", "кй", "нй", "гй", "шй", "ўй", "зй", "хй", "фй", "вй", "пй", "рй", "лй", "дй", "жй", "чй", "сй", "мй", "тй", "ьй", "бй", "жш", "ыэ", "ыы", "ыо", "ьр", "ьа", "ёы", "оы", "йу", "йы", "йж", "ьу", "гй", "уы", "юь", "аы", "юы", "эы", "ьы", "ьь", "яы", ])).search,
 #"ау", "іу", "эу", 
}


def CheckImpossible(Tag):
 Result = []
 for TagName in ['name:ru', 'name:be']:
  if TagName in Tag:
   Line = Tag[TagName].lower()
   Imp = Impossible[TagName](Line)
   if Imp:
    Result.append(f"у '{TagName}' немагчымае спалучэнне \"{Imp[0]}\"")
    break
 return Result


Refs = { 'ok': re.compile("[МР]-[0-9]+/[ЕП] [0-9]+|[МРН]-[0-9]+"), 'bad': re.compile("[МРН][0-9]+"), }


def GetList(Name, Type):
 return re.findall(Refs[Type], Name)


def GetIndex(Name, Ref):
 return [Index.start() for Index in re.finditer(Ref, Name)]


def ExcludeRef(Name, Index):
 return Name[Index-1:].strip()[:1] in ["(", ")", ""]



def CheckEqRef(Tag):
 Result = []
 Refs = { 'name:be': [], 'name:ru': [] }
 for TagName in ['name:be', 'name:ru']:
  if TagName in Tag:
   for Ref in GetList(Tag[TagName], 'ok'):
    Refs[TagName].append(Ref)
 if Counter(Refs['name:be']) != Counter(Refs['name:ru']):
  Result.append(f"у 'name:be' і 'name:ru' не аднолькавыя 'ref'")
 return Result


def CheckBadRefInRelation(Relation):
 Result = []
 Tag = Relation['tags']
 for TagName in ['name:be', 'name:ru']:
  if TagName in Tag:
   if GetList(Tag[TagName], 'bad'):
    Result.append(f"у '{TagName}' не вызначаны 'ref'")
 return Result


def CheckDoubleRef(Relation):
 Result = []
 if Relation['double']:
  Result.append(f"існуе дублікат 'ref'")
 return Result


def CheckWays(Relation):
 Result = []
 for Member in Relation['members']:
  if Member['type'] != "way":
   Result.append(f"у relation прысутнічае ня толькі way")
   break
 return Result


def CheckRefInRelation(Relation, Relations):
 Result = []
 Tag = Relation['tags']
 for TagName in ['name:be', 'name:ru']:
  if TagName in Tag:
   for Ref in GetList(Tag[TagName], 'ok'):
    if Ref in Relations:
     for Index in GetIndex(Tag[TagName], Ref):
      Tag2 = Relations[Ref]['tags'] # з агульнага спісу аўтадарог
      if TagName in Tag2:
       I = Index + len(Ref) + 1
       S2 = Tag2[TagName] # з агульнага спісу аўтадарог
       S = Tag[TagName][I:I+len(S2)]
       Len = len(S2) - (1 if S2[-1:] == "…" else 0)
       if Len == 0:
        Len = len(S2)
       if S2[:Len] != S[:Len] and not ExcludeRef(Tag[TagName], I):
        Result.append(f"\"{Ref}\" не адпавядае найменню ў '{TagName}'")
        break
    else:
     Result.append(f"у '{TagName}' не вызначаны \"{Ref}\"")
 return Result


def CheckTouch(Relation, Relations, Highways):
 Result = []
 Tag = Relation['tags']
 Name = Tag['name:ru']
 for Ref in GetList(Name, 'ok'):
  Highway = Highways[Ref]
  if Ref in Highway['Desc']:
   Name = Name.replace(f"{Ref} {Highway['Desc']}", f"{Ref}")
 Roads = GetList(Name, 'ok')
 if Roads:
  Nodes = GetAllNodes(Relation)
  for Ref in Roads:
   if Ref in Relations:
    TouchNodes = GetAllNodes(Relations[Ref])
    Touch = list(set(Nodes) & set(TouchNodes))
    if not Touch:
     Result.append(f"не дакранаецца да \"{Ref}\"")
     break
   else:
    Result.append(f"не знойдзены \"{Ref}\"")
    break
 return Result


#Words = re.compile(r"\b\w+\b")
Words = re.compile(r"\b[А-ЯЁЎІ]\w+ [А-ЯЁЎІ]\w+\b|\b\[А-ЯЁЎІ]w+[ -]\d+\b|\b[А-ЯЁЎІ]\w+\b")


def CheckPlace(Tag, Place):
 Result = []
 Be, Ru = Tag.get('name:be', ""), Tag.get('name:ru', "")
 Bes, Rus = Words.findall(Be), Words.findall(Ru)
 for Ru in Rus:
  if Ru in Place and not Result:
   for Name in Place[Ru]:
    if Name in Bes:
     break
   else:
    Result.append(f"не супадаюць населеныя пункты у name:be і name:ru")
 return Result


def CheckLaw(Tag, Highways):
 Result = []
 if 'official_ref' in Tag:
  Ref = Tag['official_ref']
  if Ref in Highways:
   Highway = Highways[Ref]
   if 'source:ref' in Tag:
    if Tag['source:ref'] != Highway['Law']:
     Result.append(f"неправільная крыніца \"{Highway['Law']}\" наймення")
   else:
    Result.append(f"адсутнічае крыніца \"{Highway['Law']}\" наймення")
 return Result


def CheckTagsInWay(Tag, Ways):
 Result = []
 Tags = {
  'ref': 'ref',
  'official_name': 'name',
  'official_name:be': 'name:be',
  'official_name:ru': 'name:ru',
  }
 for TagWay, TagRelation in Tags.items():
  for Way in Ways:
   if Tag.get(TagRelation, None) != Way['tags'].get(TagWay, None) is not None:
    Result.append(f"не супадае '{TagRelation}' у relation і '{TagWay}' яе ways")
    break
 return Result


def CheckFixme(Ways):
 Result = []
 for Way in Ways:
  if "fixme" in Way['tags']:
   Result.append(f"'fixme' у way")
   break
 return Result


def CheckHighway(Ways):
 Result = []
 Highways = ["motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential", "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link", ]
 for Way in Ways:
  Tag = Way['tags']
  if 'highway' in Tag:
   if Tag['highway'] not in Highways:
    Result.append(f"памылковы 'highway'=\"{Tag['highway']}\" на way")
    break
 for Way in Ways:
  Tag = Way['tags']
  if not('highway' in Tag or 'ferry' in Tag):
   Result.append(f"пусты 'highway' на way")
   break
 return Result


def CheckDoubleWay(Ways):
 Result = []
 c = Counter([Way['id'] for Way in Ways])
 if max(c.values()) > 1:
  Result.append(f"падвоеныя way")
 return Result


def CheckDoubleRelation(Ways, Relations):
 Result = []
 for Way in Ways:
  Count = 0
  for Relation in OSM.RelationsForWay(Way['id']):
   if Relation['tags'].get('official_ref', "") in Relations:
    Count += 1
  if Count > 1:
   Result.append(f"way знаходзяцца ў некалькіх relation")
   break
  if Count == 0:
   Result.append(f"way не знаходзіцца нават у адным relation")
 return Result


def CheckCross(Ways):
 Result = []
 Limits = GetLimits(Ways)
 Nodes = [Node for Row in Limits for Node in Row]
 c = Counter(Nodes)
 if max(c.values()) > 2:
  Result.append(f"замкнутая ў пятлю ці перакрыжаваная")
 else:
  Nodes = GetNodes(Ways)
  Nodes1 = [Node for Row in Nodes for Node in Row]
  Nodes2 = [Node for Row in Nodes for Node in Row[1:-1]]
  c = Counter(Nodes1 + Nodes2)
  if max(c.values()) > 2:
   Result.append(f"замкнутая ў пятлю ці перакрыжаваная")
 return Result


def CheckIsland(Ways):
 Result = []
 if Island(Ways) != IslandLine(Ways):
  Result.append(f"way не паслядоўныя")
 return Result


def CheckHaversine(Ways):
 Result = []
 Coords = GetCoord(Ways)
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
  if max(Lengths) > 1.0:
   Result.append(f"way занадта разарваны")
 return Result


#


def Island(Ways):
 Limits = GetLimits(Ways)
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


def IslandLine(Ways):
 Limits = GetLimits(Ways)
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


def GetAllNodes(Relation):
 Result = []
 List = [ Member['ref'] for Member in Relation['members'] if Member['type'] == "way" ]
 Result = [ ID for Way in OSM.ReadWays(List) for ID in Way['nodes'] ]
 return Result


def GetWays(Relation, Role=[]):
 Result = []
 List = [ Member['ref'] for Member in Relation['members'] if Member['type'] == "way" and (not Role or Member['role'] in Role) ]
 Result = OSM.ReadWays(List)
 return Result


def GetLimits(Ways):
 return [ [Way['nodes'][0], Way['nodes'][-1]] for Way in Ways ]


def GetNodes(Ways):
 return [ [Node for Node in Way['nodes']] for Way in Ways ]


def GetCoord(Ways):
 Nodes = IslandLine(Ways)
 List = [ID for Row in Nodes for ID in Row]
 Result = { Node['id']: (Node['lat'], Node['lon']) for Node in OSM.ReadNodes(List) }
 return [ [ Result[ID] for ID in Row ] for Row in Nodes ]


def GetNames(Tag, Lang):
 Names = ";".join([Tag.get(f'name:{Lang}', ""), Tag.get(f'alt_name:{Lang}', "")])
 return [Name.strip() for Name in Names.split(";") if Name]


#


def GetPlace():
 logger.info("Place")
 Place = {}
 for ID, Value in OSM.ExecuteSql("SELECT node_id, value FROM node_tags WHERE key = 'place';"):
  if Value in ["city", "town", "village", "hamlet", "neighbourhood", "locality"]:
   Node = OSM.ReadNode(ID)
   Tag = Node['tags']
   Bes, Rus = GetNames(Tag, 'be'), GetNames(Tag, 'ru')
   if Bes and Rus:
    for Ru in Rus:
     if Ru in Place:
      for Be in Bes:
       Place[Ru].add(Be)
     else:
      Place[Ru] = set(Bes)
 return Place


def GetNormalizeRef(Ref):
 Result = Ref
 if Result[0:1] in "МРН" and Result[1:2] in "0123456789":
  if Result[0:1] == "М":
   return Result.replace("М", "М-").replace("/П", "/П ").replace("/Е", "/Е ").replace("  ", " ")
  elif Result[0:1] == "Р":
   return Result.replace("Р", "Р-").replace("/П", "/П ").replace("/Е", "/Е ").replace("  ", " ")
  elif Result[0:1] == "Н":
   return Result.replace("Н", "Н-")
  else:
   return None


def LoadWays():
 #logger.info("missing: load ways")
 Result = {}
 for ID, _ in OSM.ExecuteSql("SELECT way_id, value FROM way_tags WHERE key = 'ref';"):
  Way = OSM.ReadWay(ID)
  Tag = Way['tags']
  if ('highway' in Tag or 'ferry' in Tag) and 'ref' in Tag:
   Ref = GetNormalizeRef(Tag.get('ref', ""))
   if Ref:
    Result[ID] = Ref
 return Result


def LoadRelations():
 #logger.info("missing: load relations")
 Result = {}
 for ID, _ in OSM.ExecuteSql("SELECT relation_id, value FROM relation_tags WHERE key = 'route';"):
  Relation = OSM.ReadRelation(ID)
  Tag = Relation['tags']
  if Tag.get('type', "") == "route" and Tag.get('route', "") == "road" and Tag.get('network', "") in ["by:national", "by:regional"]:
   Result[ID] = { 'official_ref': Tag.get('official_ref', "невядома"), 'ref': Tag.get('ref', ""), 'be': Tag.get('name:be', ""), 'ru': Tag.get('name:ru', ""), 'members': Relation['members'] }
 return Result


def LoadRelationsID():
 #logger.info("missing: load relations id")
 Result = []
 for ID in [1246287, 1246288, 1246286]:
  for _, Ref, _ in OSM.ExecuteSql("SELECT type, ref, role FROM relation_members WHERE relation_id = ? AND type = 'relation' ORDER BY member_order;", Params=[ID]):
   Result.append(Ref)
 return Result


def GetWaysID(Relations, RelationsID):
 #logger.info("missing: get ways id")
 Result = []
 for ID, Relation in Relations.items():
  if ID in RelationsID:
   Result += [ Way['ref'] for Way in Relation['members'] ]
 return Result


def GetRelationOk(Relations, RelationsID):
 #logger.info("missing: get relation ok")
 Result = {}
 for ID, Relation in Relations.items():
  if ID in RelationsID:
   Ref = Relation['official_ref']
   Item = { 'ID': ID, 'Key': Relation['ref'], 'Be': Relation['be'], 'Ru': Relation['ru'] }
   Result[Ref] = Item
 return Result


def GetMissingRelation(Relations, RelationsID):
 #logger.info("missing: missing relation")
 Result = []
 for ID, Relation in Relations.items():
  if ID not in RelationsID:
   Item = { 'ID': ID, 'Key': Relation['ref'], 'Be': Relation['be'], 'Ru': Relation['ru'] }
   Result.append(Item)
 return Result


def GetMissingWay(Ways, WaysID):
 #logger.info("missing: missing way")
 Result = {}
 for ID, Ref in Ways.items():
  if ID not in WaysID:
   if Ref in Result:
    Result[Ref].append(ID)
   else:
    Result[Ref] = [ID]
 return Result


def GetRelationsForWays(MissingWays, RelationOk):
 #logger.info("missing: missing relation for ways")
 Result = {}
 for Ref in MissingWays:
  if Ref not in Result:
   if Ref in RelationOk.keys():
    Result[Ref] = RelationOk[Ref]
 return Result


def GetMissing():
 logger.info("Missing")
 Result = {}
 Ways = LoadWays()
 Relations = LoadRelations()
 RelationsID = LoadRelationsID()
 WaysID = GetWaysID(Relations, RelationsID)
 RelationOk = GetRelationOk(Relations, RelationsID)
 MissingRelations = GetMissingRelation(Relations, RelationsID)
 MissingWays = GetMissingWay(Ways, WaysID)
 MissingRelationsForWays = GetRelationsForWays(MissingWays, RelationOk)
 Result['Relations'] = MissingRelations
 Result['Ways'] = MissingWays
 Result['RelationsForWays'] = MissingRelationsForWays
 #logger.info("done")
 return Result


#


def LoadDesc(FileName):
 Result = {}
 FileName = os.path.join(Path, "docs", FileName)
 for Line in open(FileName, mode="r", encoding="utf-8"):
  Tag, Desc, Law = Line.strip().split(";")
  Result[Tag] = { 'Desc': Desc, 'Law': Law }
 return Result


def GetRef(Tag):
 return Tag.get('official_ref', f"error-{random.randint(0, 9999)}")


def GetErrorLine(Key, Relation):
 Result = {}
 Result['Key'] = Key
 Result['Color'] = "#ff9090"
 Tag = Relation['tags']
 Type = Relation['type']
 Result['Type'] = Type
 Result['ID'] = Relation.get('id', None)
 Be = Tag.get('name', "")
 if Be:
  Result['Be'] = Be
 Ru = Tag.get('name:ru', "")
 if Ru:
  Result['Ru'] = Ru
 #
 Result['Relation'] = []
 Result['Relation'] += CheckRef(Key)
 Result['Relation'] += CheckRelation(Type)
 Result['Relation'] += ["'ref' адсутнічае ў Законе"]
 return Result


CountParse = 0


def GetLine(Class, Key, Value, Relations, Place, Highways):
 Result = {}
 Result['Key'] = Key
 Relation = Relations.get(Key, {})
 if Relation:
  #logger.info(f"parse relation {Relation['id']}")
  Type = Relation['type']
  Result['Type'] = Type
  Result['ID'] = Relation['id']
  Tag = Relation['tags']
  Be = Tag.get('name', "")
  if Be:
   Result['Be'] = Be
  Ru = Tag.get('name:ru', "")
  if Ru:
   Result['Ru'] = Ru
  #
  Result['Error'] = []
  #
  Result['Error'] += CheckRef(Key)
  Result['Error'] += CheckRelation(Type)
  Result['Error'] += CheckTag(Tag, Class)
  Result['Error'] += CheckClass(Tag, Class)
  Result['Error'] += CheckBe(Tag)
  Result['Error'] += CheckRu(Tag, Value['Desc'])
  Result['Error'] += CheckOfficialName(Tag)
  Result['Error'] += CheckWrong(Tag)
  Result['Error'] += CheckPair(Tag)
  Result['Error'] += CheckLength(Tag)
  Result['Error'] += CheckImpossible(Tag)
  Result['Error'] += CheckEqRef(Tag)
  Result['Error'] += CheckBadRefInRelation(Relation)
  Result['Error'] += CheckDoubleRef(Relation)
  Result['Error'] += CheckWays(Relation)
  Result['Error'] += CheckRefInRelation(Relation, Relations)
  #
  Result['Error'] += CheckTouch(Relation, Relations, Highways)
  Result['Error'] += CheckPlace(Tag, Place)
  Result['Error'] += CheckLaw(Tag, Highways)
  #
  Ways = GetWays(Relation)
  if Ways:
   Result['Error'] += CheckTagsInWay(Tag, Ways)
   Result['Error'] += CheckFixme(Ways)
   Result['Error'] += CheckHighway(Ways)
   Result['Error'] += CheckDoubleWay(Ways)
   Result['Error'] += CheckDoubleRelation(Ways, Relations)
  #
  Ways = GetWays(Relation, Role=["", "route", "forward"]) #"backward"
  if Ways:
   Result['Error'] += CheckCross(Ways)
   Result['Error'] += CheckIsland(Ways)
   Result['Error'] += CheckHaversine(Ways)
  #
  Result['Color'] = "#ffc0c0" if Result['Error'] else "#bbffbb"
 else:
  Result['Color'] = "#d6e090"
  Result['Ru'] = Value['Desc']
  Result['Relation'] = ["relation адсутнічае"]
 #
 global CountParse
 CountParse += 1
 if CountParse % 1000 == 0:
  logger.info(f"parse relation #{CountParse}")
 return Result


#


def ReadOSM(Class, R):
 logger.info(f"Read relation {R}")
 Result, List = {}, {}
 #
 Relation = OSM.ReadRelation(R)
 for Member in Relation['members']:
  match Member['type']:
   case "node":
    Item = OSM.ReadNode(Member['ref'])
   case "way":
    Item = OSM.ReadWay(Member['ref'])
   case "relation":
    Item = OSM.ReadRelation(Member['ref'])
   case _:
    logger.error(f"Unknown type = \"{Member['type']}\"")
  Item['class'] = Class
  Ref = GetRef(Item['tags'])
  Item['double'] = Ref in Result
  Result[Ref] = Item
 #
 return Result


def GetNotFound(Class, Relation, CSV):
 Result = { i: Relation[i] for i in Relation.keys() - CSV.keys() }
 return { Key: Value for Key, Value in Result.items() if Value['class'] == Class }


def GetOSM(Class, Relations, FileName, Place, Highways):
 logger.info(f"Parse relation {Class}")
 Result = []
 #
 FileName = os.path.join(Path, "docs", FileName)
 Desc = LoadDesc(FileName)
 #
 global CountParse
 CountParse = 0
 Result += [ GetLine(Class, Key, Value, Relations, Place, Highways) for Key, Value in Desc.items() ] 
 Result += [ GetErrorLine(Key, Relation) for Key, Relation in GetNotFound(Class, Relations, Desc).items()]
 logger.info(f"count parse relation {CountParse}")
 return Result


def GetDateTime():
 return OSM.GetDateTime()
