#https://josm.openstreetmap.de/wiki/Ru%3AHelp/RemoteControlCommands

import os
import sys
import random
import datetime

from loguru import logger

from OsmApi import OsmApi, CacheIterator

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
 Result['Relation'] += Check.GetRef(Key)
 Result['Relation'] += Check.GetRelation(Type)
 Result['Relation'] += ["'{ref}' адсутнічае ў Законе"]
 return Result


def GetLine(Class, Key, Value, Relations):
 Result = {}
 Result['Key'] = Key
 Relation = Relations.get(Key, {})
 if Relation:
#  logger.info(f"parse relation {Relation['id']}")
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
  Result['Error'] = []
  Result['Error'] += Check.GetCheck(Class, Key, Value, Type, Tag)
  Result['Error'] += Check.GetCheckRef(Relation, Relations)
  Result['Error'] += Check.GetCheckOSM(Relation)
  Result['Color'] = "#ffc0c0" if Result['Error'] else "#bbffbb"
 else:
  Result['Color'] = "#d6e090"
  Result['Ru'] = Value
  Result['Relation'] = ["relation адсутнічае"]
 return Result


#


def ReadOSM(Class, R):
 logger.info(f"Read relation {R}")
 Result, List = {}, {}
 #
 OSM = OsmApi()
 Relation = OSM.ReadRelation(R)
 for Type, Member in CacheIterator(256, Relation['members']):
#  if Type != "relation":
#   logger.info(f"{Type.title()} {Member['id']}")
  Member['type'] = Type
  Member['class'] = Class
  Ref = GetRef(Member['tags'])
  Result[Ref] = Member
 OSM.Close()
 #
 return Result


def GetNotFound(Class, Relation, CSV):
 Result = { i: Relation[i] for i in Relation.keys() - CSV.keys() }
 return { Key: Value for Key, Value in Result.items() if Value['class'] == Class }


def GetOSM(Class, Relations, FileName):
 logger.info(f"Parse relation {Class}")
 Result = []
 #
 FileName = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", FileName)
 CSV = Load(FileName)
 #
 Result += [ GetLine(Class, Key, Value, Relations) for Key, Value in CSV.items() ] 
 Result += [ GetErrorLine(Key, Relation) for Key, Relation in GetNotFound(Class, Relations, CSV).items()]
 return Result
