from git import Repo


repoPath = "D:\codes\jlb-sms"
repo = Repo(repoPath)
master = repo.heads.master
origin = repo.remotes.origin
new_branch = "uat-2019abc"
new_tag = "release-2.00"
git = repo.git
git.checkout(master)
git.pull(origin, master)
repo.create_head(new_branch, origin.refs.master)
# git.checkout(new_branch)
git.push(origin, new_branch)
# new_tag = repo.create_tag(new_tag, message='发布分支%s' % new_branch)
# git.push(origin, new_tag)
# git.push(origin, new_branch)
# repo.delete_head(new_branch)

# repo.delete_head(new_branch)
# try:
#     assert not repo.is_dirty()
# except AssertionError:
#     past_branch = repo.create_head(new_branch, 'HEAD')
#     repo.head.reference = past_branch
#     repo.head.reset(index=True, working_tree=True)
# try:
#     curBranch = repo.head.reference
#     assert curBranch == master
# except AssertionError:
#     repo.head.reference = master
# repo.delete_head(new_branch)
# new_tag = repo.create_tag(new_tag, message='my message')
# repo.head.reference = new_branch
# assert not repo.head.is_detached
# repo.head.reset(index=True, working_tree=True)
# assert not repo.delete_head(new_branch).exists()
# try:
#     repo.delete_head(new_branch)
# except:
#     print("%s不存在" % new_branch)
# origin = repo.remotes.origin
# new_branch = repo.create_head(new_branch, origin.refs.master)
# repo.head.reference = new_branch
