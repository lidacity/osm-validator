#!.venv/bin/python

#http://download.geofabrik.de/europe/belarus.html
#http://osmosis.svimik.com/latest/
#http://osm.sbin.ru/osm_dump/

import os
import sys
from datetime import datetime

import requests
from dateutil.parser import parse as parsedate
from loguru import logger
from osmiter import iter_from_osm

from Jinja import Generate


sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')



URL = "https://download.geofabrik.de/europe/belarus-latest.osm.pbf"
#URL = "http://osmosis.svimik.com/latest/BY.osm.pbf"
Path = os.path.dirname(os.path.abspath(__file__))
FileName = os.path.join(Path, ".data", "belarus-latest.osm.pbf")


def Download(URL, FileName):
 logger.info(f"Check {FileName}")
 UserAgent = {"User-agent": "https://osm-validator.lidacity.by/"}
 Requests = requests.head(URL, headers=UserAgent)
 #print(Requests.headers)
 DateTimeURL = parsedate(Requests.headers['Last-Modified'])
 #
 if os.path.isfile(FileName):
  IsDownload = datetime.fromtimestamp(os.path.getmtime(FileName)).astimezone() < DateTimeURL
  if IsDownload:
   os.remove(FileName)
 else:
  IsDownload = True
 #
 if IsDownload:
  logger.info(f"Download {URL}")
  Requests = requests.get(URL, headers=UserAgent)
  with open(FileName, 'wb') as File:
   for Buffer in Requests.iter_content(4096):
    File.write(Buffer)
  logger.info(f"Downloaded {URL}; size = {Requests.headers['Content-Length']}")
 else:
  logger.info(f"Skip download {URL}")
 Requests.close()


def GetList(Relation):
 for Member in Relation['member']:
  yield Member['ref']


def GetRef(Tag):
 Result = Tag.get('ref', "невядома")
 if Result[0:1] in "МРН" and Result[1:2] in "0123456789":
  if Result[0:1] == "М":
   return Result.replace("М", "М-").replace("/П", "/П ").replace("/Е", "/Е ").replace("  ", " ")
  elif Result[0:1] == "Р":
   return Result.replace("Р", "Р-").replace("/П", "/П ").replace("/Е", "/Е ").replace("  ", " ")
  elif Result[0:1] == "Н":
   return Result.replace("Н", "Н-")
  else:
   return None


def GetOfficialRef(Tag):
 return Tag.get('official_ref', "невядома")


def GetNames(Tag, Lang):
 Names = ";".join([Tag.get(f'name:{Lang}', ""), Tag.get(f'alt_name:{Lang}', "")])
 return [Name.strip() for Name in Names.split(";") if Name]


def Load(FileName):
 logger.info("Load PBF")
 Ways, Relations, RelationIDs = [], [], []
 Place = {}
 for Feature in iter_from_osm(FileName):
  Tag = Feature.get('tag', {})
  if Feature['type'] == "node":
   if Tag.get('place', "") in ["city", "town", "village", "hamlet", "neighbourhood", "locality"]:
    Bes, Rus = GetNames(Tag, 'be'), GetNames(Tag, 'ru')
    if Bes and Rus:
     for Ru in Rus:
      if Ru in Place:
       for Be in Bes:
        Place[Ru].add(Be)
      else:
       Place[Ru] = set(Bes)
  #
  if Feature['type'] == "way":
   if ('highway' in Tag or 'ferry' in Tag) and 'ref' in Tag:
    Ways.append(Feature)
  #
  if Feature['type'] == "relation":
   if Feature['id'] in [1246287, 1246288, 1246286]:
    RelationIDs += list(GetList(Feature))
   if Tag.get('type', "") == "route" and Tag.get('route', "") == "road" and Tag.get('network', "") in ["by:national", "by:regional"]:
    Relations.append(Feature)
 return Ways, Relations, RelationIDs, Place


def GetMissingRelation(Relations, RelationIDs):
 logger.info("Parse relation")
 Result, WayIDs, Ok = [], [], {}
 for Relation in Relations:
  ID = Relation['id']
  Tag = Relation['tag']
  Item = {'ID': ID, 'Key': Tag.get('ref', ""), 'Be': Tag.get('name:be', ""), 'Ru': Tag.get('name:ru', "")}
  if ID in RelationIDs:
   WayIDs += list(GetList(Relation))
   Ref = GetOfficialRef(Tag)
   Ok[Ref] = Item
  else:
   Result.append(Item)
 return Result, WayIDs, Ok


def GetMissingWay(Ways, WayIDs):
 logger.info("Parse way")
 Result = {}
 for Way in Ways:
  ID = Way['id']
  if ID not in WayIDs:
   Ref = GetRef(Way['tag'])
   if Ref:
    if Ref in Result:
     Result[Ref].append(ID)
    else:
     Result[Ref] = [ID]
 return Result


def GetRelation(Ways, Ok):
 logger.info("Parse relation for ways")
 Result = {}
 for Ref, _ in Ways.items():
  if Ref not in Result:
   if Ref in Ok.keys():
    Result[Ref] = Ok[Ref]
 return Result



def CheckPBF():
 Result = {}
 Download(URL, FileName)
 Ways, Relations, RelationIDs, Place = Load(FileName)
 ResultRelation, WayIDs, OkRelation = GetMissingRelation(Relations, RelationIDs)
 Result['Relations'] = ResultRelation
 Result['Ways'] = GetMissingWay(Ways, WayIDs)
 Result['RelationsForWays'] = GetRelation(Result['Ways'], OkRelation)
 return Result, Place



if __name__ == "__main__":
 logger.add(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".log", "osm.log"))
 logger.info("Start PBF")
 PBF, Place = CheckPBF()
 #print(PBF)
 #print(Place)
 Context = {}
 Context['Missing'] = PBF
 Generate("missing.html", Context)
 logger.info("Done PBF")
