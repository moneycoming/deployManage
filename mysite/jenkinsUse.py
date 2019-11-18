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
        info = {}
        try:
            next_build_number = server.get_job_info(jenkinsJob)['nextBuildNumber']
            server.build_job(jenkinsJob, param)
            time.sleep(15)
            consoleOpt = server.get_build_console_output(jenkinsJob, next_build_number)
            isSuccess = consoleOpt.find("Finished: SUCCESS")
            isFailure = consoleOpt.find("Finished: FAILURE")
            while isSuccess == -1 and isFailure == -1:
                time.sleep(5)
                consoleOpt = server.get_build_console_output(jenkinsJob, next_build_number)
                isSuccess = consoleOpt.find("Finished: SUCCESS")
                isFailure = consoleOpt.find("Finished: FAILURE")
            info['buildId'] = next_build_number
            info['consoleOpt'] = consoleOpt
        except jenkins.NotFoundException:
            logger.error("jenkins项目未找到，请检查项目是否存在")
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
