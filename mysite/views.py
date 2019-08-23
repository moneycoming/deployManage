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
from mysite.jenkinsUse import pythonJenkins, Transaction, projectBean
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
    # @register_job(scheduler, "interval", seconds=60)
    # def get_uat_buildId():
    #     projects = models.project.objects.all()
    #     for i in range(len(projects)):
    #         uat_job_name = "UAT-" + projects[i].applicationName
    #         param = {}
    #         python_jenkins_obj = PythonJenkins(uat_job_name, param)
    #         uat_buildId = python_jenkins_obj.look_uat_buildId()
    #         if uat_buildId:
    #             uat_jenkinsJobs = models.jenkinsUat.objects.filter(project=projects[i])
    #             repetition = "1"
    #             for j in range(len(uat_jenkinsJobs)):
    #                 if uat_buildId == uat_jenkinsJobs[j].buildId:
    #                     repetition = "0"
    #                     logger.info(
    #                         "uat_jenkins_job: %s, uat_buildId: %d, 已存在" % (uat_jenkinsJobs[j].name, uat_buildId))
    #                     break
    #             if repetition == "1":
    #                 uat_jenkinsJob_Model = models.jenkinsUat(name=uat_job_name, project=projects[i],
    #                                                          buildId=uat_buildId)
    #                 uat_jenkinsJob_Model.save()
    #                 logger.info(
    #                     "uat_jenkins_job: %s, uat_buildId: %d,已存储" % (uat_job_name, uat_buildId))
    @register_job(scheduler, "interval", seconds=60)
    def get_branch_info():
        projects = models.project.objects.all()
        for k in range(len(projects)):
            branches = models.devBranch.objects.filter(project=projects[k])
            projectBean_obj = projectBean(projects[k])
            branchOld = []
            for m in range(len(branches)):
                branchOld.append(branches[m].name)
            branchNew = projectBean_obj.look_branch()
            list1 = list(set(branchOld).difference(set(branchNew)))
            list2 = list(set(branchNew).difference(set(branchOld)))
            for i in range(len(list1)):
                branches.filter(name=list1[i]).delete()
                logger.info("分支%s已删除" % list1[i])
            for j in range(len(list2)):
                branch_obj = models.devBranch(name=list2[j], project=projects[k])
                branch_obj.save()
                logger.info("分支%s已添加" % list2[j])


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
    plans = models.plan.objects.all()
    productions = models.production.objects.all()
    monthAllPlan = []
    for i in range(len(productions)):
        data_analysis_obj = DataAnalysis(productions[i])
        planCounts = data_analysis_obj.totalCounts()
        productions.filter(id=productions[i].id).update(planCounts=planCounts)
        monthPerPlan = []
        productionName = [productions[i].name]
        monthMixPlan = []
        for j in range(1, datetime.datetime.now().month + 1):
            monthCounts = data_analysis_obj.monthCounts(j)
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
    plans = models.plan.objects.all()

    template = get_template('showPlan.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


@login_required
def createPlan(request):
    productions = models.production.objects.all()
    kinds = models.kind.objects.all()
    members = models.member.objects.all()
    projects = models.project.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        desc = request.POST.get('desc')
        production = request.POST.get('production')
        kind = request.POST.get('kind')
        memberList = request.POST.getlist('member')
        projectList = request.POST.getlist('project')
        devBranchList = request.POST.getlist('devBranch')
        createDate = datetime.datetime.now()
        createUser = request.user
        productionObj = models.production.objects.get(name=production)
        kindObj = models.kind.objects.get(name=kind)

        plan_obj = models.plan(title=title, description=desc, kind=kindObj, production=productionObj,
                               createUser=createUser, createDate=createDate)
        plan_obj.save()

        for i in range(len(memberList)):
            memberObj = models.member.objects.get(name=memberList[i])
            plan_member = models.plan_member(plan=plan_obj, member=memberObj)
            plan_member.save()

        for j in range(len(projectList)):
            project_obj = models.project.objects.get(name=projectList[j])
            dev_branch_obj = models.devBranch.objects.filter(project=project_obj).get(name=devBranchList[j])
            project_plan_obj = models.project_plan(plan=plan_obj, project=project_obj, devBranch=dev_branch_obj,
                                                   order=j)
            project_plan_obj.save()

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
        plan = models.plan.objects.get(id=planId)
        plan.delete()

        return HttpResponse("success")


@login_required
def planDetail(request):
    planId = request.GET.get('pid')
    if planId:
        plan_obj = models.plan.objects.get(id=planId)
        tasks = models.task.objects.filter(plan__id=planId)
        project_plans = models.project_plan.objects.filter(plan=plan_obj)

    template = get_template('planDetail.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


@login_required
def uatDetail(request):
    planId = request.GET.get('pid')
    if planId:
        plan_obj = models.plan.objects.get(id=planId)
        project_plans = models.project_plan.objects.filter(plan=plan_obj)

    template = get_template('uatDetail.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


@login_required
def uatDeploy(request):
    projectId = request.GET.get('prjId')
    planId = request.GET.get('pid')
    if projectId and planId:
        project_obj = models.project.objects.get(id=projectId)
        plan_obj = models.plan.objects.get(id=planId)
        project_plan_obj = models.project_plan.objects.get(project=project_obj, plan=plan_obj)
        consoleOpts = models.consoleOpt.objects.filter(project=project_obj, plan=plan_obj)

    template = get_template('uatDeploy.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


@login_required
@csrf_exempt
def ajax_createUatBranch(request):
    planId = request.POST.get('pid')
    projectId = request.POST.get('prjId')
    option = request.POST.get('radio')
    if projectId and planId:
        project_obj = models.project.objects.get(id=projectId)
        plan_obj = models.plan.objects.get(id=planId)
        project_plan_obj = models.project_plan.objects.get(project=project_obj, plan=plan_obj)
        result = []
        if option == "option1":
            uatBranch = request.POST.get('uatBranch')
            status = True
        else:
            uid = str(uuid.uuid4())
            branchCode = ''.join(uid.split('-'))[0:10]
            uatBranch = "uat-"
            uatBranch += branchCode
            devBranch = project_plan_obj.devBranch
            branch_obj = branch(project_obj.project_dir)
            branch_obj.create_branch(uatBranch)
            status = branch_obj.merge_branch(devBranch.name, uatBranch)
        if status:
            project_plan_obj.uatBranch = uatBranch
            project_plan_obj.save()
            res = "预发分支：%s创建成功！" % uatBranch
        else:
            res = "预发分支创建失败！"
        result.append(res)
        result.append(uatBranch)

        return HttpResponse(json.dumps(result), "application/json")


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
                status = branch_obj.merge_branch(mergeFrom, mergeTo, status=False)
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
            return HttpResponse(resultJson, "application/json")


@login_required
def createTask(request):
    user = request.user
    if user.has_perm('mysite.add_task'):
        jenkins_jobs = models.jenkinsPro.objects.all()
        plans = models.plan.objects.all()
        segments = models.segment.objects.all()
        if request.method == 'POST':
            title = request.POST.get('title')
            jenkinsJobs = request.POST.getlist('jenkinsJob')
            planName = request.POST.get('plan')
            plan_obj = models.plan.objects.get(title=planName)
            segments = request.POST.getlist('segment')
            buildId = request.POST.getlist('buildId')
            Branch = request.POST.getlist('branch')
            createDate = datetime.datetime.now()
            createUser = request.user
            task_obj = models.task(name=title, plan=plan_obj, createUser=createUser, createDate=createDate, onOff=1)
            task_obj.save()

            for i in range(len(jenkinsJobs)):
                jenkinsJob_obj = models.jenkinsPro.objects.get(name=jenkinsJobs[i])
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
            branches = models.devBranch.objects.filter(project=project)
            branchList = list(branches.values("name"))
            branchListJson = json.dumps(branchList)

            return HttpResponse(branchListJson, "application/json")


@login_required
@csrf_exempt
def ajax_console_opt(request):
    if request.method == 'GET':
        planId = request.GET.get('pid')
        projectId = request.GET.get('prjId')
        deployTime = request.GET.get('time')
        envSort = request.GET.get('envSort')
        if projectId and planId:
            project_obj = models.project.objects.get(id=projectId)
            plan_obj = models.plan.objects.get(id=planId)
            consoleOpts = models.consoleOpt.objects.filter(project__id=projectId, plan__id=planId).filter(
                deployTime__gte=deployTime)
            logger.info("显示计划：%s,项目: %s的后台信息" % (plan_obj.title, project_obj.name))
            contentList = [envSort]
            if consoleOpts:
                for i in range(len(consoleOpts)):
                    contentList.append(consoleOpts[i].content)

            return HttpResponse(json.dumps(contentList), "application/json")


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
                    serverInfo_obj = models.jenkinsPro_serverInfo.objects.filter(proJenkins=jenkinsJob_obj)
                    if serverInfo_obj and info['build'] == 'SUCCESS':
                        for j in range(len(serverInfo_obj)):
                            params.update(param)
                            params.update(SERVER_IP=serverInfo_obj[j].serverInfo.serverIp, REL_VERSION=buildId)
                            pythonJenkins_obj = pythonJenkins(jenkinsJob_obj.name, params)
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
                                                                                       serverInfo_obj[
                                                                                           j].serverInfo.name))
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
                        serverInfo_obj = models.jenkinsPro_serverInfo.objects.filter(proJenkins=jenkinsJob_obj)
                        if serverInfo_obj and info['build'] == 'SUCCESS':
                            for j in range(len(serverInfo_obj)):
                                params.update(param)
                                params.update(SERVER_IP=serverInfo_obj[j].serverInfo.serverIp, REL_VERSION=pre_build)
                                pythonJenkins_obj = pythonJenkins(jenkinsJob_obj.name, params)
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


# 预发构建
@csrf_exempt
def ajax_uatBuild(request):
    if request.method == 'POST':
        planId = request.POST.get('pid')
        projectId = request.POST.get('prjId')
        deployTime = request.POST.get('time')
        signId = ''.join(str(uuid.uuid4()).split('-'))
        member_obj = models.member.objects.get(user=request.user)
        plan_obj = models.plan.objects.get(id=planId)
        project_obj = models.project.objects.get(id=projectId)
        project_plan_obj = models.project_plan.objects.get(plan=plan_obj, project=project_obj)
        jenkinsUat_obj = models.jenkinsUat.objects.get(project=project_obj)
        project_servers = models.project_server.objects.filter(project=project_obj)
        param = {}
        param.update(eval(jenkinsUat_obj.param))
        for i in range(len(project_servers)):
            param.update(SERVER_IP=project_servers[i].server.ip, BRANCH=project_plan_obj.uatBranch)
            logger.info("param：%s" % param)
            pythonJenkins_obj = pythonJenkins(jenkinsUat_obj.name, param)
            info = pythonJenkins_obj.deploy()
            logger.info("分支%s执行部署" % project_plan_obj.uatBranch)
            consoleOpt = info['consoleOpt']
            buildId = info['buildId']
            if info:
                isFinished = consoleOpt.find("Finished")
                while isFinished == -1:
                    time.sleep(5)
                    consoleOpt = pythonJenkins_obj.isFinished()
                    isFinished = consoleOpt.find("Finished")
                isSuccess = consoleOpt.find("Finished: SUCCESS")
                if isSuccess:
                    result = True
                    project_plan_obj.lastPackageId = buildId
                    project_plan_obj.save()
                    logger.info("分支%s部署成功" % project_plan_obj.uatBranch)
                else:
                    result = False
                    logger.error("分支%s部署失败" % project_plan_obj.uatBranch)
                consoleOpt_obj = models.consoleOpt(type=0, plan=plan_obj, project=project_obj, content=consoleOpt,
                                                   packageId=buildId, result=result, deployTime=deployTime,
                                                   deployUser=member_obj, signId=signId)
                consoleOpt_obj.save()

                return HttpResponse(result)


# 查看控制台信息
@login_required
def console_opt(request, uid):
    if uid:
        consoleOpts = models.consoleOpt.objects.filter(signId=uid)
        planId = consoleOpts[0].plan.id
        projectId = consoleOpts[0].project.id

    template = get_template('console_opt.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)
