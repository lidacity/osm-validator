import os
import random
from datetime import datetime
from collections import Counter

import re
re._MAXCACHE = 4096

from loguru import logger
from haversine import haversine

from Validator import Validator



class RouteBusValidator(Validator):

 VehicleTypes = {
  '': [ {'Be': "", 'Ru': ""}, ],
  'bus': [ {'Be': "Аўтобус", 'Ru': "Aвтобус"}, {'Be': "Прыгарадны аўтобус", 'Ru': "Пригородный автобус"}, {'Be': "Міжгародні аўтобус", 'Ru': "Междугородный автобус"}, ],
  'tram': [ {'Be': "Трамвай", 'Ru': "Трамвай"}, ],
  'subway': [ {'Be': "Метро", 'Ru': "Метро"}, ],
  'train': [ {'Be': "Цягнік", 'Ru': "Поезд"}, {'Be': "Хуткасны цягнік", 'Ru': "Скорый поезд"}, {'Be': "Пасажырскі цягнік", 'Ru': "Пассажирский поезд"}, {'Be': "Прыгарадны дызельцягнік", 'Ru': "Пригородный дизельпоезд"}, {'Be': "Электрацягнік", 'Ru': "Электропоезд"}, {'Be': "Хуткасны электрацягнік", 'Ru': "Скоростной электропоезд"}, {'Be': "Прыгарадны электрацягнік", 'Ru': "Пригородный электропоезд"}, {'Be': "Скоры фірмовы цягнік", 'Ru': "Скорый фирменный поезд"}, ],
  'trolleybus': [ {'Be': "Тралейбус", 'Ru': "Тролейбус"}, ],
 }

 TrainTypes = [
  {'Be': "Міжнародныя лініі", 'Ru': "Международные линии"},
  {'Be': "Міжрэгіянальныя лініі бізнес-класа", 'Ru': "Межрегиональные линии бизнес-класса"}, # Электропоезд серии ЭП-М
  {'Be': "Міжрэгіянальныя лініі эканомкласа", 'Ru': "Межрегиональные линии экономкласса"},
  {'Be': "Рэгіянальныя лініі бізнес-класа", 'Ru': "Региональные линии бизнес-класса"}, # Электропоезд серии ЭП-Р, Дизель-поезд серии ДП1
  {'Be': "Рэгіянальныя лініі эканомкласа", 'Ru': "Региональные линии экономкласса"},
  {'Be': "Гарадскія лініі", 'Ru': "Городские линии"}, # Электропоезд серии ЭП-Г
 ]

 #direction': None
 AllRoutes = {
  'bus': {'type': "route", 'route': "bus", 'public_transport:version': "2", 'name': None, 'name:be': None, 'name:ru': None, 'from': None, 'to': None, },
  'train': {'type': "route", 'route': "train", 'public_transport:version': "2", 'name': None, 'name:be': None, 'name:ru': None, 'from': None, 'to': None, },
  'subway': {'type': "route", 'route': "subway", 'public_transport:version': "2", 'name': None, 'name:be': None, 'name:ru': None, 'from': None, 'to': None, },
  'tram': {'type': "route", 'route': "tram", 'public_transport:version': "2", 'name': None, 'name:be': None, 'name:ru': None, 'from': None, 'to': None, },
  'trolleybus': {'type': "route", 'route': "trolleybus", 'public_transport:version': "2", 'name': None, 'name:be': None, 'name:ru': None, 'from': None, 'to': None, },
 }

 AllMasters = {
  'bus': { 'type': "route_master", 'route_master': 'bus', 'ref': None, 'name': None, 'name:be': None, 'name:ru': None, },
  'train': { 'type': "route_master", 'route_master': 'train', 'ref': None, 'name': None, 'name:be': None, 'name:ru': None, },
  'subway': { 'type': "route_master", 'route_master': 'subway', 'ref': None, 'name': None, 'name:be': None, 'name:ru': None, },
  'tram': { 'type': "route_master", 'route_master': 'tram', 'ref': None, 'name': None, 'name:be': None, 'name:ru': None, },
  'trolleybus': { 'type': "route_master", 'route_master': 'trolleybus', 'ref': None, 'name': None, 'name:be': None, 'name:ru': None, },
 }

 AllowHighways = {
  'railway': ["subway", "tram", "rail", ],
  'highway': ["motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential", "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link", "track", "service", ],
 }

 Wrong = {
  'Latin': {'re': re.compile("[a-zA-Z]").search, 'Desc': "лацінскія літары"},
  'Number': {'re': re.compile("[a-zA-Zа-яА-ЯёЁўЎіІʼ][0-9]").search, 'Desc': "няправільныя лічбы"},
  'Hyphen': {'re': re.compile("[^ ]–|–[^ …]|[ ]-|-[ ]").search, 'Desc': "неправільны злучок"},
  'Bracket': {'re': re.compile("[^ «(]\(|\)[^ …»)]").search, 'Desc': "неправільныя дужкі"},
  'Special': {'re': re.compile("|".join(map(re.escape, ".;!_*+#¤%&[]{}$@^\\'’—"))).search, 'Desc': "спецыяльныя знакі"},
  'Abbreviations': {'re': re.compile("|".join([re.escape(s) for s in ["а/д", "г.п.", "г.", "аг.", "п.", "д.", "х.", "ж/д", "ст.", "с/т", "с/с", "хоз.", "Ж/д", "А/д", "С/т", "Ст.", "обл.", "Гр.", "р-на", "вул.", "ул.", ]])).search, 'Desc': "недапушчальны скарот"},
 }                                                   

 Role = {
  'node': ["stop", "platform", "stop_entry_only", "platform_entry_only", "stop_exit_only", "platform_exit_only", ],
  'way': ["", "platform", "platform_entry_only", "platform_exit_only", ],
  'relation': [],
 }


 def NormalizeWays(self, Ways):
  Result = []
  for Way in Ways:
   if Way['nodes']:
    Result.append(Way)
  return Result


 def NormalizeNodes(self, Nodes):
  Result = []
  for Node in Nodes:
   if Node['type'] == "node":
    if Node['lat'] != 0 and Node['lon'] != 0 and Node['uid'] != 0:
     Result.append(Node)
  return Result


 def ConvertPlatform(self, Ways):
  Result = []
  if Ways:
   for Way in Ways:
    Nodes = self.ReadNodes(Way['nodes'])
    Lat, Lon = 0, 0
    for Node in Nodes:
     Lat += Node['lat']
     Lon += Node['lon']
    Lat /= len(Nodes)
    Lon /= len(Nodes)
    Node = {'type': "node", 'id': -1, 'lat': Lat, 'lon': Lon, 'uid': 0, 'tags': Way['tags'] }
    Result.append(Node)
  return Result


 def CheckStop(self, Ways, Stops):
  Result = []
  #
  IDStops = [Stop['id'] for Stop in Stops]
  #
  IDNodes = []
  for Way in Ways:
   Nodes = Way['nodes']
   if IDNodes:
    if IDNodes[-1] == Nodes[-1]:
     IDNodes += list(reversed(Nodes))
    else:
     IDNodes += Nodes
   else:
    if IDStops:
     if IDStops[0] == Nodes[0]:
      IDNodes += Nodes
     else:
      IDNodes += list(reversed(Nodes))
    else:
     IDNodes += Nodes
  #
  if not IDNodes:
   Result.append(f"маршрут адсутнічае")
  if not IDStops:
   Result.append(f"прыпынкі адсутнічаюць")
  #
  for ID in IDStops:
   if ID not in IDNodes:
    Result.append(f"прыпынак не належыць маршруту")
  #
  if IDStops:
   for ID in IDNodes:
    if ID == IDStops[0]:
     IDStops.pop(0)
     if len(IDStops) == 0:
      break
  if len(IDStops) > 0:
   Result.append(f"прыпынкі ідуць не паслядоўна")
  #
  return Result


 def CheckPlatform(self, Stops, Platforms):
  Result = []
  #
  if not Platforms:
   Result.append(f"платформы адсутнічаюць")
  else:
   if len(Stops) != len(Platforms):
    Result.append(f"не супадае колькасць: {len(Stops)} прыпынкаў і {len(Platforms)} платформаў")
   else:
    for Stop, Platform in zip(Stops, Platforms):
     CoordStop = (Stop['lat'], Stop['lon'])
     CoordPlatform = (Platform['lat'], Platform['lon'])
     Length = haversine(CoordStop, CoordPlatform)
     if Length > 0.05:
      Name = Stop['tags'].get('name:be', Platform['tags'].get('name:be', "?"))
      Result.append(f"прыпынак далёка ад платформы: {round(Length * 1000, 1)} м (\"{Name}\")")
  #
  return Result


 def CheckNodeStop(self, Stops, Class):
  Result = []
  Classes = { 'public_transport': "stop_position", Class: "yes", }
  #
  for Stop in Stops:
   Tag = Stop['tags']
   Name = Tag.get('name:be', "?")
   Result += self.CheckTag(Tag, Classes, Note=f"прыпынак \"{Name}\": ")
  #
  return Result


 def CheckNodePlatform(self, Platforms):
  Result = []
  ClassesPlatform = { 'public_transport': "platform", }
  ClassesStation = { 'public_transport': "station", 'name': None, 'name:be': None, 'name:ru': None, }
  #
  for Platform in Platforms:
   Tag = Platform['tags']
   Name = Tag.get('name:be', "?")
   ResultStation = self.CheckTag(Tag, ClassesStation, Note=f"станцыя \"{Name}\": ")
   if ResultStation:
    ResultPlatform = self.CheckTag(Tag, ClassesPlatform, Note=f"платформа \"{Name}\": ")
    if ResultPlatform:
     Result += ResultPlatform
  #
  return Result


 def CheckStopArea(self, Stops, Platforms):
  Result = []
  Classes = { 'type': "public_transport", 'public_transport': "stop_area", 'name': None, 'name:be': None, 'name:ru': None, }
  Role = {
   'stop': { 'public_transport': "stop_position" },
   'platform': { 'public_transport': "platform" },
   '': {'public_transport': "station", 'amenity': None },
  }
  #
  return Result


 def CheckRouteRole(self, Members):
  Result = []
  #
  for Member in Members:
   Type = Member['type']
   ID = Member['ref']
   if Member['role'] in ["stop", "stop_exit_only", "stop_entry_only"]:
    if Type == "node":
     Node = self.ReadNode(ID)
     Tag = Node['tags']
     if Tag:
      if Tag.get('public_transport', "") != "stop_position":
       Result.append(f"role прыпынку не 'public_transport' = \"stop_position\"")
    else:
     Result.append(f"прыпынак не 'node'")
   #
   elif Member['role'] in ["platform", "platform_exit_only", "platform_entry_only"]:
    if Type in ["node", "way"]:
     if Type == "node":
      Node = self.ReadNode(ID)
     if Type == "way":
      Node = self.ReadWay(ID)
     Tag = Node['tags']
     if Tag:
      if Tag.get('public_transport', "") != "platform":
       Result.append(f"role платформы не 'public_transport' = \"platform\"")
    else:
     Result.append(f"прыпынак не 'node' ці 'way'")
   #
   elif Member['role'] == "":
    if Type != "way":
     Result.append(f"role маршруту не 'way'")
   #
   else:
     Result.append(f"невядомы role")
  #
  return Result


 def CheckRoute(self, Tag, Routes, Class, Note):
  Result = []
  if Class in Routes:
   Result += self.CheckTag(Tag, Routes[Class], Note=f"{Note}: ")
  else:
   Result.append(f"незразумелы {Note}")
  return Result


 #https://wiki.openstreetmap.org/w/index.php?title=Proposed_features/Public_Transport&oldid=625726#Route
 def CheckNameRoute(self, Tag, Class):
  Result = []
  ResultBe = ""
  #
  if Class in self.VehicleTypes:
   VehicleTypes = self.VehicleTypes[Class]
   ReferenceNumber = Tag.get('ref', "")
   InitialStop = Tag.get('from', "?")
   TerminalStop = Tag.get('to', "?")
   #
   if not ReferenceNumber and not InitialStop and not TerminalStop:
    for VehicleType in reversed(VehicleTypes):
     NameBe = f"{VehicleType['Be']} №{ReferenceNumber}: {InitialStop} => {TerminalStop}"
     if Tag.get('name:be', "") == NameBe:
      break
     else:
      Result.append(f"назва 'name:be' маршруту не \"{NameBe}\"")
    #
    if ResultBe:
     Result.append(ResultBe)
   #
  else:
    Result.append(f"незразумелая назва маршруту")
  #
  return Result


 def CheckNameMaster(self, Tag, Class):
  Result = []
  ResultBe = ""
  ResultRu = ""
  #
  if Class in self.VehicleTypes:
   VehicleTypes = self.VehicleTypes[Class]
   ReferenceNumber = Tag.get('ref', "?")
   #
   for VehicleType in reversed(VehicleTypes):
    NameBe = f"{VehicleType['Be']} №{ReferenceNumber}"
    if Tag.get('name:be', "") == NameBe:
     break
    else:
     ResultBe = f"назва 'name:be' майстар-маршруту не \"{NameBe}\""
   #
   for VehicleType in reversed(VehicleTypes):
    NameRu = f"{VehicleType['Ru']} №{ReferenceNumber}"
    if Tag.get('name:ru', "") == NameRu:
     break
    else:
     ResultRu = f"назва 'name:ru' майстар-маршруту не \"{NameRu}\""
   #
   if ResultBe:
    Result.append(ResultBe)
   if ResultRu:
    Result.append(ResultRu)
   #
  else:
    Result.append(f"незразумелая назва майстар-маршруту")
  return Result


# -=-=-=-=-=-


 def GetLine(self, Class, Master, Relation):
  Result = []
  Tag = Relation['tags']
  MasterTag = Master['tags']
  Member = Relation['members']
  #
  Result += self.CheckBe(Tag)
  Result += self.CheckOfficialName(Tag)
  Result += self.CheckWrong(Tag, self.Wrong)
  Result += self.CheckPair(Tag)
  Result += self.CheckLength(Tag)
  Result += self.CheckImpossible(Tag)
  #
  Result += self.CheckRoles(Member, self.Role)
  #
  Ways = self.GetWays(Relation, Role=[""])
  Ways = self.NormalizeWays(Ways)
  if Ways:
   Result += self.CheckFixme(Ways)
   Result += self.CheckHighway(Ways, self.AllowHighways)
   Result += self.CheckName(Ways)
   Result += self.CheckIsland(Ways, IsOneLine=True)
   Result += self.CheckHaversine(Ways, 0)
  #
  Nodes = self.GetNodes(Relation, Role=["stop", "stop_entry_only", "stop_exit_only"])
  Stops = self.NormalizeNodes(Nodes)
  Nodes = self.GetNodes(Relation, Role=["platform", "platform_entry_only", "platform_exit_only"])
  Platforms = self.NormalizeNodes(Nodes)
  Nodes = self.GetWays(Relation, Role=["platform", "platform_entry_only", "platform_exit_only"])
  Nodes = self.NormalizeWays(Nodes)
  Platforms += self.ConvertPlatform(Nodes)
  #
  Result += self.CheckStop(Ways, Stops)
  Result += self.CheckPlatform(Stops, Platforms)
  #
  Result += self.CheckNodeStop(Stops, Class)
  Result += self.CheckNodePlatform(Platforms)
  #Result += self.CheckStopArea(Stops, Platforms)
  Result += self.CheckNameRoute(Tag, Class)
  Result += self.CheckRoute(Tag, self.AllRoutes, Class, "маршрут")
  Result += self.CheckRouteRole(Member)
  Result += self.CheckNameMaster(MasterTag, Class)
  Result += self.CheckRoute(MasterTag, self.AllMasters, Class, "майстар-маршрут")
  #
  return Result


 def GetRoutes(self, Master):
  Routes = []
  IsError = False
  # router
  for Member in Master['members']:
   Error = []
   if Member['type'] == "relation":
    Relation = self.ReadRelation(Member['ref'])
    Tag = Relation['tags']
    Class = Tag.get('route', "")
    if Tag.get('type', "") == "route": # and Class in self.AllRoutes
     #print(Class, Relation)
     Error += self.GetLine(Class, Master, Relation)
    #
    Be = Tag.get('name:be', "")
    Ru = Tag.get('name:ru', "")
    Type = Tag.get('route', "")
    Route = { 'ID': Relation['id'], "Be": Be, 'Ru': Ru, 'Type': Type, 'Error': Error, }
    Routes.append(Route)
    if Error:
     IsError = True
  # master-route
  Error = []
  MasterTag = Master['tags']
  Be = MasterTag.get('name:be', "")
  Ru = MasterTag.get('name:ru', "")
  Type = MasterTag.get('route_master', "")
  Error += self.CheckTypes(Master, "relation")
  if not Routes:
   Error += ["адсутнічаюць маршруты"]
  if Error:
   IsError = True
  Color = "#ffc0c0" if IsError else "#bbffbb"
  #
  Result = { 'ID': Master['id'], 'Type': Type, "Be": Be, 'Ru': Ru, 'Error': Error, 'Route': Routes, 'Color': Color, }
  return Result


 def GetError(self):
  logger.info("read master routes")
  Result = []
  for Relation in self.GetRelationKey('route_master'):
   #print(Relation)
   Tag = Relation['tags']
   if Tag.get('type', "") == "route_master" and Tag.get('route_master', "") in self.AllRoutes:
    Line = self.GetRoutes(Relation)
    #print(Line)
    Result.append(Line)
  return Result


 def GetMissingMasterRoutes(self):
  logger.info("check routes without master")
  Result = []
  for Relation in self.GetRelationKey('route'):
   Tag = Relation['tags']
   if Tag.get('type', "") == "route" and Tag.get('route', "") in self.AllRoutes and Tag.get('public_transport:version', "") == "2":
     MasterRoute = self.GetRelationsForRelation(Relation['id'])
     if not MasterRoute:
      Be = Tag.get('name:be', "")
      Ru = Tag.get('name:ru', "")
      Color = "#ffc0c0"
      Missing = { 'ID': Relation['id'], "Be": Be, 'Ru': Ru, 'Error': ["не прывязаны да майстар-маршрута"], 'Color': Color, }
      #print(Missing)
      Result.append(Missing)
  return Result


# -=-=-=-=-=-


def Generate():
 RouteBus = RouteBusValidator()
 Result = {}
 #https://wiki.openstreetmap.org/wiki/RU:Relation:route
 Result['Missing'] = RouteBus.GetMissingMasterRoutes()
 Result['Route'] = RouteBus.GetError()
 return Result

