# -- coding:UTF-8 --
import jenkins
from mysite import models
import time
import logging
import os
import subprocess
import re

# 添加全局变量，记录日志
logger = logging.getLogger('log')


class pythonJenkins:
    def __init__(self, jenkinsJob, param):
        self.jenkinsJob = jenkinsJob
        self.param = param
        token = models.paramConfig.objects.get(name='jenkins_token')
        url = models.paramConfig.objects.get(name='jenkins_url')
        user = models.paramConfig.objects.get(name='jenkins_user')
        self.server = jenkins.Jenkins(url.param, username=user.param, password=token.param)

    def deploy(self):
        jenkinsJob = self.jenkinsJob
        param = self.param
        server = self.server
        status = True
        try:
            server.build_job(jenkinsJob, param)
        except jenkins.NotFoundException:
            logger.error("jenkins项目未找到，请检查项目是否存在")
            status = False

        return status

    def stop_build(self, number):
        token = models.paramConfig.objects.get(name='jenkins_token')
        jenkins_url = models.paramConfig.objects.get(name='jenkins_url')
        user = models.paramConfig.objects.get(name='jenkins_user')
        jenkinsJob = self.jenkinsJob
        server = self.server
        url = "http://" + user.param + ":" + token.param + "@" + jenkins_url.param.split("//")[
            1] + "job/" + jenkinsJob + "/" + str(number) + "/stop"
        info = dict()
        try:
            subprocess.check_output(['curl', "-X", "POST", url])
            consoleOpt = server.get_build_console_output(jenkinsJob, number)
            isSuccess = consoleOpt.find("Finished: SUCCESS")
            isFailure = consoleOpt.find("Finished: FAILURE")
            isAbort = consoleOpt.find("Finished: ABORTED")
            while isSuccess == -1 and isFailure == -1 and isAbort == -1:
                time.sleep(1)
                consoleOpt = server.get_build_console_output(jenkinsJob, number)
                isSuccess = consoleOpt.find("Finished: SUCCESS")
                isFailure = consoleOpt.find("Finished: FAILURE")
                isAbort = consoleOpt.find("Finished: ABORTED")
            info['consoleOpt'] = consoleOpt
        except subprocess.CalledProcessError:
            logger.error("job %s终止失败！" % jenkinsJob)
            info['consoleOpt'] = None

        return info

    def realConsole(self):
        jenkinsJob = self.jenkinsJob
        server = self.server
        try:
            next_build_number = server.get_job_info(jenkinsJob)['nextBuildNumber']
            return next_build_number
        except jenkins.NotFoundException:
            logger.error("jenkins项目未找到，请检查项目是否存在")

    def get_building_info(self):
        jenkinsJob = self.jenkinsJob
        server = self.server
        jobs = server.get_running_builds()
        searchedJob = dict()
        for i in range(len(jobs)):
            if jobs[i]['name'] == jenkinsJob:
                searchedJob = jobs[i]
                break
        if searchedJob:
            return searchedJob

    def get_build_console(self, number):
        jenkinsJob = self.jenkinsJob
        server = self.server
        info = dict()
        info['jenkinsJob'] = True
        try:
            consoleOpt = server.get_build_console_output(jenkinsJob, number)
            isSuccess = consoleOpt.find("Finished: SUCCESS")
            isFailure = consoleOpt.find("Finished: FAILURE")
            isAbort = consoleOpt.find("Finished: ABORTED")
            while isSuccess == -1 and isFailure == -1 and isAbort == -1:
                time.sleep(1)
                consoleOpt = server.get_build_console_output(jenkinsJob, number)
                isSuccess = consoleOpt.find("Finished: SUCCESS")
                isFailure = consoleOpt.find("Finished: FAILURE")
                isAbort = consoleOpt.find("Finished: ABORTED")
            info['consoleOpt'] = consoleOpt
        except jenkins.NotFoundException:
            logger.error("jenkins项目未找到，请检查项目是否存在")
            info['jenkinsJob'] = False

        return info


class projectBean:
    def __init__(self, project, gitCmd):
        self.project = project
        self.gitCmd = gitCmd

    def look_branch(self):
        project = self.project
        gitCmd = self.gitCmd
        project_dir = project.project_dir
        os.chdir(project_dir)
        try:
            subprocess.check_output([gitCmd, "remote", "update", "--prune"])
        except subprocess.CalledProcessError:
            logger.info("项目%s已是最新信息，无须更新" % project.name)

        branch_byte = subprocess.check_output(["git", "branch", "-r"])
        branch_str = str(branch_byte, 'utf-8')
        # branch_str = str(branch_byte)
        branches = branch_str.split('\n')
        branch_list = []
        for branch in branches[:-1]:
            match = re.match(r"uat", branch.lstrip('* origin').lstrip('/'))
            if not match:
                branch_list.append(branch.lstrip('* origin').lstrip('/'))

        if 'master' in branch_list:
            branch_list.remove('master')
        if 'HEAD -> origin/master' in branch_list:
            branch_list.remove('HEAD -> origin/master')
        if 'pre-online' in branch_list:
            branch_list.remove('pre-online')

        return branch_list

    def countDeploySum(self, flag, order):
        total = 0
        project_plans = self.project.filter(order__gte=order)
        for i in range(len(project_plans)):
            project_obj = project_plans[i].project
            project_servers = models.project_server.objects.filter(project=project_obj)
            for j in range(len(project_servers)):
                if project_servers[j].server.type == flag:
                    total += 1
        return total

    def countDeploySum2(self, flag, order):
        total = 0
        project_plans = self.project.filter(order__lte=order)
        for i in range(len(project_plans)):
            project_obj = project_plans[i].project
            project_servers = models.project_server.objects.filter(project=project_obj)
            for j in range(len(project_servers)):
                if project_servers[j].server.type == flag:
                    total += 1
        return total

    def lookFailPoint(self):
        project_plans = self.project

        order = 0
        for i in range(len(project_plans)):
            if project_plans[i].failPoint:
                order = project_plans[i].order

        return order
