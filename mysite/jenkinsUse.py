import jenkins
from mysite import models
import time
import logging

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


# 事务回滚
class Transaction:
    def __init__(self, taskDetail_obj, taskDetail_all_obj, priority):
        self.taskDetail_obj = taskDetail_obj
        self.taskDetail_all_obj = taskDetail_all_obj
        self.priority = priority

    # 任务发布
    def transRunBuild(self):
        param = {}
        taskDetail_obj = self.taskDetail_obj
        taskDetail_all_obj = self.taskDetail_all_obj
        priority = self.priority
        trans_taskDetail_obj = taskDetail_obj.filter(priority__lte=priority).order_by('priority')
        rollbackError = []
        for i in range(len(trans_taskDetail_obj)):
            buildId = trans_taskDetail_obj[i].buildID
            jenkinsJob_obj = trans_taskDetail_obj[i].jenkinsJob
            healthPort = jenkinsJob_obj.healthPort
            applicationName = jenkinsJob_obj.applicationName
            try:
                pre_build = \
                    taskDetail_all_obj.filter(jenkinsJob=jenkinsJob_obj, buildID__lt=buildId).order_by('-buildID')[
                        0].buildID
                serverInfo_obj = models.jenkinsJob_serverInfo.objects.filter(jenkinsJob=jenkinsJob_obj)
                for j in range(len(serverInfo_obj)):
                    if healthPort == '1':
                        param.update(RELEASE="deploy", SERVER_IP=serverInfo_obj[j].serverInfo.serverIp,
                                     REL_VERSION=pre_build, APPLICATION_NAME=applicationName)
                    else:
                        param.update(RELEASE="deploy", SERVER_IP=serverInfo_obj[j].serverInfo.serverIp,
                                     REL_VERSION=pre_build,
                                     APP_HEALTH_PORT=healthPort, APPLICATION_NAME=applicationName)
                    logger.info(param)
                    pythonJenkins_obj = PythonJenkins(jenkinsJob_obj.name, param)
                    console = pythonJenkins_obj.deploy()
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
        param = {}
        rollbackError = []
        taskDetail_obj = self.taskDetail_obj
        priority = self.priority
        trans_taskDetail_obj = taskDetail_obj.filter(priority__lte=priority).order_by('priority')
        for i in range(len(trans_taskDetail_obj)):
            buildId = trans_taskDetail_obj[i].buildID
            jenkinsJob_obj = trans_taskDetail_obj[i].jenkinsJob
            healthPort = jenkinsJob_obj.healthPort
            applicationName = jenkinsJob_obj.applicationName
            serverInfo_obj = models.jenkinsJob_serverInfo.objects.filter(jenkinsJob=jenkinsJob_obj)
            for s in range(len(serverInfo_obj)):
                if healthPort == '1':
                    param.update(RELEASE="deploy", SERVER_IP=serverInfo_obj[s].serverInfo.serverIp, REL_VERSION=buildId,
                                 APPLICATION_NAME=applicationName)
                else:
                    param.update(RELEASE="deploy", SERVER_IP=serverInfo_obj[s].serverInfo.serverIp, REL_VERSION=buildId,
                                 APP_HEALTH_PORT=healthPort, APPLICATION_NAME=applicationName)
                logger.info(param)
                pyJenkins_obj = PythonJenkins(jenkinsJob_obj.name, param)
                console = pyJenkins_obj.deploy()
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
