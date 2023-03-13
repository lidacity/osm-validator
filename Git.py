#https://behai-nguyen.github.io/2022/06/25/synology-dsm-python.html

import git

from loguru import logger


PATH = "~/osm-validator"


def GitPush(Message):
 logger.info("Git Push")
 try:
  repo = git.Repo(PATH)
  repo.git.add(update=True)
  repo.index.commit(Message)
  origin = repo.remote(name='origin')
  origin.push()
  return True
 except:
  logger.error('Some error occured while pushing the code')
  return False
