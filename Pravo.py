#!.venv/bin/python

import os
import json
import requests

from loguru import logger
from bs4 import BeautifulSoup


URLs = {
 'Беларусь': "https://pravo.by/document/?guid=3961&p0=W22136507",
 'Брестская область': "https://pravo.by/document/?guid=3961&p0=R920b0101102",
 'Витебская область': "https://pravo.by/document/?guid=3961&p0=R920v0100547",
 'Гомельская область': "https://pravo.by/document/?guid=3961&p0=R920g0101937",
 'Гродненская область': "https://pravo.by/document/?guid=3961&p0=R921r0112733",
 'Минская область': "https://pravo.by/document/?guid=3961&p0=R920n0100086",
 'Могилёвская область': "https://pravo.by/document/?guid=3961&p0=R920m0104900",
}

FileName = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Base", "pravo.json")


def GetMain(Soup):
 Result = []
 Div = Soup.find('div', attrs={'class':'reestrmap'})
 if Div:
  for Item in Div.find_all('div'):
   Result.append(Item.text.strip())
 if len(Result) >= 5:
  return [f"{Result[1]}. {Result[2]} ( {Result[3]} от {Result[4]} )"]
 else:
  return ["<font color='red' size='+2'>Памылка!</font>"]


def GetAppend(Soup):
 Result = []
 Table = Soup.find('table', attrs={'class':'map'})
 if Table:
  for Row in Table.find_all('tr'):
   for Col in Row.find_all('td'):
    Result.append(Col.text.strip().replace("\t", "").replace("\n", "").replace("  ", " "))
 return Result[1:]


def DownloadPravo():
 Result = {}
 for District, URL in URLs.items():
  Response = requests.get(URL)
  Soup = BeautifulSoup(Response.text, "html.parser")
  Result[District] = [URL] + GetMain(Soup) + GetAppend(Soup)
 return Result


def CheckPravo():
 logger.info("Check Pravo")
 Pravo = DownloadPravo()
 with open(FileName, encoding="utf-8") as File:
  Json = json.load(File)
 #
 Result = []
 for Key, Value in Pravo.items():
  Line = f"<a href='{Value[0]}'>{Value[1]}</a>"  
  if Value[0] != Json[Key][0] or Value[1] != Json[Key][1]:
   Line = f"<font color='red'><strike>{Line}</strike></font>"
  Result.append(f"<p>\n")
  Result.append(f"{Line}\n")
  if len(Value) > 2:
   Result.append(f"<br />в том числе акты, изменяющие (дополняющие) документ:\n <ul>\n")
   for Index, Item in enumerate(Value):
    if Index >= 2:
     if len(Json[Key]) > Index and Value[Index] == Json[Key][Index]:
      Result.append(f"  <li>{Item}</li>\n")
     else:
      Result.append(f"  <li><font color='red'><strike>{Item}</strike></font></li>\n")
   Result.append(f" </ul>\n")
  Result.append(f"</p>\n<hr width='50%' align='left'>\n")
 return Result


def GetPravo():
 logger.info("Get Pravo")
 Pravo = DownloadPravo()
 with open(FileName, encoding="utf-8") as File:
  Json = json.load(File)
 #
 Error, Result = False, []
 for Key, Value in Pravo.items():
  Item = {}
  Item['URL'] = Value[0]
  Item['Desc'] = Value[1]
  Sub = []
  for Index, Desc in enumerate(Value):
   if Index >= 2:
    E = not(len(Json[Key]) > Index and Value[Index] == Json[Key][Index])
    Sub.append({'Desc': Desc, 'Error': E })
    Error |= E
  Item['Append'] = Sub
  E = Value[0] != Json[Key][0] or Value[1] != Json[Key][1]
  Item['Error'] = E
  Error |= E
  Result.append(Item)
 return Error, Result


def Main():
 logger.add(os.path.join(".log", "osm.log"))
 logger.info("Start Pravo")
 Pravo = DownloadPravo()
 with open(FileName, 'w', encoding="utf-8") as File:
  json.dump(Pravo, File, ensure_ascii=False, indent=4)
 logger.info("Done Pravo")


if __name__ == "__main__":
 Main()
