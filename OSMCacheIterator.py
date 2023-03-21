import osmapi


class CacheIterator:

 # захаваць прамежуткавыя значэнні
 def __init__(self, OSM, Count, Array, Exclude=[]):
  self.OSM = OSM
  self.Count = Count
  self.Array = Array
  self.Exclude = Exclude
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
   #print(f"!! {self.Iters[i]}")
   self.Cache = self.GetCache(self.Iters[i])
  #
  #print(f"{self.Type} {i} {j} {self.Iters[i][j]} {self.Iters}")
  #print(f"{self.Iters[i][j]} {self.Cache[self.Iters[i][j]]}")
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
   self.Iters = self.GetItems("node")
  elif self.Type == "node":
   self.Type = "way"
   self.Iters = self.GetItems("way")
  elif self.Type == "way":
   self.Type = "relation"
   self.Iters = self.GetItems("relation")
  else:
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
   if Item['type'] == Type and Item['role'] not in self.Exclude:
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



#OSM = osmapi.OsmApi()
#Relation = OSM.RelationGet(1246287)
#for Member in CacheIterator(OSM, 3, Relation['member']):
# print(Member)
#OSM.close()