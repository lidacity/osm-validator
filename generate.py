#!.venv/bin/python

#https://behai-nguyen.github.io/2022/06/25/synology-dsm-python.html
#https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent

import git


def Push(Message):
 PATH = "~/osm-validator"
 try:
  print(1)
  repo = git.Repo(PATH)
  print(2)
  repo.git.add(update=True)
  print(3)
  repo.index.commit(Message)
  print(4)
  origin = repo.remote(name='origin')
  Print(5)
  origin.push()
  return True
 except:
  print('Some error occured while pushing the code')
  return False


if Push(f"test commit"):
 print("Ok")

