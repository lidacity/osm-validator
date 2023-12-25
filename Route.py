#https://josm.openstreetmap.de/wiki/Ru%3AHelp/RemoteControlCommands

import os
import random
from datetime import datetime
from collections import Counter

import re
re._MAXCACHE = 4096

from loguru import logger
from haversine import haversine

from Validator import Validator



class RouteValidator(Validator):

 Classes = {
  'М': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:national', 'name': None, 'name:be': None, 'name:ru': None, },
  'Р': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:national', 'name': None, 'name:be': None, 'name:ru': None, },
  'Н': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:regional', 'name': None, 'name:be': None, 'name:ru': None, },
 }


 def CheckRef(self, Key):
  Result = []
  if Key[:6] == "error-":
   Result.append(f"несапраўдны 'official_ref'")
  return Result


 def CheckRelation(self, Type):
  Result = []
  if Type != "relation":
   Result.append(f"не relation")
  return Result


 def CheckTag(self, Tag, Class):
  Result = []
  for TagName, Value in self.Classes[Class].items():
   if TagName not in Tag:
    Result.append(f"не знойдзены '{TagName}'")
   elif Value is not None:
    if self.JoinName(Tag, TagName) != Value:
     Result.append(f"'{TagName}' не роўны \"{Value}\"")
  return Result


 def CheckClass(self, Tag, Class):
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


 def CheckBe(self, Tag):
  Result = []
  Name = self.JoinName(Tag, 'name')
  Be = self.JoinName(Tag, 'name:be')
  if Name != Be:
   Result.append(f"'name:be' не роўны 'name'")
  return Result


 def CheckRu(self, Tag, Name):
  Result = []
  Ru = self.JoinName(Tag, 'name:ru')
  if Name != Ru:
   Result.append(f"'name:ru' не супадае з Законам")
  return Result


 def CheckOfficialName(self, Tag):
  Result = []
  for TagName in ['official_name', 'official_name:be', 'official_name:ru', 'description', 'description:be', 'description:ru', 'source:ref:date', ]:
   if TagName in Tag:
    Result.append(f"непатрэбны '{TagName}'")
  if 'fixme' in Tag:
   Result.append(f"'fixme' у relation")
  return Result


 Wrong = {
  'Latin': {'re': re.compile("[a-zA-Z]").search, 'Desc': "лацінскія літары"},
  'Number': {'re': re.compile("[a-zA-Zа-яА-ЯёЁўЎіІʼ][0-9]|[0-9][a-zA-Zа-яА-ЯёЁўЎіІʼ]").search, 'Desc': "няправільныя лічбы"},
  'Hyphen': {'re': re.compile("[^ ]–|–[^ …]|[ ]-|-[ ]").search, 'Desc': "неправільны злучок"},
  'Bracket': {'re': re.compile("[^ «(]\(|\)[^ …»)]").search, 'Desc': "неправільныя дужкі"},
  'Special': {'re': re.compile("|".join(map(re.escape, ".:;!_*+#¤%&[]{}$@^\\'’—"))).search, 'Desc': "спецыяльныя знакі"},
  'Abbreviations': {'re': re.compile("|".join([re.escape(s) for s in ["а/д", "г.п.", "г.", "аг.", "п.", "д.", "х.", "ж/д", "ст.", "с/т", "с/с", "хоз.", "Ж/д", "А/д", "С/т", "Ст.", "обл.", "Гр.", "р-на", "вул.", "ул.", ]])).search, 'Desc': "недапушчальны скарот"},
 }


 Replace = { 'SOS': "СОС", 'III': "3", 'II': "2", 'I': "1", }


 def CheckWrong(self, Tag):
  Result = []
  for TagName in ['name:be', 'name:ru']:
   if TagName in Tag:
    S = self.JoinName(Tag, TagName)
    for Key, Value in self.Replace.items():
     S = S.replace(Key, Value)
    for _, Value in self.Wrong.items():
     R = Value['re'](S)
     if R:
      Result.append(f"у '{TagName}' {Value['Desc']} \"{R[0]}\"")
      break
  return Result



 Pair = {
  'Split': re.compile("|".join(map(re.escape, "{}()[]\"«»„“")) + "|" + "|".join(["\B'", "'\B"])).findall,
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
     break
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
     break
  return Result


 Refs = { 'ok': re.compile("[МР]-[0-9]+/[ЕП] [0-9]+|[МРН]-[0-9]+"), 'bad': re.compile("[МРН][0-9]+"), }


 def GetList(self, Name, Type):
  return re.findall(self.Refs[Type], Name)


 def GetIndex(self, Name, Ref):
  return [Index.start() for Index in re.finditer(f"{Ref}[^/]", Name)]


 def ExcludeRef(self, Name, Index):
  return Name[Index-1:].strip()[:1] in ["(", ")", "", "\""]



 def CheckEqRef(self, Tag):
  Result = []
  Refs = { 'name:be': [], 'name:ru': [] }
  for TagName in ['name:be', 'name:ru']:
   if TagName in Tag:
    for Ref in self.GetList(self.JoinName(Tag, TagName), 'ok'):
     Refs[TagName].append(Ref)
  if Counter(Refs['name:be']) != Counter(Refs['name:ru']):
   Result.append(f"у 'name:be' і 'name:ru' не аднолькавыя 'ref'")
  return Result


 def CheckBadRefInRelation(self, Relation):
  Result = []
  Tag = Relation['tags']
  for TagName in ['name:be', 'name:ru']:
   if TagName in Tag:
    if self.GetList(self.JoinName(Tag, TagName), 'bad'):
     Result.append(f"у '{TagName}' не вызначаны 'ref'")
  return Result


 def CheckDoubleRef(self, Relation):
  Result = []
  Custom = Relation['custom']
  if Custom['double']:
   Result.append(f"існуе дублікат 'ref'")
  return Result


 def CheckWays(self, Relation):
  Result = []
  for Member in Relation['members']:
   if Member['type'] != "way":
    Result.append(f"у relation прысутнічае ня толькі way")
    break
  return Result


 def CheckRefInRelation(self, Relation, Relations):
  Result = []
  Tag = Relation['tags']
  for TagName in ['name:be', 'name:ru']:
   if TagName in Tag:
    for Ref in self.GetList(self.JoinName(Tag, TagName), 'ok'):
     if Ref in Relations:
      for Index in self.GetIndex(self.JoinName(Tag, TagName), Ref):
       Tag2 = Relations[Ref]['tags'] # з агульнага спісу аўтадарог
       if TagName in Tag2:
        I = Index + len(Ref) + 1
        S2 = self.JoinName(Tag2, TagName) # з агульнага спісу аўтадарог
        S = self.JoinName(Tag, TagName)[I:I+len(S2)]
        Len = len(S2)# - (1 if S2[-1:] == "…" else 0)
        if Len == 0:
         Len = len(S2)
        if S2[:Len] != S[:Len] and not self.ExcludeRef(self.JoinName(Tag, TagName), I) and S[:2] not in ["от", "ад"]:
         Result.append(f"\"{Ref}\" не адпавядае найменню ў '{TagName}'")
         break
     else:
      Result.append(f"у '{TagName}' не вызначаны \"{Ref}\"")
  return Result


 def CheckTouch(self, Relation, Relations, Highways):
  Result = []
  Tag = Relation['tags']
  if 'name:ru' in Tag:
   Name = self.JoinName(Tag, 'name:ru')
   Roads = self.GetList(Name, 'ok')
   for Ref in Roads:
    Highway = Highways[Ref]
    Name = Name.replace(f"{Ref} {Highway['Desc']}", f"{Ref}")
   Roads = self.GetList(Name, 'ok')
   if Roads:
    Nodes = set(self.GetAllNodes(Relation))
    for Ref in Roads:
     if Ref in Relations:
      Touch = set(self.GetAllNodes(Relations[Ref]))
      if not Nodes & Touch:
       Result.append(f"не дакранаецца да \"{Ref}\"")
       break
     else:
      Result.append(f"не знойдзены \"{Ref}\"")
      break
  return Result


 Words = re.compile(r"\b[А-ЯЁЎІ][\wʼ]+[ -][А-ЯЁЎІ][\wʼ]+\b|\b[А-ЯЁЎІ][\wʼ]+[ -]\d+\b|\b[А-ЯЁЎІ][\wʼ]+\b|«\b[А-ЯЁЎІ][\wʼ -]+\b»")
 #\b[А-ЯЁЎІ][\wʼ]+[ -][А-ЯЁЎІ][\w+ʼ]\b = Марʼіна Горка | Буда-Кашалёва
 #\b[А-ЯЁЎІ][\wʼ]+[ -]\d+\b =  Бучамля 1 | Вулька-1
 #\b[А-ЯЁЎІ][\wʼ]+\b = Ліда
 #«\b[А-ЯЁЎІ][\wʼ -]+\b» = Сасновая балка

 NormalizeWords = {
  'name:be': [("-", " ")],
  'name:ru': [("-", " "), ("ё", "е")],
 }


 def GetNormalizePlace(self, Name, Lang):
  Result = Name.strip("«»")
  for From, To in self.NormalizeWords[Lang]:
   Result = Result.replace(From, To)
  return Result



 def CheckPlace(self, Tag, Place):
  Result = []
  #
  Name = self.JoinName(Tag, 'name:be')
  Be = self.GetNormalizePlace(Name, 'name:be')
  Bes = [self.GetNormalizePlace(Item, 'name:be') for Item in self.Words.findall(Be)]
  #
  Name = self.JoinName(Tag, 'name:ru')
  Ru = self.GetNormalizePlace(Name, 'name:ru')
  Rus = [self.GetNormalizePlace(Item, 'name:ru') for Item in self.Words.findall(Ru)]
  #
  for Ru in Rus:
   if Ru in Place and not Result:
    for Name in Place[Ru]:
     if Name in Bes:
      break
    else:
     Result.append(f"не супадаюць населеныя пункты ў 'name:be' і 'name:ru'")
  return Result


 def CheckLaw(self, Tag, Highways):
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


 def CheckTagsInWay(self, Tag, Ways):
  Result = []
  for Way in Ways:
   if Tag.get('ref', "") != Way['tags'].get('ref', None):
    Result.append(f"не супадае 'ref' у relation і 'ref' яе ways")
    break
  #
  Tags = {
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


 def CheckFixme(self, Ways):
  Result = []
  for Way in Ways:
   if "fixme" in Way['tags']:
    Result.append(f"'fixme' у way")
    break
  return Result


 def CheckHighway(self, Ways):
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


 def CheckDoubleRelation(self, Ways, Relations):
  Result = []
  for Way in Ways:
   Count = 0
   for Relation in self.RelationsForWay(Way['id']):
    if Relation['tags'].get('official_ref', "") in Relations:
     Count += 1
   if Count > 1:
    Result.append(f"way знаходзяцца ў некалькіх relation")
    break
   if Count == 0:
    Result.append(f"way не знаходзіцца нават у адным relation")
  return Result


 def CheckCoordPlace(self, Tag, Ways, Coords, Highways):
  Result = []
  Name = self.JoinName(Tag, 'name:be')
  for Ref in self.GetList(Name, 'ok'):
   Highway = Highways.get(Ref, "")
   Name = Name.replace(f"{Ref} {Highway}", f"{Ref}")
  Names = [Item.strip("«»") for Item in self.Words.findall(Name)]
  List = set(self.GetListNodes(Ways))
  CoordsWays = [ (Node['lat'], Node['lon']) for Node in self.ReadNodes(List) ]
  for Name in Names:
   if Name in Coords and not Result:
    Ok = False
    for Coord1 in Coords[Name]:
     if not Ok:
      for Coord2 in CoordsWays:
       if haversine(Coord1, Coord2) < 10:
        Ok = True
        break
    if not Ok:
     Result.append(f"не праходзіць побач з \"{Name}\"")
  return Result


 def CheckCross(self, Ways):
  Result = []
  Limits = self.GetLimits(Ways)
  Nodes = [Node for Row in Limits for Node in Row]
  c = Counter(Nodes)
  if max(c.values()) > 2:
   Result.append(f"замкнутая ў пятлю ці перакрыжаваная")
  else:
   Nodes = self.GetNodes(Ways)
   Nodes1 = [Node for Row in Nodes for Node in Row]
   Nodes2 = [Node for Row in Nodes for Node in Row[1:-1]]
   c = Counter(Nodes1 + Nodes2)
   if max(c.values()) > 2:
    Result.append(f"замкнутая ў пятлю ці перакрыжаваная")
  return Result


 def CheckIsland(self, Ways):
  Result = []
  if self.Island(Ways) != self.IslandLine(Ways):
   Result.append(f"way не паслядоўныя")
  return Result


 def CheckHaversine(self, Ways):
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
   if max(Lengths) > 3:
    Result.append(f"way занадта разарваны")
  return Result


 #

 def GetNames(self, Tag, Lang):
  Names = ";".join([ Tag.get(f'{Name}:{Lang}', "") for Name in ['name', 'alt_name', 'short_name'] ])
  return [self.GetNormalizePlace(Name, f"name:{Lang}") for Name in Names.split(";") if Name]


 #


 KeyPlace = {
  'place': ["city", "town", "village", "hamlet", "isolated_dwelling", "suburb", "neighbourhood", "locality"],
  'natural': ["water"],
  'waterway': ["river"],
  'office': ["government"],
  'railway': ["station", "halt"],
  'historic': ["memorial"],
  'amenity': ["school"],
  'landuse': ["allotments", "quarry", "residential", "industrial"],
  'leisure': ["resort"],
  'highway': ["bus_stop"],
 }


 def GetPlace(self):
  logger.info("read place")
  Result = {}
  #
  Places = []
  for Key, Values in self.KeyPlace.items():
   for Node in self.GetNodeKey(Key, Values=Values):
    Places.append(Node['tags'])
   for Way in self.GetWayKey(Key, Values=Values):
    Places.append(Way['tags'])
  #
  for Tag in Places:
   Bes, Rus = self.GetNames(Tag, 'be'), self.GetNames(Tag, 'ru')
   if Bes and Rus:
    for Ru in Rus:
     if Ru in Result:
      for Be in Bes:
       Result[Ru].add(Be)
     else:
      Result[Ru] = set(Bes)
  return Result


 def GetCoordPlace(self):
  logger.info("read coord place")
  Result = {}
  #
  Places = []
  for Key, Values in self.KeyPlace.items():
   for Node in self.GetNodeKey(Key, Values=Values):
    Coord = (Node['lat'], Node['lon'])
    Places.append((Coord, Node['tags']))
   for Way in self.GetWayKey(Key, Values=Values):
    for Node in self.ReadNodes(Way['nodes']):
     Coord = (Node['lat'], Node['lon'])
     Places.append((Coord, Way['tags']))
  #
  for Coord, Tag in Places:
   Bes = self.GetNames(Tag, 'be')
   if Bes:
    for Be in Bes:
     if Be not in Result:
      Result[Be] = set()
     Result[Be].add(Coord)
  return Result


 def GetNormalizeRef(self, Ref):
  Result = Ref
  if Result[0:1] in "МРН" and Result[1:2] in "0123456789":
   match Result[0:1]:
    case "М":
     return Result.replace("М", "М-").replace("/П", "/П ").replace("/Е", "/Е ").replace("  ", " ")
    case "Р":
     return Result.replace("Р", "Р-").replace("/П", "/П ").replace("/Е", "/Е ").replace("  ", " ")
    case "Н":
     return Result.replace("Н", "Н-")
    case _:
     return None


 def GetHighways(self, TagName='name:be'):
  logger.info("read highways description")
  Result = {}
  for Relation in self.GetRelationKey('route'):
   Tag = Relation['tags']
   if Tag.get('type', "") == "route" and Tag.get('route', "") == "road" and Tag.get('network', "") in ["by:national", "by:regional"]:
    if 'official_ref' in Tag:
     Ref = Tag['official_ref']
     Result[Ref] = self.JoinName(Tag, TagName)
  return Result


 def LoadWays(self):
  #logger.info("missing: load ways")
  Result = {}
  for Way in self.GetWayKey('ref'):
   ID, Tag = Way['id'], Way['tags']
   if ('highway' in Tag or 'ferry' in Tag) and 'ref' in Tag:
    Ref = self.GetNormalizeRef(Tag.get('ref', ""))
    if Ref:
     Result[ID] = Ref
  return Result


 def LoadRelations(self):
  #logger.info("missing: load relations")
  Result = {}
  for Relation in self.GetRelationKey('route'):
   ID, Tag = Relation['id'], Relation['tags']
   if Tag.get('type', "") == "route" and Tag.get('route', "") == "road" and Tag.get('network', "") in ["by:national", "by:regional"]:
    Result[ID] = { 'official_ref': Tag.get('official_ref', "невядома"), 'ref': Tag.get('ref', ""), 'be': self.JoinName(Tag, 'name:be'), 'ru': self.JoinName(Tag, 'name:ru'), 'members': Relation['members'] }
  return Result


 def LoadRelationsID(self, List):
  #logger.info("missing: load relations id")
  Result = []
  for ID in List:
   for _, Ref, _ in self.GetRelationMembers(ID):
    Result.append(Ref)
  return Result


 def GetWaysID(self, Relations, RelationsID):
  #logger.info("missing: get ways id")
  Result = []
  for ID, Relation in Relations.items():
   if ID in RelationsID:
    Result += [ Way['ref'] for Way in Relation['members'] ]
  return Result


 def GetRelationOk(self, Relations, RelationsID):
  #logger.info("missing: get relation ok")
  Result = {}
  for ID, Relation in Relations.items():
   if ID in RelationsID:
    Ref = Relation['official_ref']
    Item = { 'ID': ID, 'Key': Relation['ref'], 'Be': Relation['be'], 'Ru': Relation['ru'] }
    Result[Ref] = Item
  return Result


 def GetMissingRelation(self, Relations, RelationsID):
  #logger.info("missing: missing relation")
  Result = []
  for ID, Relation in Relations.items():
   if ID not in RelationsID:
    Item = { 'ID': ID, 'Key': Relation['ref'], 'Be': Relation['be'], 'Ru': Relation['ru'] }
    Result.append(Item)
  return Result


 def GetMissingWay(self, Ways, WaysID):
  #logger.info("missing: missing way")
  Result = {}
  for ID, Ref in Ways.items():
   if ID not in WaysID:
    if Ref in Result:
     Result[Ref].append(ID)
    else:
     Result[Ref] = [ID]
  return Result


 def GetRelationsForWays(self, MissingWays, RelationOk):
  #logger.info("missing: missing relation for ways")
  Result = {}
  for Ref in MissingWays:
   if Ref not in Result:
    if Ref in RelationOk.keys():
     Result[Ref] = RelationOk[Ref]
  return Result


 def GetMissing(self, List):
  logger.info("Missing")
  Result = {}
  Ways = self.LoadWays()
  Relations = self.LoadRelations()
  RelationsID = self.LoadRelationsID(List)
  WaysID = self.GetWaysID(Relations, RelationsID)
  RelationOk = self.GetRelationOk(Relations, RelationsID)
  MissingRelations = self.GetMissingRelation(Relations, RelationsID)
  MissingWays = self.GetMissingWay(Ways, WaysID)
  MissingRelationsForWays = self.GetRelationsForWays(MissingWays, RelationOk)
  Result['Relations'] = MissingRelations
  Result['Ways'] = MissingWays
  Result['RelationsForWays'] = MissingRelationsForWays
  #logger.info("done")
  return Result


 def AtoI(self, Text):
  return int(Text) if Text.isdigit() else Text


 Sorted = re.compile("(\d+)")


 def NaturalKeys(self, text):
  return [ self.AtoI(c) for c in self.Sorted.split(text) ]


 def GetNetwork(self, Parse, All):
  logger.info("Network")
  Relations = {}
  for _, Value in Parse.items():
   Class, ID, Main = Value['Cyr'], Value['ID'], Value['Main']
   if Main or All:
    Relations |= self.ReadOSM(Class, ID)
  #
  Nodes, IDs = {}, {}
  for Ref, Relation in Relations.items():
   Ways = self.GetWays(Relation)
   Nodes[Ref] = set(self.GetListNodes(Ways))
   IDs[Ref] = Relation['id']
  #
  logger.info("parse network")
  Island = []
  while Nodes:
   for Ref, Node in Nodes.items():
    for Item in Island:
     if Item['Nodes'] & Node:
      Item['Ref'].append(Ref)
      Item['Nodes'] |= Node
      del Nodes[Ref]
      break
    else:
     continue
    break
   else:
    Item = { 'Ref': [Ref], 'Nodes': Node }
    Island.append(Item)
    del Nodes[Ref]
  #
  Result = [ { Ref: IDs[Ref] for Ref in sorted(Item['Ref'], key=self.NaturalKeys) } for Item in Island ]
  Result.sort(reverse=True, key=len)
  return Result[1:]


 def LoadDesc(self, FileName):
  Result = {}
  FileName = os.path.join(self.Path, "docs", FileName)
  for Line in open(FileName, mode="r", encoding="utf-8"):
   Tag, Desc, Law = Line.strip().split(";")
   Result[Tag] = { 'Desc': Desc, 'Law': Law }
  return Result


 def GetRef(self, Tag):
  return Tag.get('official_ref', f"error-{random.randint(0, 9999)}")


 def ReadOSM(self, Class, R):
  #logger.info(f"read relation {R}")
  Result, List = {}, {}
  #
  Relation = self.ReadRelation(R)
  for Member in Relation['members']:
   match Member['type']:
    case "node":
     Item = self.ReadNode(Member['ref'])
    case "way":
     Item = self.ReadWay(Member['ref'])
    case "relation":
     Item = self.ReadRelation(Member['ref'])
    case _:
     logger.error(f"Unknown type = \"{Member['type']}\"")
   #
   Ref = self.GetRef(Item['tags'])
   Custom = { 'class': Class, 'double': Ref in Result }
   Item['custom'] = Custom
   #
   Result[Ref] = Item
  #
  return Result


 #


 def GetErrorLine(self, Key, Relation):
  Result = {}
  Result['Key'] = Key
  Result['Color'] = "#ff9090"
  Tag = Relation['tags']
  Type = Relation['type']
  Result['Type'] = Type
  Result['ID'] = Relation.get('id', None)
  Be = self.JoinName(Tag, 'name')
  if Be:
   Result['Be'] = Be
  Ru = self.JoinName(Tag, 'name:ru')
  if Ru:
   Result['Ru'] = Ru
  #
  Result['Error'] = []
  Result['Error'] += self.CheckRef(Key)
  Result['Error'] += self.CheckRelation(Type)
  Result['Error'] += ["'ref' адсутнічае ў Законе"]
  return Result


 def GetSeparated(self, Parse):
  logger.info("Separated")
  Relations = {}
  for _, Value in Parse.items():
   Class, ID = Value['Cyr'], Value['ID']
   Relations |= self.ReadOSM(Class, ID)
  #
  Highways = {}
  for _, Value in Parse.items():
   FileName = Value['FileName']
   Highways |= self.LoadDesc(FileName)
  #
  return [ self.GetErrorLine(Key, Relations[Key]) for Key in Relations.keys() - Highways.keys() ]


 #


 def GetLine(self, Class, Key, Value, Relations, Place, Coords, Highways, HighwaysBe):
  Result = {}
  Result['Key'] = Key
  Relation = Relations.get(Key, {})
  if Relation:
   #logger.info(f"parse relation {Relation['id']}")
   Type = Relation['type']
   Result['Type'] = Type
   Result['ID'] = Relation['id']
   Result['UID'] = Relation['uid']
   Tag = Relation['tags']
   Be = self.JoinName(Tag, 'name')
   if Be:
    Result['Be'] = Be
   Ru = self.JoinName(Tag, 'name:ru')
   if Ru:
    Result['Ru'] = Ru
   #
   Result['Error'] = []
   #
   Result['Error'] += self.CheckRef(Key)
   Result['Error'] += self.CheckRelation(Type)
   Result['Error'] += self.CheckTag(Tag, Class)
   Result['Error'] += self.CheckClass(Tag, Class)
   Result['Error'] += self.CheckBe(Tag)
   Result['Error'] += self.CheckRu(Tag, Value['Desc'])
   Result['Error'] += self.CheckOfficialName(Tag)
   Result['Error'] += self.CheckWrong(Tag)
   Result['Error'] += self.CheckPair(Tag)
   Result['Error'] += self.CheckLength(Tag)
   Result['Error'] += self.CheckImpossible(Tag)
   Result['Error'] += self.CheckEqRef(Tag)
   Result['Error'] += self.CheckBadRefInRelation(Relation)
   Result['Error'] += self.CheckDoubleRef(Relation)
   Result['Error'] += self.CheckWays(Relation)
   Result['Error'] += self.CheckRefInRelation(Relation, Relations)
   #
   Result['Error'] += self.CheckTouch(Relation, Relations, Highways)
   Result['Error'] += self.CheckPlace(Tag, Place)
   Result['Error'] += self.CheckLaw(Tag, Highways)
   #
   Ways = self.GetWays(Relation)
   if Ways:
    Result['Error'] += self.CheckTagsInWay(Tag, Ways)
    Result['Error'] += self.CheckFixme(Ways)
    Result['Error'] += self.CheckHighway(Ways)
    Result['Error'] += self.CheckDoubleWay(Ways)
    Result['Error'] += self.CheckName(Ways)
    Result['Error'] += self.CheckDoubleRelation(Ways, Relations)
    Result['Error'] += self.CheckCoordPlace(Tag, Ways, Coords, HighwaysBe)
   #
   Ways = self.GetWays(Relation, Role=["", "route", "forward"]) #"backward"
   if Ways:
    Result['Error'] += self.CheckCross(Ways)
    Result['Error'] += self.CheckIsland(Ways)
    Result['Error'] += self.CheckHaversine(Ways)
   #
   Result['Color'] = "#ffc0c0" if Result['Error'] else "#bbffbb"
  else:
   Result['Color'] = "#d6e090"
   Result['Ru'] = Value['Desc']
   Result['Error'] = ["relation адсутнічае"]
  #
  self.CountParse += 1
  if self.CountParse % 1000 == 0:
   logger.info(f"parse relation #{self.CountParse}")
  return Result


 def GetOSM(self, Class, Desc, Relations, Place, Coords, Highways, HighwaysBe):
  logger.info(f"parse relations {Class}")
  self.CountParse = 0
  Result = [ self.GetLine(Class, Key, Value, Relations, Place, Coords, Highways, HighwaysBe) for Key, Value in Desc.items() ] 
  logger.info(f"count parse relation {self.CountParse}")
  return Result


 def GetHighway(self, Parse):
  logger.info("Highway")
  Relations = {}
  for _, Value in Parse.items():
   Class, ID = Value['Cyr'], Value['ID']
   Relations |= self.ReadOSM(Class, ID)
  #
  Place = self.GetPlace()
  Coords = self.GetCoordPlace()
  HighwaysBe = self.GetHighways()
  #
  Highways = {}
  for _, Value in Parse.items():
   FileName = Value['FileName']
   Highways |= self.LoadDesc(FileName)
  #
  Result = {}
  for Key, Value in Parse.items():
   Class, Description, FileName = Value['Cyr'], Value['Desc'], Value['FileName']
   FileName = os.path.join(self.Path, "docs", FileName)
   Desc = self.LoadDesc(FileName)
   Items = self.GetOSM(Class, Desc, Relations, Place, Coords, Highways, HighwaysBe)
   Result[Key] = { 'Desc': Description, 'List': Items }
  return Result


 def GetError(self, Highway):
  logger.info("Error highway")
  Result = {}
  for Class, Roads in Highway.items():
   Items = []
   for Road in Roads['List']:
    if 'ID' in Road and Road['Error']:
     Items.append(Road)
   if Items:
    Result[Class] = { 'Desc': Roads['Desc'], 'List': Items }
  return Result


 def GetRelation(self, Highway):
  Result = {}
  for Class, Roads in Highway.items():
   Items = []
   for Road in Roads['List']:
    if 'ID' not in Road and Road['Key'][:6] != "error-":
     Items.append(Road)
   if Items:
    Result[Class] = { 'Desc': Roads['Desc'], 'List': Items }
  return Result


 def GetUID(self):
  FileName = os.path.join(".data", ".uid")
  for Line in open(FileName, mode="r", encoding="utf-8"):
   return int(Line)


# -=-=-=-=-=-


def Generate(Check, Network):
 Route = RouteValidator()
 Result = {}
 #Result['PravoError'], Result['Pravo'] = False, []
 #Result['Highway'] = {}
 #Result['Error'] = {}
 #Result['Relation'] = {}
 #Result['Separated'] = []
 #Result['Missing'] = { 'Relations': [], 'Ways': {}, 'RelationsForWays': {} }
 #Result['Network'] = {}
 #Result['PBFDateTime'] = Route.GetDateTime()
 #Result['DateTime'] = Route.GetNow()
 Highway = Route.GetHighway(Check)
 Result['Highway'] = Highway
 Result['Error'] = Route.GetError(Highway)
 Result['Relation'] = Route.GetRelation(Highway)
 Result['Separated'] = Route.GetSeparated(Check)
 Result['Missing'] = Route.GetMissing([Item['ID'] for _, Item in Check.items()])
 Result['Network'] = { Network[Bool]: Route.GetNetwork(Check, Bool) for Bool in [False, True] }
 Result['UID'] = Route.GetUID()
 Result['PBFDateTime'] = Route.GetDateTime()
 Result['DateTime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
 return Result

