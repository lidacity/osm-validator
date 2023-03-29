import re
from collections import Counter

from haversine import haversine
#from lingua import Language, LanguageDetectorBuilder

from OsmApi import CacheIterator, ArrayCacheIterator


#

Classes = {
 'М': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:national', 'name': None, 'name:be': None, 'name:ru': None, },
 'Р': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:national', 'name': None, 'name:be': None, 'name:ru': None, },
 'Н': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:regional', 'name': None, 'name:be': None, 'name:ru': None, },
}


def GetRef(Key):
 Result = []
 if Key[:6] == "error-":
  Result.append(f"несапраўдны 'official_ref'")
 return Result


def GetRelation(Type):
 Result = []
 if Type != "relation":
  Result.append(f"не relation")
 return Result


def GetTag(Tag, Class):
 Result = []
 for TagName, Value in Classes[Class].items():
  if TagName not in Tag:
   Result.append(f"не знойдзены '{TagName}'")
  elif Value is not None:
   if Tag[TagName] != Value:
    Result.append(f"'{TagName}' не роўны \"{Value}\"")
 return Result


def GetClass(Tag, Class):
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


def GetBe(Tag):
 Result = []
 Name = Tag.get('name', None)
 Be = Tag.get('name:be', None)
 if Name != Be:
  Result.append(f"'name:be' не роўны 'name'")
 return Result


def GetRu(Tag, Name):
 Result = []
 Ru = Tag.get('name:ru', "")
 if Name[:254] != Ru[:254]:
  Result.append(f"'name:ru' не супадае з Законам")
 return Result


Abbreviations = re.compile("|".join([re.escape(s) for s in ["’", "—", "а/д", "г.п.", "г.", "аг.", "п.", "д.", "х.", "ж/д", "ст.", "с/т", "с/с", "хоз.", "Ж/д", "А/д", "С/т", "Ст.", "обл.", "Гр.", "р-на", "вул.", "ул.", ]])).search


def GetAbbr(Tag):
 Result = []
 for TagName in ['name:be', 'name:ru']:
  Name = Tag.get(TagName, "")
  Abbr = Abbreviations(Name)
  if Abbr:
   Result.append(f"у '{TagName}' недапушчальны скарот \"{Abbr[0]}\"")
   break
 return Result


def GetOfficialName(Tag):
 Result = []
 for TagName in ['official_name', 'official_name:be', 'official_name:ru', 'description', 'description:be', 'description:ru']:
  if TagName in Tag:
   Result.append(f"непатрэбны '{TagName}'")
 if 'fixme' in Tag:
  Result.append(f"'fixme' у relation")
 return Result


Letter = {
 'Latin': { 're': re.compile("[a-zA-Z]").search, 'Desc': "лацінскія літары" },
 'Number': { 're': re.compile("[a-zA-Zа-яА-ЯёЁ][0-9]|[0-9][a-zA-Zа-яА-ЯёЁ]").search, 'Desc': "лацінскія літары" },
 'Hyphen': { 're': re.compile("[^ ]–|–[^ …]|[ ]-|-[ ]").search, 'Desc': "неправільны злучок" },
 'Bracket': { 're': re.compile("[^ \"(]\(|\)[^ …\")]").search, 'Desc': "неправільныя дужкі" },
 'Special': { 're': re.compile("|".join(map(re.escape, ".:;!_*+#¤%&[]{}$@^\\"))).search, 'Desc': "спецыяльныя знакі" },
}


Replace = { 'SOS': "СОС", 'III': "3", 'II': "2", 'I': "1", }


def GetLetter(Tag):
 Result = []
 for TagName in ['name:be', 'name:ru']:
  if TagName in Tag:
   S = Tag[TagName]
   for Key, Value in Replace.items():
    S = S.replace(Key, Value)
   for _, Value in Letter.items():
    R = Value['re'](S)
    if R:
     Result.append(f"у '{TagName}' {Value['Desc']} \"{R[0]}\"")
     break
 return Result


def GetLength(Tag):
 Result = []
 Be = len(Tag.get('name:be', ""))
 Ru = len(Tag.get('name:ru', ""))
 if abs(Be - Ru) > 12:
  Result.append(f"розніца паміж даўжынёй 'name:be' і 'name:ru'")
 return Result


#https://vl2d.livejournal.com/21053.html
#https://yadro-servis.ru/blog/nevosmosnoe-sochetanie-bukv/ 
Impossible = {
 'name:ru': re.compile("|".join(["ёя", "ёь", "ёэ", "ъж", "эё", "ъд", "цё", "уь", "щч", "чй", "шй", "шз", "ыф", "жщ", "жш", "ыъ", "ыэ", "ыю", "ыь", "жй", "ыы", "жъ", "жы", "ъш", "пй", "ъщ", "зщ", "ъч", "ъц", "ъу", "ъф", "ъх", "ъъ", "ъы", "ыо", "жя", "зй", "ъь", "ъэ", "ыа", "нй", "еь", "цй", "ьй", "ьл", "ьр", "пъ", "еы", "еъ", "ьа", "шъ", "ёы", "ёъ", "ът", "щс", "оь", "къ", "оы", "щх", "щщ", "щъ", "щц", "кй", "оъ", "цщ", "лъ", "мй", "шщ", "ць", "цъ", "щй", "йь", "ъг", "иъ", "ъб", "ъв", "ъи", "ъй", "ъп", "ър", "ъс", "ъо", "ън", "ък", "ъл", "ъм", "иы", "иь", "йу", "щэ", "йы", "йъ", "щы", "щю", "щя", "ъа", "мъ", "йй", "йж", "ьу", "гй", "эъ", "уъ", "аь", "чъ", "хй", "тй", "чщ", "ръ", "юъ", "фъ", "уы", "аъ", "юь", "аы", "юы", "эь", "эы", "бй", "яь", "ьы", "ьь", "ьъ", "яъ", "яы", "хщ", "дй", "фй", ])).search,
 'name:be': re.compile("|".join(["и", "щ", "ъ", "ї", "жі", "же", "жё", "жя", "жю", "рі", "ре", "рё", "ря", "рю", "чі", "че", "чё", "чя", "чю", "ші", "ше", "шё", "шя", "шю", "ді", "де", "дё", "дя", "дю", "ті", "те", "тё", "тя", "тю", "еу", "ыу", "ау", "оу", "эу", "яу", "іу", "юу", "ёу", "уу", "еь", "ыь", "аь", "оь", "эь", "яь", "іь", "юь", "ёь", "уь", "ўь", "йь", "йў", "цў", "кў", "нў", "гў", "шў", "ўў", "зў", "хў", "фў", "вў", "пў", "рў", "лў", "дў", "жў", "чў", "сў", "мў", "тў", "ьў", "бў", "йй", "цй", "кй", "нй", "гй", "шй", "ўй", "зй", "хй", "фй", "вй", "пй", "рй", "лй", "дй", "жй", "чй", "сй", "мй", "тй", "ьй", "бй", "жш", "ыэ", "ыы", "ыо", "ьр", "ьа", "ёы", "оы", "йу", "йы", "йж", "ьу", "гй", "уы", "юь", "аы", "юы", "эы", "ьы", "ьь", "яы", ])).search,
}


def GetImpossible(Tag):
 Result = []
 for TagName in ['name:ru', 'name:be']:
  if TagName in Tag:
   Line = Tag[TagName].lower()
   Imp = Impossible[TagName](Line)
   if Imp:
    Result.append(f"у '{TagName}' немагчымае спалучэнне \"{Imp[0]}\"")
    break
 return Result


#Languages = [Language.RUSSIAN, Language.BELARUSIAN] #Language.ENGLISH
#Detector = LanguageDetectorBuilder.from_languages(*Languages).build()

#def GetLanguage(Tag):
# Result = []
# global Detector
## for language, value in Detector.compute_language_confidence_values(Line):
##  print(f"{language.name}: {value:.2f}")
## print(Detector.detect_language_of(Line))
## sys.exit(0)
# for TagName in ['name:ru']:
#  if TagName in Tag:
#   if Detector.detect_language_of(Tag[TagName]) != Language.RUSSIAN:
#    Result.append(f"у '{TagName}' мова не руская")
#    break
# for TagName in ['name', 'name:be']:
#  if TagName in Tag:
#   if Detector.detect_language_of(Tag[TagName]) != Language.BELARUSIAN:
#    Result.append(f"у '{TagName}' мова не беларуская")
#    break
# return Result


#


Refs = { 'ok': re.compile("[МР]-[0-9]+/[ЕП] [0-9]+|[МРН]-[0-9]+"), 'bad': re.compile("[МРН][0-9]+"), }


def GetList(Name, Type):
 return re.findall(Refs[Type], Name)


def GetIndex(Name, Ref):
 return [Index.start() for Index in re.finditer(Ref, Name)]


def ExcludeRef(Name, Index):
 return Name[Index-1:].strip()[:1] in ["(", ")", ""]


def GetBadRefInRelation(Relation, Relations):
 Result = []
 Tag = Relation['tags']
 for TagName in ['name:be', 'name:ru']:
  if TagName in Tag:
   if GetList(Tag[TagName], 'bad'):
    Result.append(f"у '{TagName}' не вызначаны 'ref'")
 return Result


def GetRefInRelation(Relation, Relations):
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


#


def GetWays(Relation, Exclude=[]):
 Result = []
 for Type, Member in CacheIterator(256, Relation['members'], Type=["way"], Role=Exclude):
  Result.append(Member)
 return Result


def GetLimits(Ways):
 return [ [Way['nodes'][0], Way['nodes'][-1]] for Way in Ways ]


def GetNodes(Ways):
 return [ [Node for Node in Way['nodes']] for Way in Ways ]


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
 return Result


def GetCoord(Ways):
 Nodes = IslandLine(Ways)
 Array = [Item for Row in Nodes for Item in Row]
 Result = { Item['id']: (Item['lat'], Item['lon']) for Item in ArrayCacheIterator(256, Array, "node") }
 return [ [ Result[ID] for ID in Row ] for Row in Nodes ]


#


def GetCheckWays(Relation):
 Result = []
 for Member in Relation['members']:
  if Member['type'] != "way":
   Result.append(f"у relation прысутнічае ня толькі way")
   break
 return Result


def GetCheckFixme(Ways):
 Result = []
 for Way in Ways:
  if "fixme" in Way['tags']:
   Result.append(f"'fixme' у way")
   break
 return Result


def GetCheckHighway(Ways):
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


def GetCheckDouble(Ways):
 Result = []
 c = Counter([Way['id'] for Way in Ways])
 if max(c.values()) > 1:
  Result.append(f"падвоеныя way")
 return Result


def GetCheckTagsInWay(Tag, Ways):
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


def GetCheckCross(Ways):
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


def GetIsland(Ways):
 Result = []
 if Island(Ways) != IslandLine(Ways):
  Result.append(f"way не паслядоўныя")
 return Result


def GetHaversine(Ways):
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
   Result.append(f"разарваная дарога")
 return Result


#


def GetCheck(Class, Key, Value, Type, Tag):
 Result = []
 Result += GetRef(Key)
 Result += GetRelation(Type)
 Result += GetTag(Tag, Class)
 Result += GetClass(Tag, Class)
 Result += GetBe(Tag)
 Result += GetRu(Tag, Value)
 Result += GetAbbr(Tag)
 Result += GetOfficialName(Tag)
 Result += GetLetter(Tag)
 Result += GetLength(Tag)
 Result += GetImpossible(Tag)
# Result += GetLanguage(Tag)
 return Result


def GetCheckRef(Relation, Relations):
 Result = []
 Result += GetBadRefInRelation(Relation, Relations)
 Result += GetRefInRelation(Relation, Relations)
 return Result


def GetCheckOSM(Relation):
 Result = []
 Ways = GetWays(Relation)
 Result += GetCheckWays(Relation)
 Result += GetCheckFixme(Ways)
 Result += GetCheckHighway(Ways)
 Result += GetCheckDouble(Ways)
 #
 Ways = GetWays(Relation, Exclude=["link"])
 Result += GetCheckTagsInWay(Relation['tags'], Ways)
 Result += GetCheckCross(Ways)
 Result += GetIsland(Ways)
 Result += GetHaversine(Ways)
 return Result
