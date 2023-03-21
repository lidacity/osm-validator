import osmapi


class CacheIterator:

 # захаваць прамежуткавыя значэнні
 def __init__(self, Count, Array, Type=["node", "way", "relation"], Role=[]):
  self.OSM = osmapi.OsmApi()
  self.Count = Count
  self.Array = Array
  self.IncludeType = Type
  self.ExcludeRole = Role
  self.Type = ""
  self.Iters = self.GetIters()
  self.i = 0
  self.j = 0
  self.Cache = {}


 # абнавіць значэнне і вярнуць вынік
 def __next__(self):
  i, j = self.i, self.j
  IsCache = self.j == 0
  #
  if self.i > len(self.Iters) - 1:
   self.Iters = self.GetIters()
   i, j = self.i, self.j = 0, 0
  if self.j < len(self.Iters[i]) - 1:
   self.j += 1
  else:
   self.i += 1
   self.j = 0
  #
  if IsCache:
   Cache = self.GetCache(self.Iters[i])
   self.Cache = { Key: Cache[Key] for Key in self.Iters[i] }
  #
  Index = self.Iters[i][j]
  return self.Type, self.Cache[Index]
 

 def GetCache(self, IDs):
  if self.Type == "node":
   return self.OSM.NodesGet(IDs)
  elif self.Type == "way":
   return self.OSM.WaysGet(IDs)
  elif self.Type == "relation":
   return self.OSM.RelationsGet(IDs)
  else:
   raise "Error!"


 def GetIters(self):
  if self.Type == "":
   self.Type = "node"
   if self.Type in self.IncludeType:
    self.Iters = self.GetItems("node")
   else:
    return self.GetIters()
  elif self.Type == "node":
   self.Type = "way"
   if self.Type in self.IncludeType:
    self.Iters = self.GetItems("way")
   else:
    return self.GetIters()
  elif self.Type == "way":
   self.Type = "relation"
   if self.Type in self.IncludeType:
    self.Iters = self.GetItems("relation")
   else:
    return self.GetIters()
  else:
   self.OSM.close()
   raise StopIteration
  #
  if self.Iters:
   return self.Iters
  else:
   return self.GetIters()


 def GetItems(self, Type):
  Result = []
  Index, Items = 0, []
  for Item in self.Array:
   if Item['type'] == Type and Item['role'] not in self.ExcludeRole:
    Items.append(Item['ref'])
    if Index >= self.Count - 1:
     Result.append(Items)
     Index, Items = 0, []
    else:
     Index += 1
  if Items:
   Result.append(Items)
  return Result


 def __iter__(self):
  return self



class ArrayCacheIterator:

 # захаваць прамежуткавыя значэнні
 def __init__(self, Count, Array, Type):
  self.OSM = osmapi.OsmApi()
  self.Count = Count
  self.Array = Array
  self.Type = Type
  self.Iters = self.GetItems()
  self.i = 0
  self.j = 0
  self.Cache = {}


 # абнавіць значэнне і вярнуць вынік
 def __next__(self):
  i, j = self.i, self.j
  IsCache = self.j == 0
  #
  if self.i > len(self.Iters) - 1:
   raise StopIteration
  if self.j < len(self.Iters[i]) - 1:
   self.j += 1
  else:
   self.i += 1
   self.j = 0
  #
  if IsCache:
   Cache = self.GetCache(self.Iters[i])
   self.Cache = { Key: Cache[Key] for Key in self.Iters[i] }
  #
  Index = self.Iters[i][j]
  return self.Cache[Index]
 

 def GetCache(self, IDs):
  if self.Type == "node":
   return self.OSM.NodesGet(IDs)
  elif self.Type == "way":
   return self.OSM.WaysGet(IDs)
  elif self.Type == "relation":
   return self.OSM.RelationsGet(IDs)
  else:
   raise "Error!"


 def GetItems(self):
  Result = []
  Index, Items = 0, []
  for Item in self.Array:
   Items.append(Item)
   if Index >= self.Count - 1:
    Result.append(Items)
    Index, Items = 0, []
   else:
    Index += 1
  if Items:
   Result.append(Items)
  #
  return Result


 def __iter__(self):
  return self
