#!/usr/bin/python3
# -*- coding:utf-8 -*-
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection, connections
from mysite.functions import TimeChange, fileObj
from mysite import models
import datetime
from mysite.jenkinsUse import PythonJenkins, Transaction
from django.views.decorators.csrf import csrf_exempt
import uuid
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
from apscheduler.jobstores.base import ConflictingIdError

# 添加全局变量，记录日志
logger = logging.getLogger('log')

# 定时获取uat_build_number
scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")
try:
    @register_job(scheduler, "interval", seconds=60)
    def get_uat_buildId():
        jenkins_job_obj = models.jenkins_job.objects.all()
        print('=======================================')
        print(len(jenkins_job_obj))
        for i in range(len(jenkins_job_obj)):
            uat_job_name = "UAT-" + jenkins_job_obj[i].applicationName
            param = {}
            python_jenkins_obj = PythonJenkins(uat_job_name, param)
            uat_buildId = python_jenkins_obj.look_uat_buildId()
            print(jenkins_job_obj[i].name, uat_buildId)
            if uat_buildId:
                uat_jenkins_job_obj = models.uat_jenkins_job.objects.filter(jenkins_job=jenkins_job_obj[i])
                repetition = "1"
                for j in range(len(uat_jenkins_job_obj)):
                    if uat_buildId == uat_jenkins_job_obj[j].uat_buildId:
                        repetition = "0"
                        break
                if repetition == "1":
                    uat_jenkins_job_obj_new = models.uat_jenkins_job(name=uat_job_name, jenkins_job=jenkins_job_obj[i],
                                                                     uat_buildId=uat_buildId)
                    uat_jenkins_job_obj_new.save()
                    logger.info(
                        "uat_jenkins_job: %s, uat_buildId: %d,已存储" % (uat_jenkins_job_obj[j].name, uat_buildId))
                else:
                    logger.info(
                        "uat_jenkins_job: %s, uat_buildId: %d, 已存在" % (uat_jenkins_job_obj[j].name, uat_buildId))


    register_events(scheduler)
    scheduler.start()
except ConflictingIdError as e:
    print(e)
    scheduler.remove_all_jobs()
    scheduler.start()


def index(request):
    template = get_template('index.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


@login_required
def showTask(request):
    # 使用了js分页技术，无须做分页
    jenkins_tasks = models.TaskDetail.objects.all()
    taskBar_obj = models.TaskBar.objects.all()

    template = get_template('showTask.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 控制任务启用开关
@login_required
@csrf_exempt
def ajax_showTask(request):
    onOff = request.POST.get('onOff')
    taskId = request.POST.get('id')
    print(onOff, taskId)
    if taskId:
        task = models.TaskBar.objects.get(id=taskId)
        task.onOff = onOff
        task.save()

        return HttpResponse(task)


@login_required
def taskDetail(request):
    taskId = request.GET.get('tid')
    if taskId:
        taskHistory_obj = models.TaskHistory.objects.filter(taskBar__id=taskId)
        taskBar_obj = models.TaskBar.objects.filter(id=taskId)[0]
        taskDetail_obj = models.TaskDetail.objects.filter(taskBar=taskBar_obj).order_by('priority')

    template = get_template('taskDetail.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


@login_required
def CreateTask(request):
    jenkins_jobs = models.jenkins_job.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        jenkinsJobs = request.POST.getlist('jenkinsJob')
        buildId = request.POST.getlist('buildId')
        createDate = datetime.datetime.now()
        createUser = request.user
        taskBar_obj = models.TaskBar(name=title, createUser=createUser, createDate=createDate, onOff=1)
        taskBar_obj.save()

        for i in range(len(jenkinsJobs)):
            jenkinsJob_obj = models.jenkins_job.objects.get(name=jenkinsJobs[i])
            taskDetail_obj = models.TaskDetail(jenkinsJob=jenkinsJob_obj, taskBar=taskBar_obj, buildID=buildId[i],
                                               createDate=createDate, createUser=createUser, priority=i)
            taskDetail_obj.save()

        return HttpResponseRedirect('/showTask')

    template = get_template('showJob.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 获取uat_buildId
@login_required
def ajax_load_buildIds(request):
    if request.method == 'GET':
        jenkins_job_name = request.GET.get('jenkins_job_name')
        if jenkins_job_name:
            jenkins_job = models.jenkins_job.objects.get(name=jenkins_job_name)
            uat_jenkins_jobs = models.uat_jenkins_job.objects.filter(jenkins_job=jenkins_job).order_by("-id")
            data = list(uat_jenkins_jobs.values("uat_buildId"))
            result = json.dumps(data)
            print(result)
    return HttpResponse(result, "application/json")


@login_required
def fileKeySearch(request):
    if request.method == 'POST':
        account = request.POST.get('account')
        if account:
            cursor = connections['jlb-app'].cursor()
            query = "select fileKey,createTime from jlbapp.t_parts_problem_collect where account = %s"
            cursor.execute(query, account)
            allData = cursor.fetchall()
            fileKeyList = []
            createDateList = []
            for i in range(len(allData)):
                allDataList = list(allData[i])
                fileKey = allDataList[0]
                dateObj = TimeChange(allDataList[1])
                createDate = dateObj.ChangeFormat()
                # obj = fileObj(fileKey, createDate)
                fileKeyList.append(fileKey)
                createDateList.append(createDate)
                # dic.update(fileKeyList=createDateList)
            obj = fileObj(fileKeyList, createDateList)
            # print(obj.fileKeyList, obj.createDateList)
            # for x in obj:
            #     print(x[0], x[1])
            #     # print(x.fileKeyList, x.createDateList)
            cursor.close()
        else:
            messages.warning(request, '输入有误，请重新输入！')
    else:
        pass
    template = get_template('ioskey.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 任务执行
@csrf_exempt
@login_required
def ajax_runBuild(request):
    if request.method == 'POST':
        taskId = request.POST.get('id')
        if taskId:
            taskDetail_all_obj = models.TaskDetail.objects.all()
            taskDetail_obj = models.TaskDetail.objects.filter(taskBar=taskId).order_by('priority')
            taskBar_obj = models.TaskBar.objects.get(id=taskId)
            param = {}
            info = {'build': 'SUCCESS'}
            rollbackError = []
            uid = str(uuid.uuid4())
            suid = ''.join(uid.split('-'))
            for i in range(len(taskDetail_obj)):
                buildId = taskDetail_obj[i].buildID
                jenkinsJob_obj = taskDetail_obj[i].jenkinsJob
                healthPort = jenkinsJob_obj.healthPort
                applicationName = jenkinsJob_obj.applicationName
                serverInfo_obj = models.JenkinsJob_ServerInfo.objects.filter(jenkinsJob=jenkinsJob_obj)
                if serverInfo_obj and info['build'] == 'SUCCESS':
                    # if info['build'] == 'SUCCESS':
                    for j in range(len(serverInfo_obj)):
                        if healthPort == '1':
                            param.update(RELEASE="deploy", SERVER_IP=serverInfo_obj[j].serverInfo.serverIp,
                                         REL_VERSION=buildId,
                                         APPLICATION_NAME=applicationName)
                        else:
                            param.update(RELEASE="deploy", SERVER_IP=serverInfo_obj[j].serverInfo.serverIp,
                                         REL_VERSION=buildId,
                                         APP_HEALTH_PORT=healthPort, APPLICATION_NAME=applicationName)
                        pythonJenkins_obj = PythonJenkins(jenkinsJob_obj.name, param)
                        console = pythonJenkins_obj.deploy()
                        isFinished = console.find("Finished")
                        while isFinished == -1:
                            time.sleep(15)
                            console = pythonJenkins_obj.isFinished()
                            isFinished = console.find("Finished")
                        isSuccess = console.find("Finished: SUCCESS")
                        if isSuccess == -1:
                            # 此处插入事务回滚
                            logger.info("taskId: %s, job: %s ,build: %s, server: %s, 发布出错，执行回滚" %
                                        (taskId, jenkinsJob_obj.name, buildId, serverInfo_obj[j].serverInfo.name))
                            priority = taskDetail_obj[i].priority
                            transaction_obj = Transaction(taskDetail_obj, taskDetail_all_obj, priority)
                            rollbackError = transaction_obj.transRunBuild()
                            info['jenkinsName'] = jenkinsJob_obj.name
                            info['serverName'] = serverInfo_obj[j].serverInfo.name
                            info['build'] = 'Fail'
                            break
                        else:
                            operateHistory_obj = models.OperationHistory(console_opt=console, type=1,
                                                                         operateUser=request.user,
                                                                         server=serverInfo_obj[j].serverInfo,
                                                                         taskDetail=taskDetail_obj[i], suuid=suid)
                            operateHistory_obj.save()
                            logger.info("taskId: %s, job: %s ,server: %s, 发布记录存储完成" %
                                        (taskId, jenkinsJob_obj.name, serverInfo_obj[j].serverInfo.name))
                else:
                    # 当出现发布失败后，立即终止后面的发布
                    logger.info("发布任务: %s,服务器不存在，或者发布失败，终止所有发布。" % taskId)
                    break

            if info['build'] == 'SUCCESS':
                taskHistory_obj = models.TaskHistory(type=1, operateUser=request.user, taskBar=taskBar_obj, suuid=suid)
                taskHistory_obj.save()
                res = "任务编号: %s,发布成功" % taskBar_obj.id
                logger.info(res)
                return HttpResponse("done")
            else:
                if len(rollbackError) > 0:
                    res = "项目：%s,所在服务器：%s,发布失败,发布事务回退！--回退失败，请手动处理！" % (info['jenkinsName'], info['serverName'])
                else:
                    res = "项目：%s,所在服务器：%s,发布失败,发布事务回退！--回退成功！" % (info['jenkinsName'], info['serverName'])
                logger.info(res)
                return HttpResponse(res)
        else:
            res = "找不到对应的任务"
            logger.error(res)
            return HttpResponse(res)


# 任务回滚
@csrf_exempt
def ajax_rollBack(request):
    if request.method == 'POST':
        taskId = request.POST.get('id')
        if taskId:
            taskBar_obj = models.TaskBar.objects.get(id=taskId)
            taskDetail_obj = models.TaskDetail.objects.filter(taskBar=taskBar_obj).order_by('priority')
            taskDetail_all_obj = models.TaskDetail.objects.all()
            param = {}
            rollbackError = []
            info = {'build': 'SUCCESS'}
            uid = str(uuid.uuid4())
            suid = ''.join(uid.split('-'))
            for i in range(len(taskDetail_obj)):
                buildId = taskDetail_obj[i].buildID
                jenkinsJob_obj = taskDetail_obj[i].jenkinsJob
                applicationName = jenkinsJob_obj.applicationName
                healthPort = jenkinsJob_obj.healthPort
                try:
                    pre_build = \
                        taskDetail_all_obj.filter(jenkinsJob=jenkinsJob_obj, buildID__lt=buildId).order_by('-buildID')[
                            0].buildID
                    serverInfo_obj = models.JenkinsJob_ServerInfo.objects.filter(jenkinsJob=jenkinsJob_obj)
                    if serverInfo_obj and info['build'] == 'SUCCESS':
                        for j in range(len(serverInfo_obj)):
                            if healthPort == '1':
                                param.update(RELEASE="deploy", SERVER_IP=serverInfo_obj[j].serverInfo.serverIp,
                                             REL_VERSION=pre_build, APPLICATION_NAME=applicationName)
                            else:
                                param.update(RELEASE="deploy", SERVER_IP=serverInfo_obj[j].serverInfo.serverIp,
                                             REL_VERSION=pre_build,
                                             APP_HEALTH_PORT=healthPort, APPLICATION_NAME=applicationName)
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
                                # 此处插入事务回滚
                                logger.info("taskId: %s, job: %s ,pre_buildId: %s, server: %s, 回滚出错，执行回退" %
                                            (taskId, jenkinsJob_obj.name, pre_build, serverInfo_obj[j].serverInfo.name))
                                priority = taskDetail_obj[i].priority
                                transaction_obj = Transaction(taskDetail_obj, taskDetail_all_obj, priority)
                                rollbackError = transaction_obj.transRollback()
                                info['jenkinsName'] = jenkinsJob_obj.name
                                info['serverName'] = serverInfo_obj[j].serverInfo.name
                                info['build'] = 'Fail'
                                break
                            else:
                                operateHistory_obj = models.OperationHistory(console_opt=console, type=2,
                                                                             operateUser=request.user,
                                                                             server=serverInfo_obj[j].serverInfo,
                                                                             taskDetail=taskDetail_obj[i])
                                operateHistory_obj.save()
                                logger.info("taskId: %s, job: %s ,server: %s, 回滚记录存储完成" %
                                            (taskId, jenkinsJob_obj.name, serverInfo_obj[j].serverInfo.name))
                    else:
                        # 当出现发布失败后，立即终止后面的发布
                        logger.info("回滚任务: %s,服务器不存在，或者回滚失败，终止所有回滚。" % taskId)
                        break
                except IndexError:
                    logger.error("%s已是首发版本，无法回退" % jenkinsJob_obj.name)

            if info['build'] == 'SUCCESS':
                taskHistory_obj = models.TaskHistory(type=2, operateUser=request.user, taskBar=taskBar_obj, suuid=suid)
                taskHistory_obj.save()
                res = "任务编号: %s, 回滚成功" % taskId
                logger.info(res)
                return HttpResponse("done")
            else:
                if len(rollbackError) > 0:
                    res = "项目：%s,所在服务器：%s,回滚失败,回滚事务回退！ --事务回退失败，请手动处理！" % (info['jenkinsName'], info['serverName'])
                else:
                    res = "项目：%s,所在服务器：%s,回滚失败，回滚事务回退！ --事务回退成功！" % (info['jenkinsName'], info['serverName'])
                logger.info(res)
                return HttpResponse(res)
        else:
            res = "找不到对应的任务"
            logger.error(res)
            return HttpResponse("找不到对应的任务")


# 查看控制台信息
@login_required
def console_opt(request, uid):
    print(uid)
    if uid:
        operateHistory_obj = models.OperationHistory.objects.filter(suuid=uid)

    template = get_template('console_opt.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)
