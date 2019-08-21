import jenkins
from mysite import models
import time
import logging
import os
import subprocess


# 添加全局变量，记录日志
logger = logging.getLogger('log')


class PythonJenkins:
    def __init__(self, jenkinsJob, param):
        self.jenkinsJob = jenkinsJob
        self.param = param
        token = "114cac1892a8158d6e0f4d51e117d016da"
        url = "http://10.10.10.24:8080"
        user = "zhumingjie"
        self.server = jenkins.Jenkins(url, username=user, password=token)

    def deploy(self):
        jenkinsJob = self.jenkinsJob
        param = self.param
        server = self.server
        try:
            next_build_number = server.get_job_info(jenkinsJob)['nextBuildNumber']
            server.build_job(jenkinsJob, param)
            time.sleep(15)
            console_opt = server.get_build_console_output(jenkinsJob, next_build_number)
        except jenkins.NotFoundException:
            console_opt = None
            logger.error("jenkins项目未找到，请检查项目是否存在")
        return console_opt

    def isFinished(self):
        jenkinsJob = self.jenkinsJob
        server = self.server
        last_build_number = server.get_job_info(jenkinsJob)['nextBuildNumber'] - 1
        console_opt = server.get_build_console_output(jenkinsJob, last_build_number)
        return console_opt

    def look_uat_buildId(self):
        jenkinsJob = self.jenkinsJob
        server = self.server
        last_build_number = server.get_job_info(jenkinsJob)['lastCompletedBuild']['number']

        return last_build_number


class projectBean:
    def __init__(self, project):
        self.project = project

    def look_branch(self):
        project = self.project
        project_dir = project.project_dir
        os.chdir(project_dir)
        subprocess.check_output(["git", "remote", "update", "--prune"])
        branch_byte = subprocess.check_output(["git", "branch", "-r"])
        branch_str = str(branch_byte, 'utf-8')
        branches = branch_str.split('\n')
        branch_list = []
        for branch in branches[1: -1]:
            branch_list.append(branch.lstrip('* origin').lstrip('/'))
            if 'master' in branch_list:
                branch_list.remove('master')

        return branch_list


# 事务回滚
class Transaction:
    def __init__(self, taskDetail_obj, taskDetail_all_obj, priority):
        self.taskDetail_obj = taskDetail_obj
        self.taskDetail_all_obj = taskDetail_all_obj
        self.priority = priority

    # 任务发布
    def transRunBuild(self):
        params = {}
        taskDetail_obj = self.taskDetail_obj
        taskDetail_all_obj = self.taskDetail_all_obj
        priority = self.priority
        trans_taskDetail_obj = taskDetail_obj.filter(priority__lte=priority).order_by('priority')
        rollbackError = []
        for i in range(len(trans_taskDetail_obj)):
            buildId = trans_taskDetail_obj[i].packageId
            jenkinsJob_obj = trans_taskDetail_obj[i].proJenkins
            param = eval(jenkinsJob_obj.param)
            try:
                pre_build = \
                    taskDetail_all_obj.filter(proJenkins=jenkinsJob_obj, packageId__lt=buildId).order_by('-packageId')[
                        0].packageId
                serverInfo_obj = models.jenkinsPro_serverInfo.objects.filter(proJenkins=jenkinsJob_obj)
                for j in range(len(serverInfo_obj)):
                    params.update(param)
                    params.update(SERVER_IP=serverInfo_obj[j].serverInfo.serverIp, REL_VERSION=pre_build)
                    logger.info(params)
                    pythonJenkins_obj = PythonJenkins(jenkinsJob_obj.name, params)
                    console = pythonJenkins_obj.deploy()
                    params = {}
                    # 判断Jenkins项目执行是否成功
                    isFinished = console.find("Finished")
                    while isFinished == -1:
                        time.sleep(15)
                        console = pythonJenkins_obj.isFinished()
                        isFinished = console.find("Finished")
                    isSuccess = console.find("Finished: SUCCESS")
                    if isSuccess == -1:
                        logger.error("jenkins: %s, server: %s,【任务发布-事务回滚】失败" %
                                     (jenkinsJob_obj.name, serverInfo_obj[j].serverInfo.name))
                        rollbackError.append(jenkinsJob_obj.name)
                    else:
                        logger.info("jenkins: %s, server: %s,【任务发布-事务回滚】成功" %
                                    (jenkinsJob_obj.name, serverInfo_obj[j].serverInfo.name))
            except IndexError:
                logger.error("%s已是首发版本，无法回退" % jenkinsJob_obj.name)

            return rollbackError

    # 任务回滚
    def transRollback(self):
        params = {}
        rollbackError = []
        taskDetail_obj = self.taskDetail_obj
        priority = self.priority
        trans_taskDetail_obj = taskDetail_obj.filter(priority__lte=priority).order_by('priority')
        for i in range(len(trans_taskDetail_obj)):
            buildId = trans_taskDetail_obj[i].packageId
            jenkinsJob_obj = trans_taskDetail_obj[i].proJenkins
            param = eval(jenkinsJob_obj.param)
            serverInfo_obj = models.jenkinsPro_serverInfo.objects.filter(proJenkins=jenkinsJob_obj)
            for s in range(len(serverInfo_obj)):
                params.update(param)
                params.update(SERVER_IP=serverInfo_obj[s].serverInfo.serverIp, REL_VERSION=buildId)
                logger.info(params)
                pyJenkins_obj = PythonJenkins(jenkinsJob_obj.name, params)
                console = pyJenkins_obj.deploy()
                params = {}
                # 判断Jenkins项目执行是否成功
                isFinished = console.find("Finished")
                while isFinished == -1:
                    time.sleep(15)
                    console = pyJenkins_obj.isFinished()
                    isFinished = console.find("Finished")
                isSuccess = console.find("Finished: SUCCESS")
                if isSuccess == -1:
                    logger.error("jenkins: %s, server: %s,【任务回滚-事务回滚】失败" %
                                 (jenkinsJob_obj.name, serverInfo_obj[s].serverInfo.name))
                    rollbackError.append(jenkinsJob_obj.name)
                else:
                    logger.info("jenkins: %s, server: %s,【任务回滚-事务回滚】成功" %
                                (jenkinsJob_obj.name, serverInfo_obj[s].serverInfo.name))

        return rollbackError
