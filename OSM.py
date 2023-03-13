import os
import sys
import random
import datetime

from loguru import logger
import osmapi



#  File.write(f"<font size='-1'>старонка створаная {datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}</font>\n")

def HtmlWrite(Key, Value, Relation):
 with open("index.html", mode="a", encoding="utf-8") as File:
  ID = Relation.get('id', None)
  Tag = Relation.get('tag', {})
  Color = "#bbffbb" if Tag else "#D6E090"
  ColorError = "#bbffbb" if Tag else "#D6E090"
  Be = Tag.get('name', "")
  Ru = Tag.get('name:ru', f"{Value}")
  #
  E, Error = GetError(Key, Value, Relation)
  if E and Error:
   ColorError = "#FFC0C0"
  #
  File.write(f"<tr bgcolor='{Color}' valign='top'>\n")
  File.write(f" <td><a>{Key}</a></td>\n")
  if ID:
   File.write(f" <td><a target='_blank' href='https://openstreetmap.org/relation/{ID}'>osm</a><br /><a target='_josm' href='.#' onclick='return josm({ID});'>josm</a></td>\n")
  else:
   File.write(f" <td><br /></td>\n")
  if Tag:
   File.write(f" <td>{Be}<br /><font color='gray'>{Ru}</font></td>\n")
  else:
   File.write(f" <td><font color='gray'><i>{Ru}<i></font></td>\n")
  File.write(f" <td bgcolor='{ColorError}'><nobr>{Error}</nobr></td>\n")
  File.write(f"</tr>\n")


def HtmlWrite2(Key, Relation):
 with open("index.html", mode="a", encoding="utf-8") as File:
  ID = Relation.get('id', None)
  Tag = Relation.get('tag', {})
  Color = "#FFC0C0"
  Be = Tag.get('name', "")
  Ru = Tag.get('name:ru', "")
  Error = "адсутнічае&nbsp;ў&nbsp;Законе"
  #
  File.write(f"<tr bgcolor='{Color}' valign='top'>\n")
  File.write(f" <td><a>{Key}</a></td>\n")
  if ID:
   File.write(f" <td><a target='_blank' href='https://openstreetmap.org/relation/{ID}'>osm</a><br /><a target='_josm' href='.#' onclick='return josm({ID});'>josm</a></td>\n")
  else:
   File.write(f" <td><br /></td>\n")
  if Tag:
   File.write(f" <td>{Be}<br /><font color='gray'>{Ru}</font></td>\n")
  else:
   File.write(f" <td><font color='gray'><i>{Ru}<i></font></td>\n")
  File.write(f" <td><nobr>{Error}</nobr></td>\n")
  File.write(f"</tr>\n")





def GetError(Key, Value, Relation):
 Result = []
 Tag = Relation.get('tag', {})
 if Tag:
  Result += CheckRef(Key)
  Result += CheckTag(Tag, {'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:regional', 'name': None, 'name:be': None, 'name:ru': None})
  Result += CheckH(Tag)
  Result += CheckBe(Tag)
  Result += CheckRu(Tag, Value)
  E = True
 else:
  Result = ["relation адсутнічае"]
  E = False
 return E, "<br/>".join(Result) if Result else ""



def Load(FileName):
 Result = {}
 for Line in open(FileName, mode="r", encoding="utf-8"):
  S = Line.strip().split(";")
  Tag, Desc = S[0], S[1]
  Result[Tag] = Desc
 return Result


def GetRef(Tag):
 return Tag.get('official_ref', f"error-{random.randint(0, 999999)}")


def CheckRef(Key):
 Result = []
 if Key[:6] == "error-":
  Result.append(f"'{Key}' несапраўдны!")
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
   

def CheckH(Tag):
 Result = []
 Ref = Tag['ref']
 OfficialRef = Tag['official_ref']
 if Ref[0] != "Н":
  Result.append(f"'ref' не пачынаецца з 'Н'")
 if OfficialRef[:2] != "Н-":
  Result.append(f"'official_ref' не пачынаецца з 'Н-'")
 if Ref[1:] != OfficialRef[2:]:
  Result.append(f"'official_ref' не суадносны 'ref'")
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
 #
 return Result


def GetNot(All, CSV):
 Result = {}
 for Key, Relation in All.items():
  if Key not in CSV:
   Result[Key] = Relation
 return Result




def ReadOSM(R):
 logger.info(f"Read Main Relation {R}")
 Result = {}

 i = 10

 OSM = osmapi.OsmApi()
 Relation = OSM.RelationGet(R)
 for Member in Relation['member']:
  logger.info(f"Relation {Member['ref']}")
  Relation = OSM.RelationGet(Member['ref'])
  Tag = Relation['tag']
  Ref = GetRef(Tag)
  Result[Ref] = Relation

  if i == 0:
   break
  else:
   i -= 1

 OSM.close()
 return Result

# FileName = os.path.join("Base", FileName)
# CSV = Load(FileName)

#HtmlStart()
#for Key, Value in CSV.items():
# HtmlWrite(Key, Value, All.get(Key, {}))
#for Key, Relation in GetNot(All, CSV).items():
# HtmlWrite2(Key, Relation)
#HtmlFinish()
