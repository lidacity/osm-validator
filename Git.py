#!.venv/bin/python

#https://behai-nguyen.github.io/2022/06/25/synology-dsm-python.html
#https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent

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
