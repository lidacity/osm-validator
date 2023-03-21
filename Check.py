import re

Classes = {
 'М': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:national', 'name': None, 'name:be': None, 'name:ru': None, },
 'Р': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:national', 'name': None, 'name:be': None, 'name:ru': None, },
 'Н': { 'ref': None, 'official_ref': None, 'type': 'route', 'route': 'road', 'network': 'by:regional', 'name': None, 'name:be': None, 'name:ru': None, },
}


def Ref(Key):
 Result = []
 if Key[:6] == "error-":
  Result.append(f"'official_ref' несапраўдны!")
 return Result


def Relation(Type):
 Result = []
 if Type != "relation":
  Result.append(f"не 'relation'")
 return Result


def Tag(Tag, Class):
 Result = []
 for Key, Value in Classes[Class].items():
  if Key not in Tag:
   Result.append(f"'{Key}' не знойдзены")
  elif Value is not None:
   if Tag[Key] != Value:
    Result.append(f"у '{Key}' не зададзена '{Value}'")
 return Result
   

def Class(Tag, Class):
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


def Be(Tag):
 Result = []
 Name = Tag.get('name', None)
 Be = Tag.get('name:be', None)
 if Name != Be:
  Result.append(f"'name:be' не роўны 'name'")
 return Result


def Ru(Tag, Name):
 Result = []
 Ru = Tag.get('name:ru', "")
 if Name[:254] != Ru[:254]:
  Result.append(f"'name:ru' не супадае з назвай у Законе")
 return Result


def Abbr(Tag):
 Result = []
 for N in [ 'name', 'name:be', 'name:ru' ]:
  Name = Tag.get(N, "")
  Abbreviations = ["’", "—", "а/д", "г.п.", "г.", "аг.", "п.", "д.", "х.", "ж/д", "ст.", "с/т", "с/с", "хоз.", "Ж/д", "А/д", "С/т", "Ст.", "обл.", "Гр.", "р-на", ]
  for A in Abbreviations:
   if A in Name:
    Result.append(f"недапушчальны скарот у '{N}'")
    break
 return Result


def OfficialName(Tag):
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
 return Result


#


ReRefs2 = { 'ok': re.compile("[МР]-[0-9]+/[ЕП] [0-9]+|[МРН]-[0-9]+"), 'bad': re.compile("[МРН][0-9]+"), }


def GetList(Name, Type):
 return re.findall(ReRefs2[Type], Name)


def GetIndex(S, Ref):
 return [m.start() for m in re.finditer(Ref, S)]


def ExcludeRef(Name, Index):
 return Name[Index-1:].strip()[:1] in ["(", ")", ""]


def BadRefInRelation(Relation, Relations):
 Result = []
 Tag = Relation['tag']
 for Name in [ 'name', 'name:be', 'name:ru' ]:
  if Name in Tag:
   if GetList(Tag[Name], 'bad'):
    Result.append(f"Не вызначаны 'ref' у апісанні {Name}")
 return Result


def RefInRelation(Relation, Relations):
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
        Result.append(f"Апісанне {Ref} не адпавядае свайму апісанню ў {Name}")
    else:
     Result.append(f"Не вызначаны {Ref} у апісанні {Name}")
 return Result
