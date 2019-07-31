#!/usr/bin/python3
# -*- coding:utf-8 -*-
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection, connections
from mysite.functions import TimeChange, fileObj, branch
from mysite import models
import datetime
from mysite.jenkinsUse import PythonJenkins, Transaction, projectBean
from django.views.decorators.csrf import csrf_exempt
import uuid
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
from apscheduler.jobstores.base import ConflictingIdError
from mysite.dataAnalysis import DataAnalysis
from django.core.mail import send_mail
from django.contrib.auth.models import User


# 添加全局变量，记录日志
logger = logging.getLogger('log')

# 定时获取uat_build_number
scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")
try:
    @register_job(scheduler, "interval", seconds=60)
    def get_uat_buildId():
        projects = models.project.objects.all()
        for i in range(len(projects)):
            uat_job_name = "UAT-" + projects[i].applicationName
            param = {}
            python_jenkins_obj = PythonJenkins(uat_job_name, param)
            uat_buildId = python_jenkins_obj.look_uat_buildId()
            if uat_buildId:
                uat_jenkinsJobs = models.uat_jenkinsJob.objects.filter(project=projects[i])
                repetition = "1"
                for j in range(len(uat_jenkinsJobs)):
                    if uat_buildId == uat_jenkinsJobs[j].buildId:
                        repetition = "0"
                        logger.info(
                            "uat_jenkins_job: %s, uat_buildId: %d, 已存在" % (uat_jenkinsJobs[j].name, uat_buildId))
                        break
                if repetition == "1":
                    uat_jenkinsJob_Model = models.uat_jenkinsJob(name=uat_job_name, project=projects[i],
                                                                 buildId=uat_buildId)
                    uat_jenkinsJob_Model.save()
                    logger.info(
                        "uat_jenkins_job: %s, uat_buildId: %d,已存储" % (uat_job_name, uat_buildId))


    @register_job(scheduler, "interval", seconds=3600)
    def get_branch_info():
        projects = models.project.objects.all()
        for k in range(len(projects)):
            models.branch.objects.filter(project=projects[k]).delete()
            projectBean_obj = projectBean(projects[k])
            branchList = projectBean_obj.look_branch()
            for i in range(len(branchList)):
                branchModel = models.branch(name=branchList[i], project=projects[k])
                branchModel.save()
                logger.info("jenkins_job: %s, 分支: %s" % (projects[k].name, branchList[i]))


    register_events(scheduler)
    scheduler.start()
except ConflictingIdError as e:
    scheduler.remove_all_jobs()
    scheduler.start()

# 添加全局变量，邮件功能
mail_to = ['hepengchong@zhixuezhen.com']
mail_from = 'zhumingjie@zhixuezhen.com'


# 首页及任务信息展示
def index(request):
    plans = models.deployPlan.objects.all()
    productions = models.production.objects.all()
    monthAllPlan = []
    for i in range(len(productions)):
        dataAnalysis_obj = DataAnalysis(productions[i])
        planCounts = dataAnalysis_obj.totalCounts()
        productions.filter(id=productions[i].id).update(planCounts=planCounts)
        monthPerPlan = []
        productionName = [productions[i].name]
        monthMixPlan = []
        for j in range(1, datetime.datetime.now().month + 1):
            monthCounts = dataAnalysis_obj.monthCounts(j)
            monthPerPlan.append(monthCounts)
        monthMixPlan.append(productionName)
        monthMixPlan.append(monthPerPlan)
        monthAllPlan.append(monthMixPlan)
        productionName = []

    template = get_template('index.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 产品发布类型统计图
@login_required
def productionKindChart(request):
    productionId = request.GET.get('pid')
    if productionId:
        kinds = models.kind.objects.all()
        production = models.production.objects.get(id=productionId)
        dataAnalysis_obj = DataAnalysis(production)
        monthAllKind = []
        productionName = production.name
        for i in range(len(kinds)):
            kindName = [kinds[i].name]
            monthPerKind = []
            monthMixKind = []
            for k in range(1, datetime.datetime.now().month + 1):
                monthCounts = dataAnalysis_obj.monthKindCounts(k, kinds[i])
                monthPerKind.append(monthCounts)
            monthMixKind.append(kindName)
            monthMixKind.append(monthPerKind)
            monthAllKind.append(monthMixKind)

    template = get_template('productionKindChart.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


@login_required
def showPlan(request):
    plans = models.deployPlan.objects.all()

    template = get_template('showPlan.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


@login_required
def createPlan(request):
    productions = models.production.objects.all()
    kinds = models.kind.objects.all()
    users = User.objects.all()
    projects = models.project.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        desc = request.POST.get('desc')
        production = request.POST.get('production')
        kind = request.POST.get('kind')
        memberList = request.POST.getlist('member')
        createDate = datetime.datetime.now()
        createUser = request.user
        production_obj = models.production.objects.get(name=production)
        kind_obj = models.kind.objects.get(name=kind)

        plan_obj = models.deployPlan(title=title, description=desc, kind=kind_obj, production=production_obj,
                                     createUser=createUser, createDate=createDate)
        plan_obj.save()

        return HttpResponseRedirect('/showPlan')

    template = get_template('createPlan.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


@login_required
def showTask(request):
    # 使用了js分页技术，无须做分页
    jenkins_tasks = models.taskDetail.objects.all()
    taskBar_obj = models.task.objects.all()

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
        task = models.task.objects.get(id=taskId)
        task.onOff = onOff
        task.save()

        return HttpResponse(task)


# 任务删除
@login_required
@csrf_exempt
def ajax_deleteTask(request):
    taskId = request.POST.get('id')
    if taskId:
        task = models.task.objects.get(id=taskId)
        task.delete()

        return HttpResponse("success")


# 计划删除
@login_required
@csrf_exempt
def ajax_deletePlan(request):
    planId = request.POST.get('id')
    if planId:
        plan = models.deployPlan.objects.get(id=planId)
        plan.delete()

        return HttpResponse("success")


@login_required
def planDetail(request):
    planId = request.GET.get('pid')
    if planId:
        plan_obj = models.deployPlan.objects.get(id=planId)
        tasks = models.task.objects.filter(plan__id=planId)

    template = get_template('planDetail.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


@login_required
def taskDetail(request):
    taskId = request.GET.get('tid')
    if taskId:
        taskHistory = models.taskHistory.objects.filter(task__id=taskId)
        task = models.task.objects.get(id=taskId)
        taskDetails = models.taskDetail.objects.filter(task=task).order_by('priority')
        sequences = models.sequence.objects.filter(task=task).order_by('priority')
        lastNum = len(sequences) + 1

    template = get_template('taskDetail.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


@login_required
@csrf_exempt
def ajax_taskImplement(request):
    implement = request.POST.get('implemented')
    sequenceId = request.POST.get('id')
    remark = request.POST.get('remark')
    user = request.user
    executeDate = datetime.datetime.now()
    info = []
    if sequenceId:
        sequence = models.sequence.objects.get(id=sequenceId)
        if user.has_perm('projectDeploy'):
            sequence.implemented = implement
            sequence.remarks = remark
            sequence.executor = user
            sequence.executeDate = executeDate
            sequence.save()
            info.append('implemented')
            info.append(remark)
        else:
            info.append("no_role")
        infoJson = json.dumps(info)

        return HttpResponse(infoJson, "application/json")


# 代码自动合并
@login_required
@csrf_exempt
def ajax_autoCodeMerge(request):
    checked = request.POST.get('checked')
    taskId = request.POST.get('id')
    remark = request.POST.get('remark')
    checkUser = request.user
    checkDate = datetime.datetime.now()
    result = []
    if taskId:
        if checkUser.has_perm('mysite.can_check_project'):
            task = models.task.objects.get(id=taskId)
            task.checkUser = checkUser
            task.checkDate = checkDate
            task.checked = checked
            task.remark = remark
            task.save()
            taskDetails = models.taskDetail.objects.filter(task=task)
            mergeTo = "master"
            conflictBranches = []
            for i in range(len(taskDetails)):
                jenkinsJob = taskDetails[i].proJenkins
                mergeFrom = taskDetails[i].branch
                project_dir = jenkinsJob.project.project_dir
                branch_obj = branch(project_dir)
                status = branch_obj.merge(mergeFrom, mergeTo, status=False)
                if not status:
                    conflictBranches.append(jenkinsJob.name)

            if len(conflictBranches) == 0:
                res = "所有项目的分支合并完成！！"
            else:
                res = "以下项目%s的分支合并冲突，请手动处理！" % conflictBranches
            result.append(res)
            result.append(remark)
            resultJson = json.dumps(result)
            send_mail(task.name, res, mail_from, mail_to, fail_silently=False)

            return HttpResponse(resultJson, "application/json")
        else:
            result.append("no_role")
            res = "你没有验证部署的权限！！！"
            result.append(res)
            resultJson = json.dumps(result)
            return HttpResponse(resultJson,  "application/json")


@login_required
def createTask(request):
    user = request.user
    if user.has_perm('mysite.add_task'):
        jenkins_jobs = models.pro_jenkinsJob.objects.all()
        plans = models.deployPlan.objects.all()
        segments = models.segment.objects.all()
        if request.method == 'POST':
            title = request.POST.get('title')
            jenkinsJobs = request.POST.getlist('jenkinsJob')
            planName = request.POST.get('plan')
            plan_obj = models.deployPlan.objects.get(title=planName)
            segments = request.POST.getlist('segment')
            buildId = request.POST.getlist('buildId')
            Branch = request.POST.getlist('branch')
            createDate = datetime.datetime.now()
            createUser = request.user
            task_obj = models.task(name=title, plan=plan_obj, createUser=createUser, createDate=createDate, onOff=1)
            task_obj.save()

            for i in range(len(jenkinsJobs)):
                jenkinsJob_obj = models.pro_jenkinsJob.objects.get(name=jenkinsJobs[i])
                taskDetail_obj = models.taskDetail(proJenkins=jenkinsJob_obj, task=task_obj, packageId=buildId[i],
                                                   branch=Branch[i], priority=i)
                taskDetail_obj.save()

            for j in range(len(segments)):
                segment_obj = models.segment.objects.get(name=segments[j])
                sequence_obj = models.sequence(segment=segment_obj, task=task_obj, pre_segment=j, next_segment=j + 2,
                                               priority=j + 1)
                sequence_obj.save()

            return HttpResponseRedirect('/showTask')

    template = get_template('createTask.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 获取项目的所有分支
@login_required
def ajax_load_info(request):
    if request.method == 'GET':
        jenkins_job_name = request.GET.get('jenkins_job_name')
        if jenkins_job_name:
            project = models.project.objects.get(name=jenkins_job_name)
            branches = models.branch.objects.filter(project=project)
            branchList = list(branches.values("name"))
            branchListJson = json.dumps(branchList)

            return HttpResponse(branchListJson, "application/json")


@login_required
@csrf_exempt
def ajax_console_opt(request):
    if request.method == 'GET':
        taskId = request.GET.get('id')
        dateTime = request.GET.get('time')
        if taskId:
            taskDetails = models.taskDetail.objects.filter(task__id=taskId)
            operateHistoryList = []
            for i in range(len(taskDetails)):
                operateHistory = models.operationHistory.objects.filter(taskDetail=taskDetails[i]).filter(
                    operateTime__gte=dateTime)
                if operateHistory:
                    data = operateHistory[0].console_opt
                    operateHistoryList.append(data)

            jsonList = json.dumps(operateHistoryList)

            return HttpResponse(jsonList, "application/json")


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
    user = request.user
    if user.has_perm('mysite.can_deploy_project'):
        if request.method == 'POST':
            taskId = request.POST.get('id')
            if taskId:
                taskDetail_all_obj = models.taskDetail.objects.all()
                taskDetail_obj = models.taskDetail.objects.filter(task=taskId).order_by('priority')
                task_obj = models.task.objects.get(id=taskId)
                info = {'build': 'SUCCESS'}
                params = {}
                rollbackError = []
                uid = str(uuid.uuid4())
                suid = ''.join(uid.split('-'))
                for i in range(len(taskDetail_obj)):
                    buildId = taskDetail_obj[i].packageId
                    jenkinsJob_obj = taskDetail_obj[i].proJenkins
                    param = eval(jenkinsJob_obj.param)
                    serverInfo_obj = models.proJenkins_ServerInfo.objects.filter(proJenkins=jenkinsJob_obj)
                    if serverInfo_obj and info['build'] == 'SUCCESS':
                        for j in range(len(serverInfo_obj)):
                            params.update(param)
                            params.update(SERVER_IP=serverInfo_obj[j].serverInfo.serverIp, REL_VERSION=buildId)
                            pythonJenkins_obj = PythonJenkins(jenkinsJob_obj.name, params)
                            console = pythonJenkins_obj.deploy()
                            params = {}
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

                                operateHistory_obj = models.operationHistory(console_opt=console, type=1,
                                                                             operateUser=request.user,
                                                                             server=serverInfo_obj[j].serverInfo,
                                                                             taskDetail=taskDetail_obj[i], suuid=suid)
                                operateHistory_obj.save()
                                logger.info("taskId: %s, job: %s ,server: %s, 发布记录存储完成" % (taskId, jenkinsJob_obj.name,
                                                                                           serverInfo_obj[
                                                                                               j].serverInfo.name))
                                break

                            operateHistory_obj = models.operationHistory(console_opt=console, type=1,
                                                                         operateUser=request.user,
                                                                         server=serverInfo_obj[j].serverInfo,
                                                                         taskDetail=taskDetail_obj[i], suuid=suid)
                            operateHistory_obj.save()
                            logger.info("taskId: %s, job: %s ,server: %s, 发布记录存储完成" % (taskId, jenkinsJob_obj.name,
                                                                                       serverInfo_obj[j].serverInfo.name))
                    else:
                        # 当出现发布失败后，立即终止后面的发布
                        logger.info("发布任务: %s,服务器不存在，或者发布失败，终止所有发布。" % taskId)
                        break

                if info['build'] == 'SUCCESS':
                    taskHistory_obj = models.taskHistory(type=1, operateUser=request.user, task=task_obj, suuid=suid)
                    taskHistory_obj.save()
                    res = "任务编号: %s,发布成功" % task_obj.id
                    logger.info(res)
                    send_mail(task_obj.name, res, mail_from, mail_to, fail_silently=False)
                    return HttpResponse("done")
                else:
                    if len(rollbackError) > 0:
                        res = "项目：%s,所在服务器：%s,发布失败,发布事务回退！--回退失败，请手动处理！" % (info['jenkinsName'], info['serverName'])
                    else:
                        res = "项目：%s,所在服务器：%s,发布失败,发布事务回退！--回退成功！" % (info['jenkinsName'], info['serverName'])
                    logger.info(res)
                    send_mail(task_obj.name, res, mail_from, mail_to, fail_silently=False)
                    return HttpResponse(res)
            else:
                res = "找不到对应的任务"
                logger.error(res)
                return HttpResponse(res)
    else:
        res = "你没有发布任务的权限！！"
        return HttpResponse(res)


# 任务回滚
@csrf_exempt
def ajax_rollBack(request):
    user = request.user
    if user.has_perm('mysite.can_deploy_project'):
        if request.method == 'POST':
            taskId = request.POST.get('id')
            if taskId:
                task_obj = models.task.objects.get(id=taskId)
                taskDetail_obj = models.taskDetail.objects.filter(task=task_obj).order_by('priority')
                taskDetail_all_obj = models.taskDetail.objects.all()
                params = {}
                rollbackError = []
                info = {'build': 'SUCCESS'}
                uid = str(uuid.uuid4())
                suid = ''.join(uid.split('-'))
                for i in range(len(taskDetail_obj)):
                    buildId = taskDetail_obj[i].packageId
                    jenkinsJob_obj = taskDetail_obj[i].proJenkins
                    param = eval(jenkinsJob_obj.param)
                    try:
                        pre_build = \
                            taskDetail_all_obj.filter(proJenkins=jenkinsJob_obj, packageId__lt=buildId).order_by(
                                '-packageId')[0].buildID
                        serverInfo_obj = models.proJenkins_ServerInfo.objects.filter(proJenkins=jenkinsJob_obj)
                        if serverInfo_obj and info['build'] == 'SUCCESS':
                            for j in range(len(serverInfo_obj)):
                                params.update(param)
                                params.update(SERVER_IP=serverInfo_obj[j].serverInfo.serverIp, REL_VERSION=pre_build)
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
                                    # 此处插入事务回滚
                                    logger.info("taskId: %s, job: %s ,pre_buildId: %s, server: %s, 回滚出错，执行回退" %
                                                (taskId, jenkinsJob_obj.name, pre_build,
                                                 serverInfo_obj[j].serverInfo.name))
                                    priority = taskDetail_obj[i].priority
                                    transaction_obj = Transaction(taskDetail_obj, taskDetail_all_obj, priority)
                                    rollbackError = transaction_obj.transRollback()
                                    info['jenkinsName'] = jenkinsJob_obj.name
                                    info['serverName'] = serverInfo_obj[j].serverInfo.name
                                    info['build'] = 'Fail'
                                    break

                                operateHistory_obj = models.operationHistory(console_opt=console, type=2,
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
                    taskHistory_obj = models.taskHistory(type=2, operateUser=request.user, task=task_obj, suuid=suid)
                    taskHistory_obj.save()
                    res = "任务编号: %s, 回滚成功" % taskId
                    logger.info(res)
                    send_mail(task_obj.name, res, mail_from, mail_to, fail_silently=False)
                    return HttpResponse("done")
                else:
                    if len(rollbackError) > 0:
                        res = "项目：%s,所在服务器：%s,回滚失败,回滚事务回退！ --事务回退失败，请手动处理！" % (info['jenkinsName'], info['serverName'])
                    else:
                        res = "项目：%s,所在服务器：%s,回滚失败，回滚事务回退！ --事务回退成功！" % (info['jenkinsName'], info['serverName'])
                    logger.info(res)
                    send_mail(task_obj.name, res, mail_from, mail_to, fail_silently=False)
                    return HttpResponse(res)
            else:
                res = "找不到对应的任务"
                logger.error(res)
                return HttpResponse(res)
    else:
        res = "你没有回滚的权限！！！"
        return HttpResponse(res)


# 查看控制台信息
@login_required
def console_opt(request, uid):
    if uid:
        operateHistory_obj = models.operationHistory.objects.filter(suuid=uid)
        taskHistory = models.taskHistory.objects.get(suuid=uid)

    template = get_template('console_opt.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)
