from loguru import logger

from Validator import Validator



class BoundaryValidator(Validator):

 def GetColor(self, Error, Warning):
  if Error:
   return "#ffc0c0", "немагчыма замкнуць"
  elif Warning:
   return "#ffcc00", "не замкнуты"
  else:
   return "#bbffbb", ""


 def CheckIsland(self, Nodes):
  for x1, x2 in Nodes:
   if x1 != x2:
    return True
  return False


 def Recurse(self, Level, ID):
  Relation = self.ReadRelation(ID)
  Tag = Relation['tags']
  Name = Tag['name']
  Ways = self.GetWays(Relation, Role=['outer', 'inner'])
  if Ways:
   Warning = self.IslandLine(Ways)
   Error = self.Island(Ways)
   Warning = self.CheckIsland(Warning)
   Error = self.CheckIsland(Error)
   Color, Text = self.GetColor(Error, Warning)
   yield {'Level': Level, 'ID': ID, 'Name': Name, 'Error': [Text], 'Color': Color}
   for Feature in self.GetRelations(Relation, Role=['subarea']):
    yield from self.Recurse(Level+1, Feature['id'])


# -=-=-=-=-=-


def Generate(ID):
 logger.info("Boundary")
 Boundary = BoundaryValidator()
 Result = Boundary.Recurse(1, ID)
 return {'Boundary': list(Result)}
