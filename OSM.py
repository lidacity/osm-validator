import os
import sys
import random
import datetime

from loguru import logger
import osmapi


def Load(FileName):
 Result = {}
 for Line in open(FileName, mode="r", encoding="utf-8"):
  S = Line.strip().split(";")
  Tag, Desc = S[0], S[1]
  Result[Tag] = Desc
 return Result


def GetError(Class, Key, Value, Tag):
 Result = []
 Result += CheckRef(Key)
 Result += CheckRelation(Tag)
 Result += CheckTag(Tag, {'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:regional', 'name': None, 'name:be': None, 'name:ru': None})
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


def CheckRelation(Tag):
 Result = []
 if Tag['type'] != "relation":
  Result.append(f"не 'relation'")
 return Result


def CheckTag(Tag, Names):
 Result = []
 for Key, Value in Names.items():
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
  if OfficialRef[:2] != "Н-":
   Result.append(f"'official_ref' не пачынаецца з '{Class}-'")
  if Ref[1:] != OfficialRef[2:]:
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



def GetNot(Relation, CSV):
 Result = {}
 for Key, Value in Relation.items():
  if Key not in CSV:
   Result[Key] = Value
 return Result


def GetErrorLine(Key, Relation):
 Result = {}
 Result['Key'] = Key
 Result['Color'] = "#ff9090"
 Tag = Relation['tag']
 Result['ID'] = Relation.get('id', None)
 Be = Tag.get('name', "")
 if Be:
  Result['Be'] = Be
 Ru = Tag.get('name:ru', "")
 if Ru:
  Result['Ru'] = Ru
 Result['Relation'] = ["'{ref}' адсутнічае ў Законе"]
 return Result


def GetLine(Class, Key, Value, Relation):
 Result = {}
 Result['Key'] = Key
 Tag = Relation.get('tag', {})
 if Tag:
  Result['ID'] = Relation.get('id', None)
  Be = Tag.get('name', "")
  if Be:
   Result['Be'] = Be
  Ru = Tag.get('name:ru', "")
  if Ru:
   Result['Ru'] = Ru
  Result['Error'] = GetError(Class, Key, Value, Tag)
  Result['Color'] = "#ffc0c0" if Result['Error'] else "#bbffbb"
 else:
  Result['Color'] = "#d6e090"
  Result['Ru'] = Value
  Result['Relation'] = ["'relation' адсутнічае"]
 return Result




def ReadOSM(R):
 logger.info(f"Read Main Relation {R}")
 Result = {}

 i = 1e10

 OSM = osmapi.OsmApi()
 Relation = OSM.RelationGet(R)
 for Member in Relation['member']:
  if Member['type'] == "relation":
   logger.info(f"Relation {Member['ref']}")
   Relation = OSM.RelationGet(Member['ref'])
   Relation['type'] = "relation"
   Ref = GetRef(Relation['tag'])
   Result[Ref] = Relation
  elif Member['type'] == "node":
   logger.error(f"Node {Member['ref']}")
   Node = OSM.NodeGet(Member['ref'])
   Node['type'] = "node"
   Ref = GetRef(Node['tag'])
   Result[Ref] = Node
  elif Member['type'] == "way":
   logger.error(f"Way {Member['ref']}")
   Way = OSM.WayGet(Member['ref'])
   Way['type'] = "way"
   Ref = GetRef(Way['tag'])
   Result[Ref] = Way


  if i == 0:
   break
  else:
   i -= 1

 OSM.close()
 return Result


def GetOSM(Class, Relations, FileName):
 logger.info(f"Get Relation {Class}")
 Result = []
 FileName = os.path.join("Base", FileName)
 CSV = Load(FileName)
 for Key, Value in CSV.items():
  Line = GetLine(Class, Key, Value, Relations.get(Key, {}))
  Result.append(Line)
 #
 for Key, Relation in GetNot(Relations, CSV).items():
  Line = GetErrorLine(Key, Relation)
  Result.append(Line)
 return Result
