from git import Repo
import os
import subprocess


project_dir = "D:\codes\zxz-app-service"
# repo = Repo(project_dir)
# curBranch = repo.head.reference
# origin = repo.remotes.origin
# remote = repo.remote()
# # print(origin.refs)
# git = repo.git
# git.checkout('test')

# project = self.project
# project_dir = project.project_dir
os.chdir(project_dir)
branch_byte = subprocess.check_output(["git", "branch", "-r"])
# print(branch_byte)
# branch_byte = subprocess.check_output(["git", "remote", "update", "--prune"])
branch_str = str(branch_byte, 'utf-8')
# print(branch_str)
branches = branch_str.split('\n')
branch_list = []
for branch in branches[1: -1]:
    branch_list.append(branch.lstrip('* origin').lstrip('/').lstrip('uat-*'))
    # branch_list.append(branch.lstrip('* origin'))
    if 'master' in branch_list:
        branch_list.remove('master')
    # branch_list.lstrip('/')
    print(branch_list)
# print(git.update(remote))
# heads = repo.heads
# master = heads.master
# devBranch = "opt_alltest"
# try:
#     assert curBranch == master
# except AssertionError:
#     repo.head.reference = master
# try:
#     repo.delete_head(devBranch)
# except:
#     print("该分支不存在")
# try:
#     assert not repo.is_dirty()
# except AssertionError:
#     past_branch = repo.create_head(master, 'HEAD')
#     repo.head.reference = past_branch
#     repo.head.reset(index=True, working_tree=True)
# origin.pull()
# git = repo.git
# try:
#     git.checkout(devBranch)
#     origin.pull(devBranch)
# except:
#     print("线上没有该分支")
