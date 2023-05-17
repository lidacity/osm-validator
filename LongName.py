import sys
from OSM import Validator


if len(sys.argv) == 2:
 _, S = sys.argv
 #
 Convert = Validator()
 R = {}
 R |= Convert.SplitName(S)
 print(R)
 S1 = Convert.JoinName(R)
 if S != S1:
  print("Oops! error")
else:
 print("usage\n\t./longname.py \"Very Long Name\"")
