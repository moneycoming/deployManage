import time
from django.db import models
from git import Repo
import logging


class TimeChange:
    def __init__(self, timeStamp):
        self.timeStamp = timeStamp

    def ChangeFormat(self):
        timeStamp = self.timeStamp
        timeArray = time.localtime(timeStamp)
        otherStyleTime = time.strftime("%Y--%m--%d %H:%M:%S", timeArray)
        # print(otherStyleTime)
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

    def merge(self, mergeFrom, mergeTo, status):
        repoPath = self.url
        repo = Repo(repoPath)
        origin = repo.remotes.origin
        curBranch = repo.head.reference
        master = repo.heads.master
        git = repo.git
        git.checkout(master)
        origin.pull()
        try:
            repo.delete_head(mergeFrom)
        except:
            logging.warning("删除分支，分支%s不存在" % mergeFrom)
        git.checkout(mergeFrom)
        if curBranch != mergeTo:
            git.checkout(mergeTo)
            origin.pull(mergeTo)
        try:
            git.merge(mergeFrom)
            # 测试的时候关闭推送功能
            # origin.push(mergeTo)
            status = True
            logging.info("分支%s合并成功！" % mergeFrom)
        except:
            past_branch = repo.create_head(mergeTo, 'HEAD')
            repo.head.reference = past_branch
            repo.head.reset(index=True, working_tree=True)
            logging.error("分支%s合并冲突，请手动处理！" % mergeFrom)
        try:
            repo.delete_head(mergeFrom)
        except:
            logging.info("线上没有%s分支！" % mergeFrom)

        return status
