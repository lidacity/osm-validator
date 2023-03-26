#https://behai-nguyen.github.io/2022/06/25/synology-dsm-python.html
#https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent

import os
import git

from loguru import logger


def GitPush(Message):
 logger.info("Git Push")
 try:
  PathName = os.path.dirname(os.path.abspath(__file__))
  repo = git.Repo(PathName)
  repo.git.add("docs")
  #repo.git.add(update=True)
  repo.index.commit(Message)
  origin = repo.remote(name='origin')
  origin.push()
  return repo.git.diff('HEAD~1')
 except:
  logger.error('Some error occured while pushing the code')
  return None
