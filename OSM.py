#https://josm.openstreetmap.de/wiki/Ru%3AHelp/RemoteControlCommands

import os
import sys
import random
import datetime

from loguru import logger
import osmapi

from OSMCacheIterator import CacheIterator


Classes = {
 'М': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:national', 'name': None, 'name:be': None, 'name:ru': None, },
 'Р': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:national', 'name': None, 'name:be': None, 'name:ru': None, },
 'Н': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:regional', 'name': None, 'name:be': None, 'name:ru': None, },
}


def Load(FileName):
 Result = {}
 for Line in open(FileName, mode="r", encoding="utf-8"):
  S = Line.strip().split(";")
  Tag, Desc = S[0], S[1]
  Result[Tag] = Desc
 return Result


def GetError(Class, Key, Value, Type, Tag):
 Result = []
 Result += CheckRef(Key)
 Result += CheckRelation(Type)
 Result += CheckTag(Tag, Class)
 Result += CheckClass(Tag, Class)
 Result += CheckBe(Tag)
 Result += CheckRu(Tag, Value)
 return Result


def GetRef(Tag):
 return Tag.get('official_ref', f"error-{random.randint(0, 9999)}")


def CheckRef(Key):
 Result = []
 if Key[:6] == "error-":
  Result.append(f"'official_ref' несапраўдны!")
 return Result


def CheckRelation(Type):
 Result = []
 if Type != "relation":
  Result.append(f"не 'relation'")
 return Result


def CheckTag(Tag, Class):
 Result = []
 for Key, Value in Classes[Class].items():
  if Key not in Tag:
   Result.append(f"'{Key}' не знойдзены")
  elif Value is not None:
   if Tag[Key] != Value:
    Result.append(f"у '{Key}' не зададзена '{Value}'")
 return Result
   

def CheckClass(Tag, Class):
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
  Result.append(f"'name:ru' не супадае з назвай у Законе")
 return Result



def GetErrorLine(Key, Relation):
 Result = {}
 Result['Key'] = Key
 Result['Color'] = "#ff9090"
 Tag = Relation['tag']
 Result['Type'] = Relation['type']
 Result['ID'] = Relation.get('id', None)
 Be = Tag.get('name', "")
 if Be:
  Result['Be'] = Be
 Ru = Tag.get('name:ru', "")
 if Ru:
  Result['Ru'] = Ru
 Result['Relation'] = ["'{ref}' адсутнічае ў Законе"]
 return Result


def GetLine(Class, Key, Value, Relations):
 Result = {}
 Result['Key'] = Key
 Relation = Relations.get(Key, {})
 if Relation:
  Type = Relation['type']
  Result['Type'] = Type
  Result['ID'] = Relation['id']
  Tag = Relation['tag']
  Be = Tag.get('name', "")
  if Be:
   Result['Be'] = Be
  Ru = Tag.get('name:ru', "")
  if Ru:
   Result['Ru'] = Ru
  Result['Error'] = GetError(Class, Key, Value, Type, Tag)
  Result['Color'] = "#ffc0c0" if Result['Error'] else "#bbffbb"
 else:
  Result['Color'] = "#d6e090"
  Result['Ru'] = Value
  Result['Relation'] = ["'relation' адсутнічае"]
 return Result




def ReadOSM(R):
 logger.info(f"Read Main Relation {R}")
 Result = {}
 #
 OSM = osmapi.OsmApi()
 Relation = OSM.RelationGet(R)
 for Type, Member in CacheIterator(OSM, 256, Relation['member']):
  logger.info(f"{Type.title()} {Member['id']}")
  Member['type'] = Type
  Ref = GetRef(Member['tag'])
  Result[Ref] = Member
 OSM.close()
 #
 return Result


def GetNotFound(Relation, CSV):
 return { i: Relation[i] for i in Relation.keys() - CSV.keys() }


def GetOSM(Class, ID, FileName):
 logger.info(f"Get Relation {Class}")
 Result = []
 Relations = ReadOSM(ID)
 #
 FileName = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", FileName)
 CSV = Load(FileName)
 #
 Result += [ GetLine(Class, Key, Value, Relations) for Key, Value in CSV.items() ] 
 Result += [ GetErrorLine(Key, Relation) for Key, Relation in GetNotFound(Relations, CSV).items()]
 return Result
