from git import Repo

PATH_OF_GIT_REPO = "~/osm/osm-validator"  # make sure .git folder is properly configured
COMMIT_MESSAGE = 'comment from python script'

def git_push():
#    try:
        repo = Repo(PATH_OF_GIT_REPO)
        repo.git.add(update=True)
        repo.index.commit(COMMIT_MESSAGE)
        origin = repo.remote(name='origin')
#        origin.pull()
        origin.push()

#        repo.git.grep("--files-with-matches", "\"config.isEnabled([[:space:]*]'async-payments'[[:space:]*])\"]")

        #repo.git.push()
#    except:
#        print('Some error occured while pushing the code')

git_push()
sys.exit(0)



import sys
#import subprocess as cmd

#def git_push_automation():
# try:
#  cp = cmd.run("file path", check=True, shell=True)
#  print("cp", cp)
#  cmd.run("git add .", check=True, shell=True)
#  cmd.run('git commit -m "message"', check=True, shell=True)
#  cmd.run('git add .', check=True, shell=True)
#  cmd.run("git push", check=True, shell=True)
#  print("Success")
#  return True
# except:
#  print("Error git automation")
#  return False

#git_push_automation()
#sys.exit(0)

#from git import Repo
#Repo.clone_from("https://github.com/lidacity/osm-validator", "osm-validator")



import git

repo = git.Repo('~/osm/osm-validator')





#print(repo.index.add(['.']))
#print(repo.index.commit('Initial commit'))
#print(repo.remotes.origin.push())
print(repo.remotes.origin.url)
#print(repo.remotes.origin.push())
#origin = repo.create_remote("origin", repo.remotes.origin.url)
#origin = repo.remote()
print(repo.remotes.origin.fetch())


repo.remotes.origin.fetch()  # assure we actually have data. fetch() returns useful information
# Three above commands in one:

repo.remotes.origin.push()
#repo.remotes.origin.pull()
#print(repo.remotes.push())

#repo.git.push()

#print(repo.remotes.origin.push())



# List remotes
#print('Remotes:')
#for remote in repo.remotes:
#    print(f'- {remote.name} {remote.url}')

# Create a new remote
#try:
#    remote = repo.create_remote('origin', url='git@github.com:NanoDano/testrepo')
#except git.exc.GitCommandError as error:
#    print(f'Error creating remote: {error}')

# Reference a remote by its name as part of the object
#print(f'Remote name: {repo.remotes.origin.name}')
#print(f'Remote URL: {repo.remotes.origin.url}')

# Delete a remote
#repo.delete_remote('myremote')

# Pull from remote repo
#print(repo.remotes.origin.pull())
# Push changes

#origin = repo.remote(name='origin')
#origin.push()


#print(repo.remotes.origin.push())

