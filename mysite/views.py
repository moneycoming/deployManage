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
from mysite.jenkinsUse import pythonJenkins, projectBean
from django.views.decorators.csrf import csrf_exempt
import uuid
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
from apscheduler.jobstores.base import ConflictingIdError
from mysite.dataAnalysis import DataAnalysis
from django.core.mail import send_mail
from dwebsocket.decorators import accept_websocket
from django.db.models import Q
from django.contrib.auth.models import User

# 添加全局变量，记录日志
logger = logging.getLogger('log')

# 定时获取uat_build_number
scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")
try:
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


# 计划主页
@login_required
def showPlan(request):
    plans = models.plan.objects.all()

    template = get_template('showPlan.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 创建计划
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
        member_obj = models.member.objects.get(user=request.user)
        productionObj = models.production.objects.get(name=production)
        kindObj = models.kind.objects.get(name=kind)

        plan_obj = models.plan(name=title, description=desc, kind=kindObj, production=productionObj,
                               createUser=member_obj, createDate=createDate)
        plan_obj.save()

        for j in range(len(projectList)):
            project_obj = models.project.objects.get(name=projectList[j])
            dev_branch_obj = models.devBranch.objects.filter(project=project_obj).get(name=devBranchList[j])
            project_plan_obj = models.project_plan(plan=plan_obj, project=project_obj, devBranch=dev_branch_obj,
                                                   order=j)
            project_plan_obj.save()
            project_servers = models.project_server.objects.filter(project=project_obj).filter(server__type=1)
            for i in range(len(project_servers)):
                deployDetail_obj = models.deployDetail(project_plan=project_plan_obj, server=project_servers[i].server)
                deployDetail_obj.save()

        return HttpResponseRedirect('/showPlan')

    template = get_template('createPlan.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 任务主页
@login_required
def showTask(request):
    # 使用了js分页技术，无须做分页
    tasks = models.task.objects.all()

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


# 计划详情
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


# 预发详情
@login_required
def uatDetail(request):
    planId = request.GET.get('pid')
    if planId:
        plan_obj = models.plan.objects.get(id=planId)
        project_plans = models.project_plan.objects.filter(plan=plan_obj)

    template = get_template('uatDetail.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 预发部署
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


# 创建预发分支
@login_required
@csrf_exempt
def ajax_createUatBranch(request):
    if request.method == 'POST':
        planId = request.POST.get('pid')
        projectId = request.POST.get('prjId')
        option = request.POST.get('radio')
        member_obj = models.member.objects.get(user=request.user)
        if projectId and planId:
            project_obj = models.project.objects.get(id=projectId)
            plan_obj = models.plan.objects.get(id=planId)
            project_plan_obj = models.project_plan.objects.get(project=project_obj, plan=plan_obj)
            production_members = models.production_member.objects.filter(production=plan_obj.production)
            isMember = False
            for m in range(len(production_members)):
                if member_obj == production_members[m].member:
                    isMember = True
            result = []
            if isMember and member_obj.user.has_perm("can_deploy_project"):
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
                    result.append(res)
                    result.append(uatBranch)
                else:
                    res = "预发分支创建失败！"
                    result.append(res)
            else:
                res = "你没有创建预发分支的权限！"
                result.append(res)

            return HttpResponse(json.dumps(result), "application/json")


# 任务详情
@login_required
def taskDetail(request):
    taskId = request.GET.get('tid')
    if taskId:
        task_obj = models.task.objects.get(id=taskId)
        project_plans = models.project_plan.objects.filter(plan=task_obj.plan).order_by('order')
        sequences = models.sequence.objects.filter(task=task_obj).order_by('priority')
        lastNum = len(sequences) + 1
        consoleOpts = models.consoleOpt.objects.filter(plan=task_obj.plan)
        show = False
        mergeStatus = True
        for i in range(len(project_plans)):
            if project_plans[i].buildStatus != 1:
                show = True
                break

        for j in range(len(project_plans)):
            if project_plans[j] == 0:
                mergeStatus = False
                break

    template = get_template('taskDetail.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 任务队列是否执行完成
@login_required
@csrf_exempt
def ajax_taskImplement(request):
    implement = request.POST.get('implemented')
    sequenceId = request.POST.get('id')
    remark = request.POST.get('remark')
    taskId = request.POST.get('taskId')
    executeDate = datetime.datetime.now()
    task_obj = models.task.objects.get(id=taskId)
    production_members = models.production_member.objects.filter(production=task_obj.plan.production)
    member_obj = models.member.objects.get(user=request.user)
    isMember = False
    for m in range(len(production_members)):
        if member_obj == production_members[m].member:
            isMember = True
    info = []
    if sequenceId:
        sequence = models.sequence.objects.get(id=sequenceId)
        if isMember and member_obj.user.has_perm('can_deploy_project'):
            sequence.implemented = implement
            sequence.remarks = remark
            sequence.executor = member_obj
            sequence.executeDate = executeDate
            sequence.save()
            info.append('implemented')
            info.append(remark)
        else:
            info.append("no_role")

        return HttpResponse(json.dumps(info), "application/json")


# 任务验收通过
@login_required
@csrf_exempt
def ajax_checkSuccess(request):
    taskId = request.POST.get('taskId')
    remark = request.POST.get('remark')
    if taskId:
        task_obj = models.task.objects.get(id=taskId)
        production_members = models.production_member.objects.filter(production=task_obj.plan.production)
        member_obj = models.member.objects.get(user=request.user)
        isMember = False
        for m in range(len(production_members)):
            if member_obj == production_members[m].member:
                isMember = True
        if isMember and member_obj.user.has_perm('can_check_project'):
            task_obj.checkUser = member_obj
            task_obj.checkDate = datetime.datetime.now()
            task_obj.checked = 1
            task_obj.remark = remark
            task_obj.save()
            res = "发布任务%s验证通过，请合并代码！" % task_obj.name
            send_mail(task_obj.name, res, mail_from, mail_to, fail_silently=False)

            return HttpResponse(json.dumps(remark), "application/json")
        else:
            return HttpResponse("no_role")


# 创建任务
@login_required
def createTask(request):
    user = request.user
    if user.has_perm('add_task'):
        plans = models.plan.objects.all()
        segments = models.segment.objects.all()
        if request.method == 'POST':
            title = request.POST.get('title')
            plan_obj = models.plan.objects.get(name=request.POST.get('plan'))
            segmentList = request.POST.getlist('segment')
            createDate = datetime.datetime.now()
            member_obj = models.member.objects.get(user=request.user)
            task_obj = models.task(name=title, plan=plan_obj, createUser=member_obj, createDate=createDate, onOff=1)
            task_obj.save()
            for i in range(len(segmentList)):
                segment_obj = models.segment.objects.get(name=segmentList[i])
                sequence_obj = models.sequence(segment=segment_obj, task=task_obj, pre_segment=i, next_segment=i + 2,
                                               priority=i + 1)
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


# 任务部署
@login_required
@accept_websocket
def ws_startDeploy(request):
    if request.is_websocket():
        for taskId in request.websocket:
            if taskId:
                uniteKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                task_obj = models.task.objects.get(id=taskId)
                project_plans = models.project_plan.objects.filter(plan=task_obj.plan).filter(
                    ~Q(buildStatus=1)).order_by('order')
                production_members = models.production_member.objects.filter(production=task_obj.plan.production)
                member_obj = models.member.objects.get(user=request.user)
                sequence_obj = models.sequence.objects.filter(task=task_obj).get(segment__isDeploy=True)
                isMember = False
                for m in range(len(production_members)):
                    if member_obj == production_members[m].member:
                        isMember = True
                buildMessages = []
                if isMember and member_obj.user.has_perm("can_deploy_project"):
                    projectBean_obj = projectBean(project_plans)
                    total = projectBean_obj.countDeploySum(1, 0)
                    buildMessages.append(total)
                    request.websocket.send(json.dumps(buildMessages))
                    cursor = []
                    for i in range(len(project_plans)):
                        project_obj = project_plans[i].project
                        deployDetails = models.deployDetail.objects.filter(project_plan=project_plans[i]).order_by(
                            '-buildStatus')
                        jenkinsPro_obj = models.jenkinsPro.objects.get(project=project_obj)
                        param = eval(jenkinsPro_obj.param)
                        relVersion = project_plans[i].lastPackageId
                        if len(cursor) == 0:
                            for j in range(len(deployDetails)):
                                params = {}
                                params.update(param)
                                server_obj = deployDetails[j].server
                                if relVersion:
                                    uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                                    params.update(SERVER_IP=server_obj.ip, REL_VERSION=relVersion)
                                    pythonJenkins_obj = pythonJenkins(jenkinsPro_obj.name, params)
                                    info = pythonJenkins_obj.deploy()
                                    for n in range(len(project_plans)):
                                        if project_plans[n].cursor:
                                            project_plans[n].cursor = False
                                            project_plans[n].save()
                                    project_plans[i].cursor = True
                                    project_plans[i].save()
                                    consoleOpt = info['consoleOpt']
                                    isSuccess = consoleOpt.find("Finished: SUCCESS")
                                    if isSuccess == -1:
                                        project_plans[i].buildStatus = 2
                                        project_plans[i].save()
                                        deployDetails[j].buildStatus = 2
                                        deployDetails[j].save()
                                        res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 发布出错!" % \
                                              (task_obj.name, project_obj.name, relVersion, server_obj.name)
                                        logger.info(res)
                                        buildMessages.append(res)
                                        buildMessages.append(uniqueKey)
                                        buildMessages.append('deploy_failed')
                                        request.websocket.send(json.dumps(buildMessages))
                                        request.websocket.close()
                                        consoleOpt_obj = models.consoleOpt(type=1, category=0, plan=task_obj.plan,
                                                                           project=project_obj, content=consoleOpt,
                                                                           packageId=relVersion, result=False,
                                                                           deployUser=member_obj, uniqueKey=uniqueKey,
                                                                           uniteKey=uniteKey)
                                        consoleOpt_obj.save()
                                        cursor.append(project_obj.id)
                                        break
                                    else:
                                        res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 发布完成！" % (
                                            task_obj.name, project_obj.name, relVersion, server_obj.name)
                                        logger.info(res)
                                        buildMessages.append(res)
                                        buildMessages.append(uniqueKey)
                                        request.websocket.send(json.dumps(buildMessages))
                                        consoleOpt_obj = models.consoleOpt(type=1, category=0, plan=task_obj.plan,
                                                                           project=project_obj, content=consoleOpt,
                                                                           packageId=relVersion, result=True,
                                                                           deployUser=member_obj,
                                                                           uniqueKey=uniqueKey, uniteKey=uniteKey)
                                        consoleOpt_obj.save()
                                        project_plans[i].buildStatus = 1
                                        project_plans[i].save()
                                        deployDetails[j].buildStatus = 1
                                        deployDetails[j].save()
                                else:
                                    cursor.append(project_obj.id)
                                    logger.info("项目：%s，没有发布版本号，请先在预发创建！" % project_obj.name)
                                    res = "项目：%s，没有发布版本号，请先在预发创建！" % project_obj.name
                                    buildMessages.append(res)
                                    buildMessages.append('no_reversion')
                                    request.websocket.send(json.dumps(buildMessages))
                                    request.websocket.close()
                                    break
                        else:
                            break
                    if len(cursor) == 0:
                        sequence_obj.implemented = True
                        sequence_obj.executor = member_obj.name
                        sequence_obj.executeDate = datetime.datetime.now()
                        sequence_obj.remarks = "已部署"
                        sequence_obj.save()
                        res = "任务：%s，部署完成！" % task_obj.name
                        buildMessages.append(res)
                        buildMessages.append('deploy_success')
                        request.websocket.send(json.dumps(buildMessages))
                        request.websocket.close()
                else:
                    buildMessages.append('no_role')
                    request.websocket.send(json.dumps(buildMessages))
                    request.websocket.close()


# 重新发布
@login_required
@accept_websocket
def ws_restartDeploy(request):
    if request.is_websocket():
        for taskId in request.websocket:
            if taskId:
                uniteKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                task_obj = models.task.objects.get(id=taskId)
                project_plans = models.project_plan.objects.filter(plan=task_obj.plan).filter(
                    ~Q(buildStatus=1)).order_by('order')
                sequence_obj = models.sequence.objects.filter(task=task_obj).get(segment__isDeploy=True)
                production_members = models.production_member.objects.filter(production=task_obj.plan.production)
                member_obj = models.member.objects.get(user=request.user)
                isMember = False
                for m in range(len(production_members)):
                    if member_obj == production_members[m].member:
                        isMember = True
                buildMessages = []
                if isMember and member_obj.user.has_perm("can_deploy_project"):
                    order = 0
                    for i in range(len(project_plans)):
                        if project_plans[i].cursor:
                            order = project_plans[i].order
                            break
                    project_plans_news = project_plans.filter(order__gte=order).order_by('order')
                    projectBean_obj = projectBean(project_plans_news)
                    total = projectBean_obj.countDeploySum(1, order)
                    buildMessages.append(total)
                    request.websocket.send(json.dumps(buildMessages))
                    cursor = []
                    for j in range(len(project_plans_news)):
                        project_obj = project_plans_news[j].project
                        deployDetails = models.deployDetail.objects.filter(project_plan=project_plans_news[j]).order_by(
                            '-buildStatus')
                        project_servers = models.project_server.objects.filter(project=project_obj)
                        jenkinsPro_obj = models.jenkinsPro.objects.get(project=project_obj)
                        param = eval(jenkinsPro_obj.param)
                        relVersion = project_plans_news[j].lastPackageId
                        if len(cursor) == 0:
                            for k in range(len(deployDetails)):
                                params = {}
                                params.update(param)
                                if relVersion:
                                    uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                                    server_obj = deployDetails[k].server
                                    params.update(SERVER_IP=server_obj.ip, REL_VERSION=relVersion)
                                    pythonJenkins_obj = pythonJenkins(jenkinsPro_obj.name, params)
                                    info = pythonJenkins_obj.deploy()
                                    for n in range(len(project_plans)):
                                        if project_plans[n].cursor:
                                            project_plans[n].cursor = False
                                            project_plans[n].save()
                                    project_plans_news[j].cursor = True
                                    project_plans_news[j].save()
                                    consoleOpt = info['consoleOpt']
                                    isSuccess = consoleOpt.find("Finished: SUCCESS")
                                    if isSuccess == -1:
                                        project_plans_news[j].buildStatus = 2
                                        project_plans_news[j].save()
                                        res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 发布出错!" % \
                                              (task_obj.name, project_obj.name, relVersion,
                                               project_servers[k].server.name)
                                        logger.info(res)
                                        buildMessages.append(res)
                                        buildMessages.append(uniqueKey)
                                        buildMessages.append('deploy_failed')
                                        request.websocket.send(json.dumps(buildMessages))
                                        request.websocket.close()
                                        consoleOpt_obj = models.consoleOpt(type=1, category=0, plan=task_obj.plan,
                                                                           project=project_obj,
                                                                           content=consoleOpt, packageId=relVersion,
                                                                           result=False, deployUser=member_obj,
                                                                           uniqueKey=uniqueKey, uniteKey=uniteKey)
                                        consoleOpt_obj.save()
                                        deployDetails[k].buildStatus = 2
                                        deployDetails[k].save()
                                        cursor.append(project_obj.id)
                                        break
                                    else:
                                        res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 发布完成！" % (
                                            task_obj.name, project_obj.name, relVersion,
                                            project_servers[k].server.name)
                                        logger.info(res)
                                        buildMessages.append(res)
                                        buildMessages.append(uniqueKey)
                                        request.websocket.send(json.dumps(buildMessages))
                                        consoleOpt_obj = models.consoleOpt(type=1, category=0, plan=task_obj.plan,
                                                                           project=project_obj, content=consoleOpt,
                                                                           packageId=relVersion, result=True,
                                                                           deployUser=member_obj,
                                                                           uniqueKey=uniqueKey, uniteKey=uniteKey)
                                        consoleOpt_obj.save()
                                        project_plans_news[j].buildStatus = 1
                                        project_plans_news[j].save()
                                        deployDetails[k].buildStatus = 1
                                        deployDetails[k].save()
                                else:
                                    cursor.append(project_obj.id)
                                    logger.info("项目：%s，没有发布版本号，请先在预发创建！" % project_obj.name)
                                    res = "项目：%s，没有发布版本号，请先在预发创建！" % project_obj.name
                                    buildMessages.append(res)
                                    buildMessages.append('no_reversion')
                                    request.websocket.send(json.dumps(buildMessages))
                                    request.websocket.close()
                                    break
                    if len(cursor) == 0:
                        sequence_obj.implemented = True
                        sequence_obj.executor = member_obj.name
                        sequence_obj.executeDate = datetime.datetime.now()
                        sequence_obj.remarks = "已部署"
                        sequence_obj.save()
                        res = "任务：%s，部署完成！" % task_obj.name
                        buildMessages.append(res)
                        buildMessages.append('deploy_success')
                        request.websocket.send(json.dumps(buildMessages))
                        request.websocket.close()
                else:
                    buildMessages.append('no_role')
                    request.websocket.send(json.dumps(buildMessages))
                    request.websocket.close()


# 跳过继续下一个发布
@login_required
@accept_websocket
def ws_continueDeploy(request):
    if request.is_websocket():
        for taskId in request.websocket:
            if taskId:
                uniteKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                task_obj = models.task.objects.get(id=taskId)
                project_plans = models.project_plan.objects.filter(plan=task_obj.plan).filter(
                    ~Q(buildStatus=1)).order_by('order')
                sequence_obj = models.sequence.objects.filter(task=task_obj).get(segment__isDeploy=True)
                production_members = models.production_member.objects.filter(production=task_obj.plan.production)
                member_obj = models.member.objects.get(user=request.user)
                isMember = False
                for m in range(len(production_members)):
                    if member_obj == production_members[m].member:
                        isMember = True
                buildMessages = []
                if isMember and member_obj.user.has_perm("can_deploy_project"):
                    order = 0
                    for i in range(len(project_plans)):
                        if project_plans[i].cursor:
                            order = project_plans[i].order
                            break
                    project_plans_news = project_plans.filter(order__gt=order).order_by('order')
                    if project_plans_news:
                        projectBean_obj = projectBean(project_plans_news)
                        total = projectBean_obj.countDeploySum(1, order)
                        buildMessages.append(total)
                        request.websocket.send(json.dumps(buildMessages))
                        cursor = []
                        for j in range(len(project_plans_news)):
                            project_obj = project_plans_news[j].project
                            deployDetails = models.deployDetail.objects.filter(
                                project_plan=project_plans_news[j]).order_by('-buildStatus')
                            jenkinsPro_obj = models.jenkinsPro.objects.get(project=project_obj)
                            param = eval(jenkinsPro_obj.param)
                            relVersion = project_plans_news[j].lastPackageId
                            if len(cursor) == 0:
                                for k in range(len(deployDetails)):
                                    params = {}
                                    params.update(param)
                                    if relVersion:
                                        server_obj = deployDetails[k].server
                                        uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                                        params.update(SERVER_IP=server_obj.ip, REL_VERSION=relVersion)
                                        pythonJenkins_obj = pythonJenkins(jenkinsPro_obj.name, params)
                                        info = pythonJenkins_obj.deploy()
                                        for n in range(len(project_plans)):
                                            if project_plans[n].cursor:
                                                project_plans[n].cursor = False
                                                project_plans[n].save()
                                        project_plans_news[j].cursor = True
                                        project_plans_news[j].save()
                                        consoleOpt = info['consoleOpt']
                                        isSuccess = consoleOpt.find("Finished: SUCCESS")
                                        if isSuccess == -1:
                                            project_plans_news[j].buildStatus = 2
                                            project_plans_news[j].save()
                                            deployDetails[k].buildStatus = 2
                                            deployDetails[k].save()
                                            res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 发布出错!" % \
                                                  (task_obj.name, project_obj.name, relVersion, server_obj.name)
                                            logger.info(res)
                                            buildMessages.append(res)
                                            buildMessages.append(uniqueKey)
                                            buildMessages.append('deploy_failed')
                                            request.websocket.send(json.dumps(buildMessages))
                                            request.websocket.close()
                                            consoleOpt_obj = models.consoleOpt(type=1, category=0, plan=task_obj.plan,
                                                                               project=project_obj,
                                                                               content=consoleOpt,
                                                                               packageId=relVersion,
                                                                               result=False, deployUser=member_obj,
                                                                               uniqueKey=uniqueKey,
                                                                               uniteKey=uniteKey)
                                            consoleOpt_obj.save()
                                            cursor.append(project_obj.id)
                                            break
                                        else:
                                            res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 发布完成！" % (
                                                task_obj.name, project_obj.name, relVersion, server_obj.name)
                                            logger.info(res)
                                            buildMessages.append(res)
                                            buildMessages.append(uniqueKey)
                                            request.websocket.send(json.dumps(buildMessages))
                                            consoleOpt_obj = models.consoleOpt(type=1, category=0, plan=task_obj.plan,
                                                                               project=project_obj,
                                                                               content=consoleOpt,
                                                                               packageId=relVersion, result=True,
                                                                               deployUser=member_obj,
                                                                               uniqueKey=uniqueKey,
                                                                               uniteKey=uniteKey)
                                            consoleOpt_obj.save()
                                            project_plans_news[j].buildStatus = 1
                                            project_plans_news[j].save()
                                            deployDetails[k].buildStatus = 1
                                            deployDetails[k].save()
                                    else:
                                        cursor.append(project_obj.id)
                                        logger.info("项目：%s，没有发布版本号，请先在预发创建！" % project_obj.name)
                                        res = "项目：%s，没有发布版本号，请先在预发创建！" % project_obj.name
                                        buildMessages.append(res)
                                        buildMessages.append('no_reversion')
                                        request.websocket.send(json.dumps(buildMessages))
                                        request.websocket.close()
                                        break
                        if len(cursor) == 0:
                            sequence_obj.implemented = True
                            sequence_obj.executor = member_obj.name
                            sequence_obj.executeDate = datetime.datetime.now()
                            sequence_obj.remarks = "已部署"
                            sequence_obj.save()
                            res = "任务：%s，部署完成！" % task_obj.name
                            buildMessages.append(res)
                            buildMessages.append('deploy_success')
                            request.websocket.send(json.dumps(buildMessages))
                            request.websocket.close()
                    else:
                        buildMessages.append('last_one')
                        request.websocket.send(json.dumps(buildMessages))
                        request.websocket.close()
                else:
                    buildMessages.append('no_role')
                    request.websocket.send(json.dumps(buildMessages))
                    request.websocket.close()


# 回滚当前节点
@login_required
@accept_websocket
def ws_rollbackOne(request):
    if request.is_websocket():
        for taskId in request.websocket:
            if taskId:
                uniteKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                task_obj = models.task.objects.get(id=taskId)
                project_plan_obj = models.project_plan.objects.filter(plan=task_obj.plan).get(cursor=True)
                project_obj = project_plan_obj.project
                buildMessages = []
                production_members = models.production_member.objects.filter(production=task_obj.plan.production)
                member_obj = models.member.objects.get(user=request.user)
                isMember = False
                for m in range(len(production_members)):
                    if member_obj == production_members[m].member:
                        isMember = True
                if isMember and member_obj.user.has_perm("can_deploy_project"):
                    deployDetails = models.deployDetail.objects.filter(project_plan=project_plan_obj).order_by(
                        '-buildStatus')
                    cursor = []
                    total = len(deployDetails)
                    buildMessages.append(total)
                    request.websocket.send(json.dumps(buildMessages))
                    try:
                        consoleOpt_obj = models.consoleOpt.objects.filter(project=project_obj).filter(
                            type=1).filter(packageId__lt=project_plan_obj.lastPackageId)[0]
                        project_plan_obj.buildStatus = 0
                        project_plan_obj.save()
                        for i in range(len(deployDetails)):
                            jenkinsPro_obj = models.jenkinsPro.objects.get(project=project_plan_obj.project)
                            param = eval(jenkinsPro_obj.param)
                            params = {}
                            params.update(param)
                            relVersion = consoleOpt_obj.packageId
                            print(relVersion)
                            server_obj = deployDetails[i].server
                            uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                            params.update(SERVER_IP=server_obj.ip, REL_VERSION=relVersion)
                            pythonJenkins_obj = pythonJenkins(jenkinsPro_obj.name, params)
                            info = pythonJenkins_obj.deploy()
                            consoleOpt = info['consoleOpt']
                            isSuccess = consoleOpt.find("Finished: SUCCESS")
                            if isSuccess == -1:
                                res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 回滚出错!" % \
                                      (task_obj.name, project_obj.name, relVersion, server_obj.name)
                                logger.info(res)
                                buildMessages.append(res)
                                buildMessages.append(uniqueKey)
                                request.websocket.send(json.dumps(buildMessages))
                                request.websocket.close()
                                consoleOpt_obj2 = models.consoleOpt(type=1, category=1, plan=task_obj.plan,
                                                                    project=project_obj,
                                                                    content=consoleOpt, packageId=relVersion,
                                                                    result=False, deployUser=member_obj,
                                                                    uniqueKey=uniqueKey, uniteKey=uniteKey)
                                consoleOpt_obj2.save()
                                cursor.append(project_obj.id)
                                deployDetails[i].buildStatus = 2
                                deployDetails[i].save()
                            else:
                                res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 回滚完成！" % (
                                    task_obj.name, project_obj.name, relVersion, server_obj.name)
                                logger.info(res)
                                buildMessages.append(res)
                                buildMessages.append(uniqueKey)
                                request.websocket.send(json.dumps(buildMessages))
                                consoleOpt_obj = models.consoleOpt(type=1, category=1, plan=task_obj.plan,
                                                                   project=project_obj,
                                                                   content=consoleOpt,
                                                                   packageId=relVersion, result=True,
                                                                   deployUser=member_obj,
                                                                   uniqueKey=uniqueKey,
                                                                   uniteKey=uniteKey)
                                consoleOpt_obj.save()
                                deployDetails[i].buildStatus = 1
                                deployDetails[i].save()
                        if len(cursor) == 0:
                            res = "任务：%s，部署完成！" % task_obj.name
                            buildMessages.append(res)
                            buildMessages.append('deploy_success')
                            request.websocket.send(json.dumps(buildMessages))
                            request.websocket.close()
                    except IndexError:
                        logger.info("项目：%s，已是最初版本，无法回滚！" % project_obj.name)
                        res = "项目：%s，已是最初版本，无法回滚！" % project_obj.name
                        buildMessages.append(res)
                        buildMessages.append('no_reversion')
                        request.websocket.send(json.dumps(buildMessages))
                        request.websocket.close()
                else:
                    buildMessages.append('no_role')
                    request.websocket.send(json.dumps(buildMessages))
                    request.websocket.close()


# 回滚所有节点
@login_required
@accept_websocket
def ws_rollbackAll(request):
    if request.is_websocket():
        for taskId in request.websocket:
            if taskId:
                uniteKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                task_obj = models.task.objects.get(id=taskId)
                project_plan_obj = models.project_plan.objects.filter(plan=task_obj.plan).get(cursor=True)
                project_plan_news = models.project_plan.objects.filter(order__lte=project_plan_obj.order)
                buildMessages = []
                production_members = models.production_member.objects.filter(production=task_obj.plan.production)
                member_obj = models.member.objects.get(user=request.user)
                isMember = False
                for m in range(len(production_members)):
                    if member_obj == production_members[m].member:
                        isMember = True
                if isMember and member_obj.user.has_perm("can_deploy_project"):
                    cursor = []
                    projectBean_obj = projectBean(project_plan_news)
                    total = projectBean_obj.countDeploySum2(1, project_plan_obj.order)
                    buildMessages.append(total)
                    request.websocket.send(json.dumps(buildMessages))
                    for k in range(len(project_plan_news)):
                        project_obj = project_plan_news[k].project
                        deployDetails = models.deployDetail.objects.filter(project_plan=project_plan_news[k]).order_by(
                            '-buildStatus')
                        try:
                            consoleOpt_obj = models.consoleOpt.objects.filter(project=project_obj).filter(
                                type=1).filter(packageId__lt=project_plan_news[k].lastPackageId)[0]
                            project_plan_news[k].buildStatus = 0
                            project_plan_news[k].save()
                            for i in range(len(deployDetails)):
                                jenkinsPro_obj = models.jenkinsPro.objects.get(project=project_plan_news[k].project)
                                param = eval(jenkinsPro_obj.param)
                                params = {}
                                params.update(param)
                                relVersion = consoleOpt_obj.packageId
                                server_obj = deployDetails[i].server
                                uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                                params.update(SERVER_IP=server_obj.ip, REL_VERSION=relVersion)
                                pythonJenkins_obj = pythonJenkins(jenkinsPro_obj.name, params)
                                info = pythonJenkins_obj.deploy()
                                consoleOpt = info['consoleOpt']
                                isSuccess = consoleOpt.find("Finished: SUCCESS")
                                if isSuccess == -1:
                                    res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 回滚出错!" % \
                                          (task_obj.name, project_obj.name, relVersion, server_obj.name)
                                    logger.info(res)
                                    buildMessages.append(res)
                                    buildMessages.append(uniqueKey)
                                    request.websocket.send(json.dumps(buildMessages))
                                    consoleOpt_obj2 = models.consoleOpt(type=1, category=1, plan=task_obj.plan,
                                                                        project=project_obj, content=consoleOpt,
                                                                        packageId=relVersion, result=False,
                                                                        deployUser=member_obj, uniqueKey=uniqueKey,
                                                                        uniteKey=uniteKey)
                                    consoleOpt_obj2.save()
                                    cursor.append(project_obj.id)
                                    deployDetails[i].buildStatus = 2
                                    deployDetails[i].save()
                                else:
                                    res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 回滚完成！" % (
                                        task_obj.name, project_obj.name, relVersion, server_obj.name)
                                    logger.info(res)
                                    buildMessages.append(res)
                                    buildMessages.append(uniqueKey)
                                    request.websocket.send(json.dumps(buildMessages))
                                    consoleOpt_obj = models.consoleOpt(type=1, category=1, plan=task_obj.plan,
                                                                       project=project_obj,
                                                                       content=consoleOpt,
                                                                       packageId=relVersion, result=True,
                                                                       deployUser=member_obj,
                                                                       uniqueKey=uniqueKey,
                                                                       uniteKey=uniteKey)
                                    consoleOpt_obj.save()
                                    deployDetails[i].buildStatus = 1
                                    deployDetails[i].save()
                        except IndexError:
                            logger.info("项目：%s，已是最初版本，无法回滚！" % project_obj.name)
                            res = "项目：%s，已是最初版本，无法回滚！" % project_obj.name
                            buildMessages.append(res)
                            buildMessages.append('no_reversion')
                            buildMessages.append(len(deployDetails))
                            request.websocket.send(json.dumps(buildMessages))
                            cursor.append(project_obj.id)
                    if len(cursor) == 0:
                        res = "任务：%s，所有节点都已回滚！" % task_obj.name
                        buildMessages.append(res)
                        buildMessages.append('deploy_success')
                        request.websocket.send(json.dumps(buildMessages))
                        request.websocket.close()
                else:
                    buildMessages.append('no_role')
                    request.websocket.send(json.dumps(buildMessages))
                    request.websocket.close()


# 预发构建
@login_required
@accept_websocket
def ws_uatDeploy(request):
    if request.is_websocket:
        for combination in request.websocket:
            projectId = str(combination, encoding="utf-8").split('-')[0]
            planId = str(combination, encoding="utf-8").split('-')[1]
            deployTime = str(combination, encoding="utf-8").split('-')[2]
            uniteKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
            member_obj = models.member.objects.get(user=request.user)
            plan_obj = models.plan.objects.get(id=planId)
            project_obj = models.project.objects.get(id=projectId)
            project_plan_obj = models.project_plan.objects.get(plan=plan_obj, project=project_obj)
            jenkinsUat_obj = models.jenkinsUat.objects.get(project=project_obj)
            project_servers = models.project_server.objects.filter(project=project_obj)
            production_members = models.production_member.objects.filter(production=plan_obj.production)
            isMember = False
            buildMessage = []
            for m in range(len(production_members)):
                if member_obj == production_members[m].member:
                    isMember = True
            if isMember and member_obj.user.has_perm("can_deploy_project"):
                if project_plan_obj.uatBranch:
                    param = eval(jenkinsUat_obj.param)
                    for i in range(len(project_servers)):
                        params = {}
                        params.update(param)
                        server_obj = project_servers[i].server
                        if server_obj.type == 0:
                            uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                            params.update(SERVER_IP=server_obj.ip, BRANCH=project_plan_obj.uatBranch)
                            logger.info("param：%s" % params)
                            pythonJenkins_obj = pythonJenkins(jenkinsUat_obj.name, params)
                            logger.info("分支%s执行部署" % project_plan_obj.uatBranch)
                            buildMessage.append("deploy")
                            buildMessage.append("分支%s执行部署" % project_plan_obj.uatBranch)
                            request.websocket.send(json.dumps(buildMessage))
                            info = pythonJenkins_obj.deploy()
                            if info:
                                consoleOpt = info['consoleOpt']
                                buildId = info['buildId']
                                isSuccess = consoleOpt.find("Finished: SUCCESS")
                                if isSuccess != -1:
                                    result = True
                                    project_plan_obj.lastPackageId = buildId
                                    project_plan_obj.save()
                                    res = "分支%s部署成功" % project_plan_obj.uatBranch
                                    logger.info("分支%s部署成功" % project_plan_obj.uatBranch)
                                    buildMessage.append("success")
                                    buildMessage.append(res)
                                    buildMessage.append(uniqueKey)
                                    request.websocket.send(json.dumps(buildMessage))
                                    request.websocket.close()
                                else:
                                    result = False
                                    res = "分支%s部署失败" % project_plan_obj.uatBranch
                                    logger.error("分支%s部署失败" % project_plan_obj.uatBranch)
                                    buildMessage.append("fail")
                                    buildMessage.append(res)
                                    buildMessage.append(uniqueKey)
                                    request.websocket.send(json.dumps(buildMessage))
                                    request.websocket.close()
                                consoleOpt_obj = models.consoleOpt(type=0, plan=plan_obj, project=project_obj,
                                                                   content=consoleOpt, packageId=buildId, result=result,
                                                                   deployTime=deployTime, deployUser=member_obj,
                                                                   uniqueKey=uniqueKey, uniteKey=uniteKey)
                                consoleOpt_obj.save()

                else:
                    logger.info("没有预发分支，请先创建！")
                    res = "没有预发分支，请先创建！"
                    buildMessage.append("no_branch")
                    buildMessage.append(res)
                    request.websocket.send(json.dumps(buildMessage))
                    request.websocket.close()
            else:
                logger.error("用户%s没有执行预发部署的权限！" % member_obj.name)
                res = "您没有执行产品%s预发部署权限！" % plan_obj.production.name
                buildMessage.append("no_role")
                buildMessage.append(res)
                request.websocket.send(json.dumps(buildMessage))
                request.websocket.close()


# 代码合并
@login_required
@accept_websocket
def ws_codeMerge(request):
    if request.is_websocket():
        for taskId in request.websocket:
            if taskId:
                task_obj = models.task.objects.get(id=taskId)
                project_plans = models.project_plan.objects.filter(plan=task_obj.plan)
                production_members = models.production_member.objects.filter(production=task_obj.plan.production)
                member_obj = models.member.objects.get(user=request.user)
                isMember = False
                buildMessages = []
                for m in range(len(production_members)):
                    if member_obj == production_members[m].member:
                        isMember = True
                if isMember and member_obj.user.has_perm("can_deploy_project"):
                    buildMessages.append(len(project_plans))
                    request.websocket.send(json.dumps(buildMessages))
                    for i in range(len(project_plans)):
                        project_obj = project_plans[i].project
                        branch_obj = branch(project_obj.project_dir)
                        status = branch_obj.merge_branch(project_plans[i].uatBranch, 'master_copy')
                        if status:
                            project_plans[i].mergeStatus = 1
                            project_plans[i].save()
                            buildMessages.append("ok")
                            res = "项目%s合并完成" % project_plans[i].project.name
                            buildMessages.append(res)
                            request.websocket.send(json.dumps(buildMessages))
                        else:
                            project_plans[i].mergeStatus = 2
                            project_plans[i].save()
                            buildMessages.append("conflict")
                            res = "项目%s合并冲突，请手工处理！" % project_plans[i].project.name
                            buildMessages.append(res)
                            request.websocket.send(json.dumps(buildMessages))
                    buildMessages.append("success")
                    request.websocket.send(json.dumps(buildMessages))
                    request.websocket.close()
                    send_mail("发布任务%s分支合并结果" % task_obj.name, str(buildMessages), mail_from, mail_to,
                              fail_silently=False)
                else:
                    buildMessages.append("no_role")
                    request.websocket.send(json.dumps(buildMessages))
                    request.websocket.close()


# 查看预发控制台信息
@login_required
def uat_console_opt(request, uid):
    if uid:
        consoleOpts = models.consoleOpt.objects.filter(uniteKey=uid)
        planId = consoleOpts[0].plan.id
        projectId = consoleOpts[0].project.id

    template = get_template('uatConsoleOpt.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 查看生产控制台信息
@login_required
def pro_console_opt(request, uid):
    if uid:
        consoleOpts = models.consoleOpt.objects.filter(uniteKey=uid)
        task_obj = models.task.objects.get(plan=consoleOpts[0].plan)

    template = get_template('proConsoleOpt.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 单个控制台信息查看
def single_console_opt(request, uid):
    if uid:
        consoleOpt_obj = models.consoleOpt.objects.get(uniqueKey=uid)

    template = get_template('single_console_opt.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)
