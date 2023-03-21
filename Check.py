import re

import osmapi

from OSMCacheIterator import CacheIterator


#

Classes = {
 'М': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:national', 'name': None, 'name:be': None, 'name:ru': None, },
 'Р': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:national', 'name': None, 'name:be': None, 'name:ru': None, },
 'Н': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:regional', 'name': None, 'name:be': None, 'name:ru': None, },
}


def GetRef(Key):
 Result = []
 if Key[:6] == "error-":
  Result.append(f"'official_ref' несапраўдны!")
 return Result


def GetRelation(Type):
 Result = []
 if Type != "relation":
  Result.append(f"не 'relation'")
 return Result


def GetTag(Tag, Class):
 Result = []
 for Key, Value in Classes[Class].items():
  if Key not in Tag:
   Result.append(f"'{Key}' не знойдзены")
  elif Value is not None:
   if Tag[Key] != Value:
    Result.append(f"у '{Key}' не зададзена '{Value}'")
 return Result
   

def GetClass(Tag, Class):
 Result = []
 Ref, OfficialRef = Tag.get('ref', ""), Tag.get('official_ref', "")
 if Ref and OfficialRef:
  if Ref[0] != Class:
   Result.append(f"'ref' не пачынаецца з '{Class}'")
  if OfficialRef[:2] != f"{Class}-":
   Result.append(f"'official_ref' не пачынаецца з '{Class}-'")
  if Ref[1:] != OfficialRef[2:2+len(Ref[1:])]:
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
  Result.append(f"'name:ru' не супадае з назвай у Законе")
 return Result


def GetAbbr(Tag):
 Result = []
 for N in [ 'name', 'name:be', 'name:ru' ]:
  Name = Tag.get(N, "")
  Abbreviations = ["’", "—", "а/д", "г.п.", "г.", "аг.", "п.", "д.", "х.", "ж/д", "ст.", "с/т", "с/с", "хоз.", "Ж/д", "А/д", "С/т", "Ст.", "обл.", "Гр.", "р-на", ]
  for A in Abbreviations:
   if A in Name:
    Result.append(f"недапушчальны скарот у '{N}'")
    break
 return Result


def GetOfficialName(Tag):
 Result = []
 if 'official_name' in Tag:
  Result.append(f"прысутнічае непатрэбны 'official_name'")
 if 'official_name:be' in Tag:
  Result.append(f"прысутнічае непатрэбны 'official_name:be'")
 if 'official_name:ru' in Tag:
  Result.append(f"прысутнічае непатрэбны 'official_name:ru'")
 if 'description' in Tag:
  Result.append(f"прысутнічае непатрэбны 'description'")
 if 'description:be' in Tag:
  Result.append(f"прысутнічае непатрэбны 'description:be'")
 if 'description:ru' in Tag:
  Result.append(f"прысутнічае непатрэбны 'description:ru'")
 if 'fixme' in Tag:
  Result.append(f"прысутнічае 'fixme' у relation")
 return Result


#


ReRefs2 = { 'ok': re.compile("[МР]-[0-9]+/[ЕП] [0-9]+|[МРН]-[0-9]+"), 'bad': re.compile("[МРН][0-9]+"), }


def GetList(Name, Type):
 return re.findall(ReRefs2[Type], Name)


def GetIndex(S, Ref):
 return [m.start() for m in re.finditer(Ref, S)]


def ExcludeRef(Name, Index):
 return Name[Index-1:].strip()[:1] in ["(", ")", ""]


def GetBadRefInRelation(Relation, Relations):
 Result = []
 Tag = Relation['tag']
 for Name in [ 'name', 'name:be', 'name:ru' ]:
  if Name in Tag:
   if GetList(Tag[Name], 'bad'):
    Result.append(f"Не вызначаны 'ref' у апісанні {Name}")
 return Result


def GetRefInRelation(Relation, Relations):
 Result = []
 Tag = Relation['tag']
 for Name in [ 'name', 'name:be', 'name:ru' ]:
  if Name in Tag:
   for Ref in GetList(Tag[Name], 'ok'):
    if Ref in Relations:
     for Index in GetIndex(Tag[Name], Ref):
      Tag2 = Relations[Ref]['tag']
      if Name in Tag2:
       I = Index + len(Ref) + 1
       S2 = Tag2[Name]
       S = Tag[Name][I:I+len(S2)]
       if S2 != S and not ExcludeRef(Tag[Name], I):
        Result.append(f"апісанне {Ref} не адпавядае свайму апісанню ў '{Name}'")
    else:
     Result.append(f"не вызначаны {Ref} у апісанні '{Name}'")
 return Result


#


def GetWays(OSM, Relation, Exclude=[]):
 List = [ Item['ref'] for Item in Relation['member'] if Item['type'] == "way" and Item['role'] not in Exclude ]
 Result = {}
 for Type, Member in CacheIterator(OSM, 256, Relation['member'], Exclude=Exclude):
  if Type == "way":
   Result[Member['id']] = Member
 return { Key: Result[Key] for Key in List}


def GetLimits(Ways):
 return [ [Value['nd'][0], Value['nd'][-1]] for Key, Value in Ways.items() ]


def GetPoints(Ways):
 return [ [Item for Item in Value['nd']] for Key, Value in Ways.items() ]


#


def GetCheckWays(Relation):
 Result = []
 for Item in Relation['member']:
  if Item['type'] != "way":
   Result.append(f"у relation прысутнічае ня толькі way")
   break
 return Result


def GetCheckFixme(Ways):
 Result = []
 for _, Way in Ways.items():
  if "fixme" in Way['tag']:
   Result.append(f"прысутнічае 'fixme' у way")
   break
 return Result


def GetCheckHighway(Ways):
 Result = []
 Highways = [ "motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential", "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link" ]
 for _, Way in Ways.items():
  Tag = Way['tag']
  if 'highway' in Tag:
   if Tag['highway'] not in Highways:
    Result.append(f"памылковы тып 'highway'={Tag['highway']} на way")
    break
  else:
   Result.append(f"пусты тып highway на way")
   break
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
 return Result


def GetCheckRef(Relation, Relations):
 Result = []
 Result += GetBadRefInRelation(Relation, Relations)
 Result += GetRefInRelation(Relation, Relations)
 return Result


def GetCheckOSM(OSM, Relation):
 Result = []
 Ways = GetWays(OSM, Relation)
 Result += GetCheckWays(Relation)
 Result += GetCheckFixme(Ways)
 Result += GetCheckHighway(Ways)

 return Result
