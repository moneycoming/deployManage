# -- coding:UTF-8 --
import time
from django.db import models
from git import Repo
import logging
import subprocess
import json
import datetime
import os

# 添加全局变量，记录日志
logger = logging.getLogger('log')


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)


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
    def __init__(self, url, gitCmd):
        self.url = url
        self.gitCmd = gitCmd

    def merge_branch(self, mergeFrom, mergeTo):
        repoPath = self.url
        gitCmd = self.gitCmd
        repo = Repo(repoPath)
        origin = repo.remotes.origin
        curBranch = repo.head.reference
        master = repo.heads.master
        os.chdir(repoPath)
        try:
            subprocess.check_output([gitCmd, "remote", "update", "--prune"])
        except subprocess.CalledProcessError:
            logger.info("已是最新分支信息，无法更新")
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
                origin.push(mergeTo)
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
        gitCmd = self.gitCmd
        repo = Repo(repoPath)
        origin = repo.remotes.origin
        master = repo.heads.master
        curBranch = repo.head.reference
        os.chdir(repoPath)
        try:
            subprocess.check_output([gitCmd, "remote", "update", "--prune"])
        except subprocess.CalledProcessError:
            logger.info("已是最新分支信息，无法更新")
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

    def delete_branch(self, hopeBranch):
        repoPath = self.url
        gitCmd = self.gitCmd
        os.chdir(repoPath)
        repo = Repo(repoPath)
        master = repo.heads.master
        curBranch = repo.head.reference
        try:
            subprocess.check_output([gitCmd, "remote", "update", "--prune"])
        except subprocess.CalledProcessError:
            logger.info("已是最新分支信息，无法更新")
        try:
            assert curBranch == master
        except AssertionError:
            repo.head.reference = master

        status = True
        try:
            subprocess.check_output([gitCmd, "push", "origin", "--delete", hopeBranch])
        except subprocess.CalledProcessError:
            status = False
            logger.info("线上分支%s删除失败！" % hopeBranch)
        try:
            subprocess.check_output([gitCmd, "branch", "-D", hopeBranch])
        except subprocess.CalledProcessError:
            status = False
            logger.info("本地分支%s删除失败！" % hopeBranch)

        return status

    def create_tag(self, hopeBranch):
        repoPath = self.url
        gitCmd = self.gitCmd
        repo = Repo(repoPath)
        os.chdir(repoPath)
        origin = repo.remotes.origin
        status = True
        try:
            subprocess.check_output([gitCmd, "remote", "update", "--prune"])
        except subprocess.CalledProcessError:
            logger.info("已是最新分支信息，无法更新")
        try:
            subprocess.check_output([gitCmd, "checkout", hopeBranch])
        except subprocess.CalledProcessError:
            status = False
            logger.error("分支%s切换失败" % hopeBranch)
        if status:
            subprocess.check_output([gitCmd, "pull", 'origin', hopeBranch])
            tag_name = "release-" + datetime.datetime.now().strftime('%Y.%m.%d')
            try:
                subprocess.check_output([gitCmd, "tag", "-d", tag_name])
            except subprocess.CalledProcessError:
                logger.info("本地没有该tag！")
            try:
                subprocess.check_output([gitCmd, "push", "origin", "--delete", "tag", tag_name])
            except subprocess.CalledProcessError:
                logger.info("线上没有该tag！")
            try:
                new_tag = repo.create_tag(tag_name, message='发布分支%s' % hopeBranch)
                origin.push(new_tag)
            except:
                status = False

        return status
