#https://josm.openstreetmap.de/wiki/Ru%3AHelp/RemoteControlCommands

import os
import sys
import random
import datetime

from loguru import logger
import osmapi

from OSMCacheIterator import CacheIterator
import Check


def Load(FileName):
 Result = {}
 for Line in open(FileName, mode="r", encoding="utf-8"):
  S = Line.strip().split(";")
  Tag, Desc = S[0], S[1]
  Result[Tag] = Desc
 return Result


def GetRef(Tag):
 return Tag.get('official_ref', f"error-{random.randint(0, 9999)}")


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
 #
 Result['Relation'] = []
 Result['Relation'] += Check.GetRef(Key)
 Result['Relation'] += ["'{ref}' адсутнічае ў Законе"]
 return Result


def GetLine(OSM, Class, Key, Value, Relations):
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
  Result['Error'] = []
  Result['Error'] += Check.GetCheck(Class, Key, Value, Type, Tag)
  Result['Error'] += Check.GetCheckRef(Relation, Relations)
  Result['Error'] += Check.GetCheckOSM(OSM, Relation)
  Result['Color'] = "#ffc0c0" if Result['Error'] else "#bbffbb"
 else:
  Result['Color'] = "#d6e090"
  Result['Ru'] = Value
  Result['Relation'] = ["'relation' адсутнічае"]
 return Result




def ReadOSM(Class, R):
 logger.info(f"Read Main Relation {R}")
 Result, List = {}, {}
 #
 OSM = osmapi.OsmApi()
 Relation = OSM.RelationGet(R)
 for Type, Member in CacheIterator(OSM, 256, Relation['member']):
  if Type != "relation":
   logger.info(f"{Type.title()} {Member['id']}")
  Member['type'] = Type
  Member['class'] = Class
  Ref = GetRef(Member['tag'])
  Result[Ref] = Member
 OSM.close()
 #
 return Result


def GetNotFound(Class, Relation, CSV):
 Result = { i: Relation[i] for i in Relation.keys() - CSV.keys() }
 return { Key: Value for Key, Value in Result.items() if Value['class'] == Class }


def GetOSM(Class, Relations, FileName):
 logger.info(f"Get Relation {Class}")
 Result = []
 #
 FileName = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", FileName)
 CSV = Load(FileName)
 #
 OSM = osmapi.OsmApi()
 Result += [ GetLine(OSM, Class, Key, Value, Relations) for Key, Value in CSV.items() ] 
 OSM.close()
 Result += [ GetErrorLine(Key, Relation) for Key, Relation in GetNotFound(Class, Relations, CSV).items()]
 return Result
