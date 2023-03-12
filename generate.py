#https://behai-nguyen.github.io/2022/06/25/synology-dsm-python.html

import git


def Push(Message):
 PATH = "~/osm-validator"
 try:
  repo = git.Repo(PATH)
  print(repo.git.add(update=True))
  print(repo.index.commit(Message))
  print(origin = repo.remote(name='origin'))
  print(origin.push())
  return True
 except:
  print('Some error occured while pushing the code')
  return False


Push(f"test commit")

