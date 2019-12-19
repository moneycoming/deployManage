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
        master = repo.heads.master
        os.chdir(repoPath)
        git = repo.git
        status = True
        try:
            git.checkout(master)
            logger.info("master分支切换成功！")
        except:
            status = False
            logger.info("maser分支切换失败！")
        try:
            subprocess.check_output([gitCmd, "remote", "update", "--prune"])
        except subprocess.CalledProcessError:
            logger.info("已是最新分支信息，无法更新")
        try:
            subprocess.check_output([gitCmd, "branch", "-D", mergeTo])
            subprocess.check_output([gitCmd, "branch", "-D", mergeFrom])
            logger.info("本地旧分支删除完成！")
        except subprocess.CalledProcessError:
            logger.info("本地没有旧分支！")
        origin.pull(master)
        logger.info("=========合并准备前准备已经完成============")

        try:
            git.checkout(mergeFrom)
            logger.info("1.本地开发分支：%s创建成功！" % mergeFrom)
            try:
                git.checkout(mergeTo)
                logger.info("2.本地预发分支：%s创建成功！" % mergeTo)
            except:
                status = False
                logger.error("本地分支：%s， 创建失败！" % mergeTo)
        except:
            status = False
            logger.error("本地分支：%s, 创建失败！" % mergeFrom)

        if status:
            try:
                git.checkout(mergeTo)
            except:
                status = False
                logger.info("mergeTo分支：%s，切换失败" % mergeTo)
            if status:
                try:
                    git.merge(mergeFrom)
                    origin.push(mergeTo)
                    logger.info("3.预发分支：%s合并成功！" % mergeTo)
                except:
                    past_branch = repo.create_head(mergeTo, 'HEAD')
                    repo.head.reference = past_branch
                    repo.head.reset(index=True, working_tree=True)
                    logger.error("分支：%s合并到分支：%s冲突，请手动处理！" % (mergeFrom, mergeTo))
                    status = False
                try:
                    git.checkout(master)
                    if mergeTo == 'master':
                        subprocess.check_output([gitCmd, "branch", "-D", mergeFrom])
                        logger.info("4.本地开发分支：%s，预发分支：%s删除成功！" % (mergeFrom, mergeTo))
                    else:
                        subprocess.check_output([gitCmd, "branch", "-D", mergeTo])
                        subprocess.check_output([gitCmd, "branch", "-D", mergeFrom])
                        logger.info("4.本地开发分支：%s，预发分支：%s删除成功！" % (mergeFrom, mergeTo))
                except:
                    logger.error("本地分支删除失败！")

        return status

    def create_branch(self, hopeBranch):
        repoPath = self.url
        gitCmd = self.gitCmd
        repo = Repo(repoPath)
        origin = repo.remotes.origin
        master = repo.heads.master
        os.chdir(repoPath)
        git = repo.git
        status = True
        try:
            subprocess.check_output([gitCmd, "remote", "update", "--prune"])
        except subprocess.CalledProcessError:
            logger.info("已是最新分支信息，无法更新")
        try:
            git.checkout(master)
            logger.info("master分支切换成功！")
            try:
                subprocess.check_output([gitCmd, "branch", "-D", hopeBranch])
            except subprocess.CalledProcessError:
                logger.warning("删除分支，分支%s不存在" % hopeBranch)
        except:
            status = False
            logger.error("master分支切换失败！")

        if status:
            logger.info("=========分支创建准备工作完成=============")
            repo.create_head(hopeBranch, origin.refs.master)
            origin.push(hopeBranch)
            logger.info("分支%s，创建成功！" % hopeBranch)
            try:
                subprocess.check_output([gitCmd, "branch", "-D", hopeBranch])
            except subprocess.CalledProcessError:
                logger.error("本地分支%s，删除失败！" % hopeBranch)

    def delete_branch(self, hopeBranch):
        repoPath = self.url
        gitCmd = self.gitCmd
        os.chdir(repoPath)
        repo = Repo(repoPath)
        master = repo.heads.master
        git = repo.git
        status = True
        try:
            subprocess.check_output([gitCmd, "remote", "update", "--prune"])
        except subprocess.CalledProcessError:
            logger.info("已是最新分支信息，无法更新")
        try:
            git.checkout(master)
        except:
            status = False
            logger.error("master分支切换失败！")

        if status:
            logger.info("==========删除分支准备工作完成==================")
            try:
                subprocess.check_output([gitCmd, "push", "origin", "--delete", hopeBranch])
                logger.info("1.线上分支：%s删除成功！" % hopeBranch)
            except subprocess.CalledProcessError:
                status = False
                logger.error("线上分支%s删除失败！" % hopeBranch)
            try:
                subprocess.check_output([gitCmd, "branch", "-D", hopeBranch])
                logger.info("2.本地分支：%s删除成功！" % hopeBranch)
            except subprocess.CalledProcessError:
                status = False
                logger.error("本地分支%s删除失败！" % hopeBranch)

        return status

    def create_tag(self, hopeBranch):
        repoPath = self.url
        gitCmd = self.gitCmd
        repo = Repo(repoPath)
        os.chdir(repoPath)
        origin = repo.remotes.origin
        # curBranch = repo.head.reference
        master = repo.heads.master
        git = repo.git
        status = True
        try:
            subprocess.check_output([gitCmd, "remote", "update", "--prune"])
        except subprocess.CalledProcessError:
            logger.info("已是最新分支信息，无法更新")
        try:
            git.checkout(master)
            logger.info("master分支切换成功！")
        except:
            status = False
            logger.error("master分支切换失败！")
        if status:
            try:
                subprocess.check_output([gitCmd, "branch", "-D", hopeBranch])
                logger.info("1.本地分支：%s，删除成功！" % hopeBranch)
            except subprocess.CalledProcessError:
                logger.info("本地没有分支;%s" % hopeBranch)
            try:
                git.checkout(hopeBranch)
                logger.info("2.本地分支：%s，创建成功！" % hopeBranch)
            except:
                status = False
                logger.error("分支%s,创建失败！" % hopeBranch)

        if status:
            logger.info("=========创建tag准备工作完成===============")
            tag_name = "release-" + datetime.datetime.now().strftime('%Y.%m.%d')
            try:
                repo.delete_tag(tag_name)
            except:
                logger.warning("本地没有%s！" % tag_name)
            try:
                subprocess.check_output([gitCmd, "push", "origin", "--delete", "tag", tag_name])
            except subprocess.CalledProcessError:
                logger.warning("线上没有%s！" % tag_name)
            try:
                new_tag = repo.create_tag(tag_name, message='发布分支%s' % hopeBranch)
                origin.push(new_tag)
                logger.info("3.tag%s创建成功！" % tag_name)
            except:
                logger.error("tag%s创建失败！" % tag_name)
                status = False

        return status
