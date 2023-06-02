import os

from loguru import logger
import git


#https://behai-nguyen.github.io/2022/06/25/synology-dsm-python.html
#https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent
def GitPush(Message):
 logger.info("Git Push")
 try:
  Path = os.path.dirname(os.path.abspath(__file__))
  Repo = git.Repo(Path)
  Repo.git.add("docs")
  #Repo.git.add(update=True)
  Repo.index.commit(Message)
  Origin = Repo.remote(name='origin')
  Origin.push()
  return Repo.git.diff('HEAD~1')
 except:
  logger.error('Some error occured while pushing the code')
  return None
