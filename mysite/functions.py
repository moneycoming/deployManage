# -- coding:UTF-8 --
import time
from django.db import models
from git import Repo
import logging
import subprocess

# 添加全局变量，记录日志
logger = logging.getLogger('log')


class TimeChange:
    def __init__(self, timeStamp):
        self.timeStamp = timeStamp

    def ChangeFormat(self):
        timeStamp = self.timeStamp
        timeArray = time.localtime(timeStamp)
        otherStyleTime = time.strftime("%Y--%m--%d %H:%M:%S", timeArray)

        return otherStyleTime


class fileObj(models.Model):
    def __init__(self, fileKeyList, createDateList):
        self.fileKeyList = fileKeyList
        self.createDateList = createDateList
        self.index = len(fileKeyList)

    def __iter__(self):
        return self

    def __next__(self):
        if self.index == 0:
            raise StopIteration
        self.index -= 1
        return self.fileKeyList[self.index], self.createDateList[self.index]


class branch:
    def __init__(self, url):
        self.url = url

    def merge_branch(self, mergeFrom, mergeTo):
        repoPath = self.url
        repo = Repo(repoPath)
        origin = repo.remotes.origin
        curBranch = repo.head.reference
        master = repo.heads.master
        subprocess.check_output(["git", "remote", "update", "--prune"])
        status = True
        try:
            assert curBranch == master
        except AssertionError:
            repo.head.reference = master
        try:
            repo.delete_head(mergeTo)
        except:
            logger.warning("删除分支，分支%s不存在" % mergeTo)
        try:
            repo.delete_head(mergeFrom)
        except:
            logger.warning("删除分支，分支%s不存在" % mergeFrom)
        origin.pull()
        git = repo.git
        try:
            git.checkout(mergeFrom)
        except:
            status = False
            logger.error("线上没有分支%s" % mergeFrom)

        try:
            git.checkout(mergeTo)
        except:
            status = False
            logger.error("线上没有分支%s" % mergeTo)

        if status:
            try:
                assert curBranch == mergeTo
            except AssertionError:
                git.checkout(mergeTo)
            try:
                git.merge(mergeFrom)
                # origin.push(mergeTo)
                logger.info("分支%s合并成功！" % mergeFrom)
            except:
                past_branch = repo.create_head(mergeTo, 'HEAD')
                repo.head.reference = past_branch
                repo.head.reset(index=True, working_tree=True)
                logger.error("分支%s合并到分支%s冲突，请手动处理！" % (mergeFrom, mergeTo))
                status = False
            try:
                repo.delete_head(mergeFrom)
            except:
                logger.info("本地没有分支%s" % mergeFrom)

        return status

    def create_branch(self, hopeBranch):
        repoPath = self.url
        repo = Repo(repoPath)
        origin = repo.remotes.origin
        master = repo.heads.master
        curBranch = repo.head.reference
        subprocess.check_output(["git", "remote", "update", "--prune"])
        try:
            assert curBranch == master
        except AssertionError:
            repo.head.reference = master
        try:
            repo.delete_head(hopeBranch)
        except:
            logger.warning("删除分支，分支%s不存在" % hopeBranch)
        try:
            assert not repo.is_dirty()
        except AssertionError:
            past_branch = repo.create_head(master, 'HEAD')
            repo.head.reference = past_branch
            repo.head.reset(index=True, working_tree=True)
        origin.pull()
        hopeBranch = repo.create_head(hopeBranch, 'HEAD')
        origin.push(hopeBranch)
        repo.delete_head(hopeBranch)

