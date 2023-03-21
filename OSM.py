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


def GetError(Class, Key, Value, Type, Tag):
 Result = []
 Result += Check.Ref(Key)
 Result += Check.Relation(Type)
 Result += Check.Tag(Tag, Class)
 Result += Check.Class(Tag, Class)
 Result += Check.Be(Tag)
 Result += Check.Ru(Tag, Value)
 Result += Check.Abbr(Tag)
 Result += Check.OfficialName(Tag)
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
 Result['Relation'] += Check.Ref(Key)
 Result['Relation'] += ["'{ref}' адсутнічае ў Законе"]
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
  if Type != "relation":
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
