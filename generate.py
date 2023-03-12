#!.venv/bin/python

#https://behai-nguyen.github.io/2022/06/25/synology-dsm-python.html

import git


def Push(Message):
 PATH = "~/osm-validator"
 try:
  repo = git.Repo(PATH)
  repo.git.add(update=True)
  repo.index.commit(Message)
  origin = repo.remote(name='origin')
  origin.push()
  return True
 except:
  print('Some error occured while pushing the code')
  return False


if Push(f"test commit"):
 print("Ok")

