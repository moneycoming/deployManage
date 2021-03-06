#!/usr/bin/python3
# -*- coding:utf-8 -*-
import json
import time
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template.loader import get_template
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import connection, connections
from mysite.functions import TimeChange, fileObj, branch, DateEncoder
from mysite import models
import datetime
from mysite.jenkinsUse import pythonJenkins, projectBean
from django.views.decorators.csrf import csrf_exempt
import uuid
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
from apscheduler.jobstores.base import ConflictingIdError
from mysite.dataAnalysis import DataAnalysis
from dwebsocket.decorators import accept_websocket
from django.db.models import Q
from mysite.multiEmail import email_createPlan, email_uatCheck, email_createTask, email_proCheck
from django.views.decorators.http import require_http_methods

# 添加全局变量，记录日志
logger = logging.getLogger('log')
# 参数化git配置
gitCmd_obj = models.paramConfig.objects.get(name='gitCmd')
# 邮件路径配置
email_url_obj = models.paramConfig.objects.get(name='email_url')
# 邮件抄送对象配置
mail_cc = []
mail_cc_obj = models.paramConfig.objects.get(name='mail_cc')
mail_cc.append(mail_cc_obj.param)
mail_from = "deploy@zhixuezhen.com"

# # 定时获取dev_branch
scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")
try:
    @register_job(scheduler, "interval", seconds=60)
    def get_branch_info():
        projects = models.project.objects.all()
        for k in range(len(projects)):
            branches = models.devBranch.objects.filter(project=projects[k])
            projectBean_obj = projectBean(projects[k], gitCmd_obj.param)
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


# 首页及任务信息展示
def index(request):
    plans = models.plan.objects.all()
    productions = models.production.objects.all()
    if request.user.is_authenticated:
        member_obj = models.member.objects.get(user=request.user)
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
    member_obj = models.member.objects.get(user=request.user)
    plans = models.plan.objects.filter(production__member=member_obj).order_by('-createDate')

    template = get_template('showPlan.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 创建计划
@login_required
def createPlan(request):
    kinds = models.kind.objects.all()
    projects = models.project.objects.all()
    member_obj = models.member.objects.get(user=request.user)
    productions = models.production_member.objects.filter(member=member_obj)
    if request.method == 'POST' and member_obj.user.has_perm("mysite.add_plan"):
        production_obj = models.production.objects.get(name=request.POST['production'])
        production_members = models.production_member.objects.filter(production=production_obj)
        projectList = request.POST.getlist('project')
        devBranchList = request.POST.getlist('devBranch')
        kind_obj = models.kind.objects.get(name=request.POST['kind'])
        plan_obj = models.plan(name=request.POST['title'], description=request.POST['desc'], kind=kind_obj,
                               production=production_obj, createUser=member_obj, createDate=datetime.datetime.now())
        plan_obj.save()

        for j in range(len(projectList)):
            project_obj = models.project.objects.get(name=projectList[j])
            project_plan_obj = models.project_plan(plan=plan_obj, project=project_obj, devBranch=devBranchList[j])
            project_plan_obj.save()
            project_servers = models.project_server.objects.filter(project=project_obj).filter(server__type=1)
            for i in range(len(project_servers)):
                deployDetail_obj = models.deployDetail(project_plan=project_plan_obj,
                                                       server=project_servers[i].server)
                deployDetail_obj.save()

        project_plans = models.project_plan.objects.filter(plan=plan_obj)
        mail_to = []
        for k in range(len(production_members)):
            mail_to.append(production_members[k].member.user.email)
        email_createPlan(project_plans, mail_from, mail_to, mail_cc, email_url_obj)
        return HttpResponseRedirect('/planDetail?pid=%s' % plan_obj.id)

    template = get_template('createPlan.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 计划详情
@login_required
def planDetail(request):
    planId = request.GET.get('pid')
    if request.user.is_authenticated:
        member_obj = models.member.objects.get(user=request.user)
    if planId:
        plan_obj = models.plan.objects.get(id=planId)
        project_plans = models.project_plan.objects.filter(plan=plan_obj)
        projects = models.project.objects.all()
        # sub_plans = models.plan.objects.filter(fatherPlanId=plan_obj.id)
        # father_plans = models.plan.objects.filter(subPlanId=plan_obj.id)
        try:
            task_obj = models.task.objects.filter(plan=plan_obj)[0]
            proCheckStatus = False
            sequences = models.sequence.objects.filter(task=task_obj)
            for i in range(len(sequences)):
                if sequences[i].segment.isCheck and sequences[i].implemented:
                    proCheckStatus = True
                    sequence_check_obj = sequences[i]
        except IndexError:
            pass

    template = get_template('planDetail.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 添加项目
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def ajax_addProject(request):
    plan_obj = models.plan.objects.get(id=request.POST['id'])
    projectName = request.POST['project']
    devBranch = request.POST['branch']
    member_obj = models.member.objects.get(user=request.user)
    production_members = models.production_member.objects.filter(production=plan_obj.production)
    isMember = False
    for m in range(len(production_members)):
        if member_obj == production_members[m].member:
            isMember = True
    if isMember and member_obj.user.has_perm('mysite.can_deploy_project'):
        if not plan_obj.uatCheck:
            if projectName and devBranch:
                project_obj = models.project.objects.get(name=request.POST['project'])
                devBranch = request.POST['branch']
                project_plans = models.project_plan.objects.filter(plan=plan_obj)
                flag = True
                for i in range(len(project_plans)):
                    if project_plans[i].project == project_obj:
                        flag = False
                        break
                if flag:
                    project_plan_obj = models.project_plan(project=project_obj, plan=plan_obj, devBranch=devBranch)
                    project_plan_obj.save()
                    project_servers = models.project_server.objects.filter(project=project_obj).filter(server__type=1)
                    for j in range(len(project_servers)):
                        deployDetail_obj = models.deployDetail(project_plan=project_plan_obj,
                                                               server=project_servers[j].server)
                        deployDetail_obj.save()
                else:
                    project_plan_obj = models.project_plan.objects.get(project=project_obj, plan=plan_obj)
                    project_plan_obj.devBranch = devBranch
                    project_plan_obj.save()
                ret = {
                    'result': True,
                    'role': True,
                    'params': True,
                    'project': projectName,
                    'branch': devBranch,
                    'checked': False
                }
            else:
                ret = {
                    'result': False,
                    'role': True,
                    'params': False,
                    'checked': False
                }
        else:
            ret = {
                'role': True,
                'checked': True
            }
    else:
        ret = {
            'result': False,
            'role': False,
            'params': False,
        }

    return HttpResponse(json.dumps(ret), "application/json")


# 删除项目
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def ajax_deleteProject(request):
    member_obj = models.member.objects.get(user=request.user)
    project_plan_obj = models.project_plan.objects.get(id=request.POST['id'])
    production_members = models.production_member.objects.filter(production=project_plan_obj.plan.production)
    isMember = False
    for m in range(len(production_members)):
        if member_obj == production_members[m].member:
            isMember = True
    if isMember and member_obj.user.has_perm('mysite.can_deploy_project'):
        if not project_plan_obj.plan.uatCheck:
            project_plan_obj.delete()
            ret = {
                'role': True,
                'project': project_plan_obj.project.name,
                'branch': project_plan_obj.devBranch,
                'checked': False
            }
        else:
            ret = {
                'role': True,
                'checked': True
            }
    else:
        ret = {
            'role': False
        }

    return HttpResponse(json.dumps(ret), "application/json")


# 计划删除
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def ajax_deletePlan(request):
    planId = request.POST.get('id')
    if planId:
        plan_obj = models.plan.objects.get(id=planId)
        member_obj = models.member.objects.get(user=request.user)
        production_members = models.production_member.objects.filter(production=plan_obj.production)
        isMember = False
        for m in range(len(production_members)):
            if member_obj == production_members[m].member:
                isMember = True
                break
        if isMember and member_obj.user.has_perm('mysite.delete_plan'):
            plan_obj.delete()

            ret = {
                'role': 1
            }
        else:
            ret = {
                'role': 0
            }

        return HttpResponse(json.dumps(ret), "application/json")


# 任务主页
@login_required
def showTask(request):
    # 使用了js分页技术，无须做分页
    tasks = models.task.objects.all()
    if request.user.is_authenticated:
        member_obj = models.member.objects.get(user=request.user)

    template = get_template('showTask.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 创建任务
@login_required
def createTask(request):
    deploySegment_obj = models.segment.objects.get(isDeploy=1)
    checkSegment_obj = models.segment.objects.get(isCheck=1)
    mergeSegment_obj = models.segment.objects.get(isMerge=1)
    beforeDeploySegments = models.segment.objects.filter(order__lt=deploySegment_obj.order)
    afterDeploySegments = models.segment.objects.filter(order__gt=deploySegment_obj.order).filter(
        ~Q(order=checkSegment_obj.order)).filter(~Q(order=mergeSegment_obj.order))
    member_obj = models.member.objects.get(user=request.user)
    plan_obj = models.plan.objects.get(id=request.GET['pid'])
    if request.method == 'POST':
        production_members = models.production_member.objects.filter(production=plan_obj.production)
        isMember = False
        for m in range(len(production_members)):
            if member_obj == production_members[m].member:
                isMember = True
        if isMember and member_obj.user.has_perm('mysite.add_task'):
            beforeDeployList = request.POST.getlist('beforeDeploy')
            afterDeployList = request.POST.getlist('afterDeploy')
            createDate = datetime.datetime.now()
            tasks = models.task.objects.filter(plan=plan_obj)
            if not tasks:
                task_obj = models.task(name=plan_obj.name, plan=plan_obj, createUser=member_obj,
                                       createDate=createDate,
                                       onOff=1)
                task_obj.save()
                for i in range(len(beforeDeployList)):
                    segment_obj = models.segment.objects.get(name=beforeDeployList[i])
                    sequence_obj = models.sequence(segment=segment_obj, task=task_obj)
                    sequence_obj.save()
                for j in range(len(afterDeployList)):
                    segment_obj = models.segment.objects.get(name=afterDeployList[j])
                    sequence_obj = models.sequence(segment=segment_obj, task=task_obj)
                    sequence_obj.save()
                sequence_deploy_obj = models.sequence(segment=deploySegment_obj, task=task_obj)
                sequence_deploy_obj.save()
                sequence_check_obj = models.sequence(segment=checkSegment_obj, task=task_obj)
                sequence_check_obj.save()
                sequence_merge_obj = models.sequence(segment=mergeSegment_obj, task=task_obj)
                sequence_merge_obj.save()
                sequences = models.sequence.objects.filter(task=task_obj).order_by('segment__order')

                for n in range(len(sequences)):
                    sequences[n].pre_segment = n
                    sequences[n].next_segment = n + 2
                    sequences[n].priority = n + 1
                    sequences[n].save()

                sequences[0].executeCursor = 1
                sequences[0].save()

                mail_to = []
                for k in range(len(production_members)):
                    mail_to.append(production_members[k].member.user.email)
                email_createTask(plan_obj, sequences, mail_from, mail_to, mail_cc, email_url_obj)

                return HttpResponseRedirect('/taskDetail?tid=%s' % task_obj.id)

    template = get_template('createTask.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 任务详情
@login_required
def taskDetail(request):
    taskId = request.GET.get('tid')
    if request.user.is_authenticated:
        member_obj = models.member.objects.get(user=request.user)
    if taskId:
        task_obj = models.task.objects.get(id=taskId)
        project_plans = models.project_plan.objects.filter(plan=task_obj.plan)
        upToImplementSequence = models.sequence.objects.filter(task=task_obj).get(executeCursor=True)
        unimplementedSequences = models.sequence.objects.filter(task=task_obj,
                                                                priority__gt=upToImplementSequence.priority).order_by(
            'priority')
        blueBlueSequences = models.sequence.objects.filter(task=task_obj,
                                                           priority__lte=upToImplementSequence.priority).order_by(
            'priority')
        try:
            blueGraySequence = unimplementedSequences[0]
            grayGraySequences = unimplementedSequences[1:]
        except IndexError:
            logger.info("%s已是最后一个环节" % upToImplementSequence.segment.name)

        sequences = models.sequence.objects.filter(task=task_obj).order_by('priority')
        taskBuildHistories = models.taskBuildHistory.objects.filter(task=task_obj).order_by('deployTime')

    template = get_template('taskDetail.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 任务删除
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def ajax_deleteTask(request):
    taskId = request.POST.get('id')
    if taskId:
        member_obj = models.member.objects.get(user=request.user)
        task_obj = models.task.objects.get(id=taskId)
        production_members = models.production_member.objects.filter(production=task_obj.plan.production)
        isMember = False
        for m in range(len(production_members)):
            if member_obj == production_members[m].member:
                isMember = True
                break
        if isMember and member_obj.user.has_perm('mysite.delete_task'):
            task_obj.delete()
            ret = {
                'role': 1
            }
        else:
            ret = {
                'role': 0
            }

        return HttpResponse(json.dumps(ret), "application/json")


# 控制任务启用开关
@login_required
@csrf_exempt
def ajax_showTask(request):
    onOff = request.POST.get('onOff')
    taskId = request.POST.get('id')
    if taskId:
        task = models.task.objects.get(id=taskId)
        task.onOff = onOff
        task.save()

        return HttpResponse(task)


# 预发详情
@login_required
def uatDetail(request):
    planId = request.GET.get('pid')
    member_obj = models.member.objects.get(user=request.user)
    if planId:
        plan_obj = models.plan.objects.get(id=planId)
        project_plans = models.project_plan.objects.filter(plan=plan_obj)

    template = get_template('uatDetail.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 预发部署主页
@login_required
def uatDeploy(request):
    projectId = request.GET.get('prjId')
    planId = request.GET.get('pid')
    if request.user.is_authenticated:
        member_obj = models.member.objects.get(user=request.user)
    if projectId and planId:
        project_obj = models.project.objects.get(id=projectId)
        plan_obj = models.plan.objects.get(id=planId)
        project_plan_obj = models.project_plan.objects.get(project=project_obj, plan=plan_obj)
        consoleOpts = models.consoleOpt.objects.filter(project=project_obj, plan=plan_obj, type=0).order_by(
            'deployTime')

    template = get_template('uatDeploy.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 预发部署
@login_required
@accept_websocket
def ws_uatDeploy(request):
    if request.is_websocket:
        combination = request.websocket.wait()
        if combination:
            projectId = str(combination, encoding="utf-8").split('-')[0]
            planId = str(combination, encoding="utf-8").split('-')[1]
            deployTime = str(combination, encoding="utf-8").split('-')[2]
            uniteKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
            member_obj = models.member.objects.get(user=request.user)
            plan_obj = models.plan.objects.get(id=planId)
            project_obj = models.project.objects.get(id=projectId)
            project_plan_obj = models.project_plan.objects.get(plan=plan_obj, project=project_obj)
            production_members = models.production_member.objects.filter(production=plan_obj.production)
            isMember = False
            buildMessage = []
            for m in range(len(production_members)):
                if member_obj == production_members[m].member:
                    isMember = True
            if isMember and member_obj.user.has_perm("mysite.can_check_project"):
                if not plan_obj.uatCheck:
                    project_plans = models.project_plan.objects.filter(project=project_obj, exclusiveKey=True)
                    exclusivePlan = []
                    for k in range(len(project_plans)):
                        exclusivePlan.append(project_plans[k].plan.name)
                    if not project_plans or project_plan_obj.exclusiveKey:
                        if project_plan_obj.uatBranch:
                            uatBranchCreateDate = int(project_plan_obj.uatBranchCreateDate.strftime('%Y%m%d%H%M'))
                            post_project_plans = models.project_plan.objects.filter(project=project_obj,
                                                                                    proBuildStatus=1)
                            isBranchOutOfDate = False
                            for item in range(len(post_project_plans)):
                                if post_project_plans[item].mergeDate:
                                    post_project_plan_mergeDate = int(
                                        post_project_plans[item].mergeDate.strftime('%Y%m%d%H%M'))
                                    if post_project_plan_mergeDate > uatBranchCreateDate:
                                        isBranchOutOfDate = True
                                        break
                                else:
                                    continue
                            if not isBranchOutOfDate:
                                if not project_plan_obj.uatOnBuilding:
                                    project_servers = models.project_server.objects.filter(project=project_obj,
                                                                                           server__type=0)
                                    jenkinsUat_obj = models.jenkinsUat.objects.get(project=project_obj)
                                    project_plan_obj.exclusiveKey = True
                                    project_plan_obj.uatOnBuilding = True
                                    project_plan_obj.save()
                                    deployDetails = models.deployDetail.objects.filter(project_plan=project_plan_obj)
                                    for j in range(len(deployDetails)):
                                        deployDetails[j].buildStatus = False
                                        deployDetails[j].save()
                                    for i in range(len(project_servers)):
                                        params = eval(jenkinsUat_obj.param)
                                        server_obj = project_servers[i].server
                                        uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                                        params.update(SERVER_IP=server_obj.ip, BRANCH=project_plan_obj.uatBranch)
                                        logger.info("param：%s" % params)
                                        pythonJenkins_obj = pythonJenkins(jenkinsUat_obj.name, params)
                                        logger.info("分支%s执行部署" % project_plan_obj.uatBranch)
                                        request.websocket.send(json.dumps(buildMessage))
                                        buildNumber = pythonJenkins_obj.realConsole()
                                        status = pythonJenkins_obj.deploy()
                                        if status:
                                            buildInfo = pythonJenkins_obj.get_building_info()
                                            while not buildInfo:
                                                time.sleep(1)
                                                buildInfo = pythonJenkins_obj.get_building_info()
                                            url = buildInfo['url'] + "console"
                                            buildMessage.append("deploy")
                                            buildMessage.append(url)
                                            request.websocket.send(json.dumps(buildMessage))
                                            info = pythonJenkins_obj.get_build_console(buildNumber)
                                            consoleOpt = info['consoleOpt']
                                            isAbort = consoleOpt.find("Finished: ABORTED")
                                            isSuccess = consoleOpt.find("Finished: SUCCESS")
                                            if isAbort == -1:
                                                if isSuccess != -1:
                                                    result = True
                                                    project_plan_obj.uatBuildStatus = 1
                                                    project_plan_obj.lastPackageId = buildNumber
                                                    project_plan_obj.deployBranch = project_plan_obj.uatBranch
                                                    project_plan_obj.save()
                                                    res = "分支%s部署成功" % project_plan_obj.uatBranch
                                                    logger.info("分支%s部署成功" % project_plan_obj.uatBranch)
                                                    buildMessage.append("success")
                                                    buildMessage.append(res)
                                                    buildMessage.append(buildNumber)
                                                    request.websocket.send(json.dumps(buildMessage))
                                                    request.websocket.close()
                                                    if project_plan_obj.proBuildStatus != 0:
                                                        project_plan_obj.proBuildStatus = 0
                                                        project_plan_obj.save()
                                                else:
                                                    result = False
                                                    res = "分支%s部署失败" % project_plan_obj.uatBranch
                                                    logger.error("分支%s部署失败" % project_plan_obj.uatBranch)
                                                    project_plan_obj.uatBuildStatus = 2
                                                    project_plan_obj.save()
                                                    buildMessage.append("fail")
                                                    buildMessage.append(res)
                                                    buildMessage.append(uniqueKey)
                                                    request.websocket.send(json.dumps(buildMessage))
                                                    request.websocket.close()
                                            else:
                                                result = False
                                                logger.info("项目%s已经终止部署！" % project_obj.name)
                                                res = "项目%s已经终止部署！" % project_obj.name
                                                buildMessage.append("aborted")
                                                buildMessage.append(res)
                                                request.websocket.send(json.dumps(buildMessage))
                                                request.websocket.close()
                                            consoleOpt_obj = models.consoleOpt(type=0, plan=plan_obj,
                                                                               project=project_obj,
                                                                               content=consoleOpt,
                                                                               packageId=buildNumber,
                                                                               buildStatus=result,
                                                                               deployTime=deployTime,
                                                                               deployUser=member_obj,
                                                                               uniqueKey=uniqueKey,
                                                                               uniteKey=uniteKey)
                                            consoleOpt_obj.save()
                                        else:
                                            logger.info("jenkins Job %s不存在！" % jenkinsUat_obj.name)
                                            res = "jenkins Job %s不存在！" % jenkinsUat_obj.name
                                            buildMessage.append("no_jenkinsJob")
                                            buildMessage.append(res)
                                            request.websocket.send(json.dumps(buildMessage))
                                            request.websocket.close()
                                    project_plan_obj.uatOnBuilding = False
                                    project_plan_obj.save()
                                else:
                                    logger.info("预发部署中，请不要重复执行！")
                                    res = "预发部署中，请不要重复执行！"
                                    buildMessage.append("on_building")
                                    buildMessage.append(res)
                                    request.websocket.send(json.dumps(buildMessage))
                                    request.websocket.close()
                            else:
                                logger.info("该预发分支已经过时，请重新创建！")
                                res = "该预发分支已经过时，请重新创建！"
                                buildMessage.append("out_of_date")
                                buildMessage.append(res)
                                request.websocket.send(json.dumps(buildMessage))
                                request.websocket.close()
                        else:
                            logger.info("没有预发分支，请先创建！")
                            res = "没有预发分支，请先创建！"
                            buildMessage.append("no_branch")
                            buildMessage.append(res)
                            request.websocket.send(json.dumps(buildMessage))
                            request.websocket.close()
                    else:
                        res = "该项目已经被发布计划%s占用，无法部署" % exclusivePlan
                        logger.info(res)
                        buildMessage.append("exclusive")
                        buildMessage.append(res)
                        request.websocket.send(json.dumps(buildMessage))
                        request.websocket.close()
                else:
                    logger.error("预发验收已通过，不能再执行预发部署！")
                    res = "预发验收已通过，不能再执行预发部署！"
                    buildMessage.append("already_uatCheck")
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


# 预发终止部署
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def ajax_uatStopDeploy(request):
    project_obj = models.project.objects.get(id=request.POST['projectId'])
    plan_obj = models.plan.objects.get(id=request.POST['planId'])
    project_plan_obj = models.project_plan.objects.get(plan=plan_obj, project=project_obj)
    production_members = models.production_member.objects.filter(production=plan_obj.production)
    member_obj = models.member.objects.get(user=request.user)
    isMember = False
    for m in range(len(production_members)):
        if member_obj == production_members[m].member:
            isMember = True
    if isMember and member_obj.user.has_perm('mysite.can_check_project'):
        if project_plan_obj.uatOnBuilding:
            project_plan_obj.uatOnBuilding = False
            project_plan_obj.save()
            uatJenkins_obj = models.jenkinsUat.objects.get(project=project_obj)
            pythonJenkins_obj = pythonJenkins(uatJenkins_obj.name, {})
            buildNumber = pythonJenkins_obj.get_building_info()['number']
            if buildNumber:
                info = pythonJenkins_obj.stop_build(buildNumber)
                consoleOpt = info['consoleOpt']
                isAbort = consoleOpt.find("Finished: ABORTED")
                isSuccess = consoleOpt.find("Finished: SUCCESS")
                if isAbort == -1:
                    if isSuccess == -1:
                        ret = {
                            'role': True,
                            'stop': False,
                            'build': False,
                            'project': project_obj.name
                        }
                    else:
                        ret = {
                            'role': True,
                            'stop': False,
                            'build': True,
                            'project': project_obj.name
                        }
                else:
                    ret = {
                        'role': True,
                        'stop': True,
                        'build': False,
                        'project': project_obj.name
                    }
            else:
                ret = {
                    'role': True,
                    'start': False,
                }
        else:
            ret = {
                'role': True,
                'start': False
            }
    else:
        ret = {
            'role': False
        }

    return HttpResponse(json.dumps(ret), "application/json")


# 预发验收
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def ajax_uatCheck(request):
    planId = request.POST.get('planId')
    if planId:
        member_obj = models.member.objects.get(user=request.user)
        plan_obj = models.plan.objects.get(id=planId)
        production_members = models.production_member.objects.filter(production=plan_obj.production)
        isMember = False
        for m in range(len(production_members)):
            if member_obj == production_members[m].member:
                isMember = True
        if isMember and member_obj.user.has_perm('mysite.can_check_project'):
            project_plans = models.project_plan.objects.filter(plan=plan_obj)
            unDeployedProject = []
            for j in range(len(project_plans)):
                if project_plans[j].uatBuildStatus != 1:
                    unDeployedProject.append(project_plans[j].project.name)
            if len(unDeployedProject) == 0:
                remark = request.POST.get('remark')
                plan_obj.uatCheck = True
                plan_obj.uatRemark = remark
                plan_obj.uatCheckMember = member_obj
                plan_obj.uatCheckDate = datetime.datetime.now()
                plan_obj.save()
                ret = {
                    'role': 1,
                    'uatRemark': plan_obj.uatRemark,
                    'uatCheckMember': plan_obj.uatCheckMember.name,
                    'uatCheckDate': plan_obj.uatCheckDate,
                    'deploy': 1
                }
                project_plans = models.project_plan.objects.filter(plan=plan_obj)
                for i in range(len(project_plans)):
                    project_plans[i].exclusiveKey = 0
                    project_plans[i].save()

                mail_to = []
                for k in range(len(production_members)):
                    mail_to.append(production_members[k].member.user.email)
                email_uatCheck(plan_obj, mail_from, mail_to, mail_cc, email_url_obj)
            else:
                ret = {
                    'role:': 1,
                    'deployed': 0,
                    'projects': unDeployedProject
                }
        else:
            ret = {
                'role': 0,
                'uatRemark': None,
                'uatCheckMember': None,
                'uatCheckDate': None
            }

        return HttpResponse(json.dumps(ret, cls=DateEncoder), content_type='application/json')


# 创建预发分支
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def ajax_createUatBranch(request):
    planId = request.POST.get('pid')
    projectId = request.POST.get('prjId')
    if projectId and planId:
        project_obj = models.project.objects.get(id=projectId)
        plan_obj = models.plan.objects.get(id=planId)
        project_plan_obj = models.project_plan.objects.get(project=project_obj, plan=plan_obj)
        production_members = models.production_member.objects.filter(production=plan_obj.production)
        branch_obj = branch(project_obj.project_dir, gitCmd_obj.param)
        member_obj = models.member.objects.get(user=request.user)
        isMember = False
        for m in range(len(production_members)):
            if member_obj == production_members[m].member:
                isMember = True
        if isMember and member_obj.user.has_perm("mysite.can_check_project"):
            if not plan_obj.uatCheck:
                option = request.POST.get('radio')
                if option == "option1":
                    uatBranch = request.POST.get('uatBranch')
                    status = True
                else:
                    now = datetime.datetime.now()
                    branchCode = now.strftime('%Y%m%d%H%M')
                    uid = ''.join(str(uuid.uuid4()).split('-'))[0:5]
                    uatBranch = "uat-"
                    uatBranch += branchCode
                    uatBranch += '-'
                    uatBranch += uid
                    branch_obj.create_branch(uatBranch)
                    status = branch_obj.merge_branch(project_plan_obj.devBranch, uatBranch)

                if status:
                    if project_plan_obj.uatBranch:
                        logger.info("原预发分支：%s，将被删除！" % project_plan_obj.uatBranch)
                        delStatus = branch_obj.delete_branch(project_plan_obj.uatBranch)
                        if not delStatus:
                            logger.info("原预发分支%s删除失败！" % project_plan_obj.uatBranch)
                        else:
                            logger.info("原预发分支%s删除成功！" % project_plan_obj.uatBranch)
                    project_plan_obj.uatBranch = uatBranch
                    project_plan_obj.uatBuildStatus = 0
                    project_plan_obj.uatBranchCreateDate = datetime.datetime.now()
                    project_plan_obj.save()
                    res = "预发分支：%s创建成功！" % uatBranch
                    ret = {
                        'role': 1,
                        'result': 1,
                        'res': res,
                        'check': 0,
                        'uatBranch': uatBranch
                    }
                else:
                    res = "预发分支：%s创建失败,分支合并冲突，请手工处理！" % uatBranch
                    ret = {
                        'role': 1,
                        'result': 0,
                        'check': 0,
                        'res': res
                    }
            else:
                ret = {
                    'role': 1,
                    'check': 1
                }
        else:
            ret = {
                'role': 0
            }

        return HttpResponse(json.dumps(ret), "application/json")


# 任务队列是否执行完成
@login_required
@csrf_exempt
def ajax_taskImplement(request):
    sequenceId = request.POST.get('id')
    task_obj = models.task.objects.get(id=request.POST['taskId'])
    production_members = models.production_member.objects.filter(production=task_obj.plan.production)
    member_obj = models.member.objects.get(user=request.user)
    isMember = False
    for m in range(len(production_members)):
        if member_obj == production_members[m].member:
            isMember = True
    if sequenceId:
        sequence_obj = models.sequence.objects.get(id=sequenceId)
        if isMember and member_obj.user.has_perm('mysite.can_deploy_project'):
            sequence_obj.implemented = True
            sequence_obj.remarks = request.POST['remark']
            sequence_obj.executor = member_obj
            sequence_obj.executeDate = datetime.datetime.now()
            sequence_obj.executeCursor = False
            sequence_obj.save()
            nextSequence_obj = models.sequence.objects.filter(task=sequence_obj.task).filter(
                priority__gt=sequence_obj.priority).order_by('priority')[0]
            nextSequence_obj.executeCursor = True
            nextSequence_obj.save()
            ret = {
                'role': 1,
                'remark': sequence_obj.remarks
            }
        else:
            ret = {
                'role': 0
            }

        return HttpResponse(json.dumps(ret), "application/json")


# 获取项目的所有分支
@login_required
@require_http_methods(["GET"])
def ajax_load_info(request):
    jenkins_job_name = request.GET.get('jenkins_job_name')
    if jenkins_job_name:
        project = models.project.objects.get(name=jenkins_job_name)
        branches = models.devBranch.objects.filter(project=project)
        branchList = list(branches.values("name"))
        branchListJson = json.dumps(branchList)

        return HttpResponse(branchListJson, "application/json")


@login_required
@require_http_methods(["GET"])
def ajax_get_ip(request):
    project_plan_id = request.GET['id']
    project_plans = models.project_plan.objects.filter(id=project_plan_id)
    if project_plans:
        project_obj = project_plans[0].project
        project_servers = models.project_server.objects.filter(project=project_obj, server__type=1)
        ips = list()
        names = list()
        for i in range(len(project_servers)):
            ips.append(project_servers[i].server.ip)
            names.append(project_servers[i].server.name)
        d = dict()
        d['project_plan_id'] = project_plan_id
        d['ip'] = ips
        d['name'] = names

        return HttpResponse(json.dumps(d), "application/json")


# 释放预发独占锁
@login_required
@csrf_exempt
@require_http_methods(["GET"])
def ajax_get_project(request):
    planId = request.GET['id']
    plan_obj = models.plan.objects.get(id=planId)
    project_plans = models.project_plan.objects.filter(plan=plan_obj)
    d = dict()
    names = list()
    codes = list()
    for i in range(len(project_plans)):
        names.append(project_plans[i].project.name)
        codes.append(project_plans[i].id)
    d['code'] = codes
    d['name'] = names

    return HttpResponse(json.dumps(d), "application/json")


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


# 生产回滚
@login_required
@accept_websocket
def ws_rollback(request):
    if request.is_websocket():
        project_plan_id = request.websocket.wait()
        uniteKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
        project_plan_obj = models.project_plan.objects.get(id=str(project_plan_id, encoding="utf-8"))
        production_members = models.production_member.objects.filter(production=project_plan_obj.plan.production)
        member_obj = models.member.objects.get(user=request.user)
        isMember = False
        buildMessages = []
        flag = True
        for m in range(len(production_members)):
            if member_obj == production_members[m].member:
                isMember = True
        if isMember and member_obj.user.has_perm('mysite.can_deploy_project'):
            task_obj = models.task.objects.get(plan=project_plan_obj.plan)
            sequence_obj = models.sequence.objects.get(task=task_obj, segment__isCheck=True)
            if not sequence_obj.implemented:
                if project_plan_obj.proBuildStatus != 0:
                    if not project_plan_obj.proOnBuilding:
                        pre_project_plans = \
                            models.project_plan.objects.filter(project=project_plan_obj.project, proBuildStatus=1,
                                                               lastPackageId__lt=project_plan_obj.lastPackageId,
                                                               mergeStatus=True).order_by('-lastPackageId')
                        if pre_project_plans:
                            project_obj = project_plan_obj.project
                            deployDetails = models.deployDetail.objects.filter(project_plan=project_plan_obj).order_by(
                                'buildStatus')
                            jenkinsPro_obj = models.jenkinsPro.objects.get(project=project_obj)
                            params = {}
                            params.update(eval(jenkinsPro_obj.param))
                            relVersion = pre_project_plans[0].lastPackageId
                            project_plan_obj.proOnBuilding = True
                            project_plan_obj.save()
                            total = len(deployDetails)
                            buildMessages.append(total)
                            request.websocket.send(json.dumps(buildMessages))
                            deploy_sequence_obj = models.sequence.objects.get(task=task_obj, segment__isDeploy=True)
                            after_deploy_sequences = models.sequence.objects.filter(task=task_obj,
                                                                                    priority__gt=deploy_sequence_obj.priority)
                            for item in range(len(after_deploy_sequences)):
                                if after_deploy_sequences[item].implemented:
                                    after_deploy_sequences[item].implemented = False
                                    after_deploy_sequences[item].save()
                                if after_deploy_sequences[item].executeCursor:
                                    after_deploy_sequences[item].executeCursor = False
                                    after_deploy_sequences[item].save()
                            deploy_sequence_obj.executeCursor = True
                            deploy_sequence_obj.implemented = False
                            deploy_sequence_obj.save()
                            for i in range(len(deployDetails)):
                                server_obj = deployDetails[i].server
                                uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                                params.update(SERVER_IP=server_obj.ip, REL_VERSION=relVersion)
                                pythonJenkins_obj = pythonJenkins(jenkinsPro_obj.name, params)
                                buildNumber = pythonJenkins_obj.realConsole()
                                status = pythonJenkins_obj.deploy()
                                if status:
                                    buildInfo = pythonJenkins_obj.get_building_info()
                                    while not buildInfo:
                                        time.sleep(1)
                                        buildInfo = pythonJenkins_obj.get_building_info()
                                    url = buildInfo['url'] + "console"
                                    buildMessages.append("start_deploy")
                                    buildMessages.append(url)
                                    request.websocket.send(json.dumps(buildMessages))
                                    info = pythonJenkins_obj.get_build_console(buildNumber)
                                    consoleOpt = info['consoleOpt']
                                    isAbort = consoleOpt.find("Finished: ABORTED")
                                    if isAbort == -1:
                                        isSuccess = consoleOpt.find("Finished: SUCCESS")
                                        if isSuccess == -1:
                                            project_plan_obj.proOnBuilding = False
                                            project_plan_obj.save()
                                            res = "项目: %s ,版本号: %s, 服务器: %s, 回滚出错!" % (
                                                project_obj.name, relVersion, server_obj.name)
                                            logger.info(res)
                                            buildMessages.append('deploy_failed')
                                            buildMessages.append(res)
                                            buildMessages.append(uniqueKey)
                                            request.websocket.send(json.dumps(buildMessages))
                                            request.websocket.close()
                                            consoleOpt_obj = models.consoleOpt(type=1, plan=project_plan_obj.plan,
                                                                               project=project_obj,
                                                                               content=consoleOpt,
                                                                               packageId=relVersion,
                                                                               buildStatus=False,
                                                                               deployUser=member_obj,
                                                                               uniqueKey=uniqueKey,
                                                                               uniteKey=uniteKey)
                                            consoleOpt_obj.save()
                                            break
                                        else:
                                            res = "项目: %s ,版本号: %s, 服务器: %s, 回滚完成！" % (
                                                project_obj.name, relVersion, server_obj.name)
                                            logger.info(res)
                                            buildMessages.append(res)
                                            buildMessages.append(uniqueKey)
                                            request.websocket.send(json.dumps(buildMessages))
                                            consoleOpt_obj = models.consoleOpt(type=1, plan=project_plan_obj.plan,
                                                                               project=project_obj,
                                                                               content=consoleOpt,
                                                                               packageId=relVersion,
                                                                               buildStatus=True,
                                                                               deployUser=member_obj,
                                                                               uniqueKey=uniqueKey,
                                                                               uniteKey=uniteKey)
                                            consoleOpt_obj.save()
                                    else:
                                        flag = False
                                        consoleOpt_obj = models.consoleOpt(type=1, plan=project_plan_obj.plan,
                                                                           project=project_obj,
                                                                           content=consoleOpt,
                                                                           packageId=relVersion,
                                                                           buildStatus=False,
                                                                           deployUser=member_obj,
                                                                           uniqueKey=uniqueKey,
                                                                           uniteKey=uniteKey)
                                        consoleOpt_obj.save()
                                        logger.info("项目%s已终止！" % project_obj.name)
                                        break
                                else:
                                    logger.error("Jenkins JOB %s不存在" % jenkinsPro_obj.name)
                                    res = "Jenkins JOB %s不存在" % jenkinsPro_obj.name
                                    buildMessages.append('no_jenkinsJob')
                                    buildMessages.append(res)
                                    request.websocket.send(json.dumps(buildMessages))
                                    request.websocket.close()
                                    flag = False
                                    break
                            project_plan_obj.proOnBuilding = False
                            project_plan_obj.proBuildStatus = 0
                            project_plan_obj.save()
                            taskBuildHistory_obj = models.taskBuildHistory(task=task_obj, uniteKey=uniteKey,
                                                                           deployUser=member_obj)
                            taskBuildHistory_obj.save()
                            if flag:
                                buildMessages.append('deploy_success')
                                res = "项目：%s，回滚版本：%s，回滚完成！" % (project_obj.name, relVersion)
                                buildMessages.append(res)
                                request.websocket.send(json.dumps(buildMessages))
                                request.websocket.close()
                        else:
                            buildMessages.append('first_version')
                            request.websocket.send(json.dumps(buildMessages))
                            request.websocket.close()
                    else:
                        buildMessages.append('on_building')
                        request.websocket.send(json.dumps(buildMessages))
                        request.websocket.close()
                else:
                    buildMessages.append('no_deploy')
                    request.websocket.send(json.dumps(buildMessages))
                    request.websocket.close()
            else:
                buildMessages.append('already_proCheck')
                request.websocket.send(json.dumps(buildMessages))
                request.websocket.close()
        else:
            buildMessages.append('no_role')
            request.websocket.send(json.dumps(buildMessages))
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
                sequence_obj = models.sequence.objects.filter(task=task_obj).get(segment__isMerge=True)
                isMember = False
                buildMessages = []
                for m in range(len(production_members)):
                    if member_obj == production_members[m].member:
                        isMember = True
                if isMember and member_obj.user.has_perm("mysite.can_deploy_project"):
                    buildMessages.append(len(project_plans))
                    request.websocket.send(json.dumps(buildMessages))
                    for i in range(len(project_plans)):
                        project_obj = project_plans[i].project
                        branch_obj = branch(project_obj.project_dir, gitCmd_obj.param)
                        status = branch_obj.merge_branch(project_plans[i].deployBranch, 'master')
                        buildMessages.append("startMerge")
                        if status:
                            project_plans[i].mergeStatus = True
                            project_plans[i].mergeDate = datetime.datetime.now()
                            project_plans[i].save()
                            res = "项目%s合并完成" % project_plans[i].project.name
                            buildMessages.append(res)
                            request.websocket.send(json.dumps(buildMessages))
                            branchDelStatus = branch_obj.delete_branch(project_plans[i].deployBranch)
                            if not branchDelStatus:
                                logger.error('计划：%s，项目：%s，分支：%s删除失败, 请手工删除！' % (
                                    project_plans[i].plan.name, project_obj, project_plans[i].deployBranch))
                        else:
                            res = "项目%s合并冲突或线上分支%s已被删除，请手工处理！" % (
                                project_plans[i].project.name, project_plans[i].deployBranch)
                            buildMessages.append(res)
                            request.websocket.send(json.dumps(buildMessages))
                    buildMessages.append("complete")
                    request.websocket.send(json.dumps(buildMessages))
                    request.websocket.close()
                    sequence_obj.implemented = True
                    sequence_obj.executor = member_obj
                    sequence_obj.executeDate = datetime.datetime.now()
                    sequence_obj.remarks = "已合并"
                    sequence_obj.save()
                else:
                    buildMessages.append("no_role")
                    request.websocket.send(json.dumps(buildMessages))
                    request.websocket.close()


# 查看预发控制台信息
@login_required
def uat_console_opt(request, project_plan_id):
    member_obj = models.member.objects.get(user=request.user)
    if project_plan_id:
        project_plan_obj = models.project_plan.objects.get(id=project_plan_id)
        consoleOpts = models.consoleOpt.objects.filter(project=project_plan_obj.project, plan=project_plan_obj.plan,
                                                       type=0).order_by('-deployTime')

    template = get_template('uatConsoleOpt.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 查看生产发布记录
@login_required
def pro_console_opt(request, project_plan_id):
    member_obj = models.member.objects.get(user=request.user)
    if project_plan_id:
        project_plan_obj = models.project_plan.objects.get(id=project_plan_id)
        consoleOpts = models.consoleOpt.objects.filter(project=project_plan_obj.project, plan=project_plan_obj.plan,
                                                       type=1).order_by('-deployTime')
        task_obj = models.task.objects.get(plan=project_plan_obj.plan)
    template = get_template('proConsoleOpt.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 单个控制台信息查看
@login_required
def single_console_opt(request, uid):
    member_obj = models.member.objects.get(user=request.user)
    if uid:
        consoleOpt_obj = models.consoleOpt.objects.get(uniqueKey=uid)

    template = get_template('single_console_opt.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


# 刷新生产发布记录
@login_required
@accept_websocket
def ws_proConsoleOptRefresh(request):
    if request.is_websocket():
        for taskId in request.websocket:
            if taskId:
                task_obj = models.task.objects.get(id=taskId)
                taskBuildHistories = models.taskBuildHistory.objects.filter(task=task_obj).order_by('deployTime')
                consoleMessages = []
                for i in range(len(taskBuildHistories)):
                    consoleMessages.append("console")
                    consoleMessages.append(taskBuildHistories[i].deployTime)
                    consoleMessages.append(taskBuildHistories[i].category)
                    consoleMessages.append(taskBuildHistories[i].deployUser.name)
                    consoleMessages.append(taskBuildHistories[i].uniteKey)
                request.websocket.send(json.dumps(consoleMessages, cls=DateEncoder))
                request.websocket.close()


# 刷新预发发布记录
@login_required
@accept_websocket
def ws_uatConsoleOptRefresh(request):
    if request.is_websocket():
        for combination in request.websocket:
            if combination:
                projectId = str(combination, encoding="utf-8").split('-')[0]
                planId = str(combination, encoding="utf-8").split('-')[1]
                project_obj = models.project.objects.get(id=projectId)
                plan_obj = models.plan.objects.get(id=planId)
                consoleOpts = models.consoleOpt.objects.filter(plan=plan_obj, project=project_obj, type=0).order_by(
                    'deployTime')
                consoleMessages = []
                for i in range(len(consoleOpts)):
                    consoleMessages.append("console")
                    consoleMessages.append(consoleOpts[i].deployTime)
                    consoleMessages.append(consoleOpts[i].deployUser.name)
                    consoleMessages.append(consoleOpts[i].uniteKey)
                request.websocket.send(json.dumps(consoleMessages, cls=DateEncoder))
                request.websocket.close()


# 单个项目部署
@login_required
@accept_websocket
def ws_proOneProjectDeploy(request):
    if request.is_websocket():
        project_plan_id = request.websocket.wait()
        if project_plan_id:
            uniteKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
            project_plan_obj = models.project_plan.objects.get(id=project_plan_id)
            production_members = models.production_member.objects.filter(production=project_plan_obj.plan.production)
            member_obj = models.member.objects.get(user=request.user)
            task_obj = models.task.objects.get(plan=project_plan_obj.plan)
            isMember = False
            buildMessages = []
            flag = True
            for m in range(len(production_members)):
                if member_obj == production_members[m].member:
                    isMember = True
            if isMember and member_obj.user.has_perm("mysite.can_deploy_project"):
                sequence_obj = models.sequence.objects.get(task=task_obj, segment__isCheck=True)
                if not sequence_obj.implemented:
                    if not project_plan_obj.proOnBuilding:
                        uatBranchCreateDate = int(project_plan_obj.uatBranchCreateDate.strftime('%Y%m%d%H%M'))
                        post_project_plans = models.project_plan.objects.filter(project=project_plan_obj.project,
                                                                                proBuildStatus=1)
                        isBranchOutOfDate = False
                        for item in range(len(post_project_plans)):
                            if post_project_plans[item].mergeDate:
                                post_project_plan_mergeDate = int(
                                    post_project_plans[item].mergeDate.strftime('%Y%m%d%H%M'))
                                if post_project_plan_mergeDate > uatBranchCreateDate:
                                    isBranchOutOfDate = True
                                    break
                            else:
                                continue
                        if not isBranchOutOfDate:
                            project_obj = project_plan_obj.project
                            deployDetails = models.deployDetail.objects.filter(project_plan=project_plan_obj).order_by(
                                'buildStatus')
                            jenkinsPro_obj = models.jenkinsPro.objects.get(project=project_obj)
                            params = {}
                            params.update(eval(jenkinsPro_obj.param))
                            relVersion = project_plan_obj.lastPackageId
                            project_plan_obj.proOnBuilding = True
                            project_plan_obj.save()
                            total = len(deployDetails)
                            buildMessages.append(total)
                            request.websocket.send(json.dumps(buildMessages))
                            if relVersion:
                                for i in range(len(deployDetails)):
                                    server_obj = deployDetails[i].server
                                    uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                                    params.update(SERVER_IP=server_obj.ip, REL_VERSION=relVersion)
                                    pythonJenkins_obj = pythonJenkins(jenkinsPro_obj.name, params)
                                    buildNumber = pythonJenkins_obj.realConsole()
                                    status = pythonJenkins_obj.deploy()
                                    if status:
                                        buildInfo = pythonJenkins_obj.get_building_info()
                                        while not buildInfo:
                                            time.sleep(1)
                                            buildInfo = pythonJenkins_obj.get_building_info()
                                        url = buildInfo['url'] + "console"
                                        buildMessages.append("start_deploy")
                                        buildMessages.append(url)
                                        request.websocket.send(json.dumps(buildMessages))
                                        info = pythonJenkins_obj.get_build_console(buildNumber)
                                        consoleOpt = info['consoleOpt']
                                        isAbort = consoleOpt.find("Finished: ABORTED")
                                        if isAbort == -1:
                                            isSuccess = consoleOpt.find("Finished: SUCCESS")
                                            if isSuccess == -1:
                                                project_plan_obj.proOnBuilding = False
                                                project_plan_obj.proBuildStatus = 2
                                                project_plan_obj.save()
                                                deployDetails[i].buildStatus = False
                                                deployDetails[i].save()
                                                res = "项目: %s ,版本号: %s, 服务器: %s, 发布出错!" % (
                                                    project_obj.name, relVersion, server_obj.name)
                                                logger.info(res)
                                                buildMessages.append('deploy_failed')
                                                buildMessages.append(res)
                                                buildMessages.append(uniqueKey)
                                                request.websocket.send(json.dumps(buildMessages))
                                                request.websocket.close()
                                                consoleOpt_obj = models.consoleOpt(type=1, plan=project_plan_obj.plan,
                                                                                   project=project_obj,
                                                                                   content=consoleOpt,
                                                                                   packageId=relVersion,
                                                                                   buildStatus=False,
                                                                                   deployUser=member_obj,
                                                                                   uniqueKey=uniqueKey,
                                                                                   uniteKey=uniteKey)
                                                consoleOpt_obj.save()
                                                break
                                            else:
                                                res = "项目: %s ,版本号: %s, 服务器: %s, 发布完成！" % (
                                                    project_obj.name, relVersion, server_obj.name)
                                                logger.info(res)
                                                buildMessages.append(res)
                                                buildMessages.append(uniqueKey)
                                                request.websocket.send(json.dumps(buildMessages))
                                                consoleOpt_obj = models.consoleOpt(type=1, plan=project_plan_obj.plan,
                                                                                   project=project_obj,
                                                                                   content=consoleOpt,
                                                                                   packageId=relVersion,
                                                                                   buildStatus=True,
                                                                                   deployUser=member_obj,
                                                                                   uniqueKey=uniqueKey,
                                                                                   uniteKey=uniteKey)
                                                consoleOpt_obj.save()
                                                deployDetails[i].buildStatus = True
                                                deployDetails[i].save()
                                        else:
                                            flag = False
                                            logger.info("项目%s已终止！" % project_obj.name)
                                            consoleOpt_obj = models.consoleOpt(type=1, plan=project_plan_obj.plan,
                                                                               project=project_obj,
                                                                               content=consoleOpt,
                                                                               packageId=relVersion,
                                                                               buildStatus=False,
                                                                               deployUser=member_obj,
                                                                               uniqueKey=uniqueKey,
                                                                               uniteKey=uniteKey)
                                            consoleOpt_obj.save()
                                            break
                                    else:
                                        logger.error("Jenkins JOB %s不存在" % jenkinsPro_obj.name)
                                        res = "Jenkins JOB %s不存在" % jenkinsPro_obj.name
                                        buildMessages.append('no_jenkinsJob')
                                        buildMessages.append(res)
                                        request.websocket.send(json.dumps(buildMessages))
                                        request.websocket.close()
                                        flag = False
                                        break
                                project_plan_obj.proOnBuilding = False
                                project_plan_obj.save()
                                fail_deploys = models.deployDetail.objects.filter(project_plan=project_plan_obj,
                                                                                  buildStatus=False)
                                taskBuildHistory_obj = models.taskBuildHistory(task=task_obj, uniteKey=uniteKey,
                                                                               deployUser=member_obj)
                                taskBuildHistory_obj.save()
                                if flag:
                                    if not fail_deploys:
                                        project_plan_obj.proBuildStatus = 1
                                        project_plan_obj.save()
                                        res = "项目：%s，部署完成！" % project_obj.name
                                        buildMessages.append('deploy_success')
                                        buildMessages.append(res)
                                        request.websocket.send(json.dumps(buildMessages))
                                        project_plans = models.project_plan.objects.filter(
                                            plan=project_plan_obj.plan).filter(~Q(proBuildStatus=1))
                                        if not project_plans:
                                            sequence_obj = models.sequence.objects.filter(task=task_obj).get(
                                                segment__isDeploy=True)
                                            sequence_obj.implemented = True
                                            sequence_obj.executor = member_obj
                                            sequence_obj.executeDate = datetime.datetime.now()
                                            sequence_obj.remarks = "已部署"
                                            sequence_obj.executeCursor = False
                                            sequence_obj.save()
                                            nextSequence_obj = models.sequence.objects.filter(task=sequence_obj.task,
                                                                                              priority__gt=sequence_obj.priority).order_by(
                                                'priority')[0]
                                            nextSequence_obj.executeCursor = True
                                            nextSequence_obj.save()
                                            buildMessages.append('sequence_success')
                                            request.websocket.send(json.dumps(buildMessages))
                                        request.websocket.close()
                            else:
                                logger.info("项目：%s，没有发布版本号，请先在预发创建，或者没有发布服务器，请核实！" % project_obj.name)
                                res = "项目：%s，没有发布版本号，请先在预发创建，或者没有发布服务器，请核实！" % project_obj.name
                                buildMessages.append(res)
                                buildMessages.append('no_reversion')
                                request.websocket.send(json.dumps(buildMessages))
                                request.websocket.close()
                        else:
                            buildMessages.append('out_of_date')
                            request.websocket.send(json.dumps(buildMessages))
                            request.websocket.close()
                    else:
                        buildMessages.append('on_building')
                        request.websocket.send(json.dumps(buildMessages))
                        request.websocket.close()
                else:
                    buildMessages.append('already_proCheck')
                    request.websocket.send(json.dumps(buildMessages))
                    request.websocket.close()
            else:
                buildMessages.append('no_role')
                request.websocket.send(json.dumps(buildMessages))
                request.websocket.close()


# 重新上预发
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def ajax_restartUatDeploy(request):
    plan_obj = models.plan.objects.get(id=request.POST['planId'])
    production_members = models.production_member.objects.filter(production=plan_obj.production)
    member_obj = models.member.objects.get(user=request.user)
    isMember = False
    for m in range(len(production_members)):
        if member_obj == production_members[m].member:
            isMember = True
    if isMember and member_obj.user.has_perm('mysite.can_check_project'):
        task_obj = models.task.objects.filter(plan=plan_obj)
        if task_obj:
            sequence_obj = models.sequence.objects.get(task=task_obj, segment__isCheck=True)
            if not sequence_obj.implemented:
                plan_obj.uatCheck = False
                plan_obj.uatRemark = None
                plan_obj.uatCheckDate = None
                plan_obj.uatCheckMember = None
                plan_obj.save()
                deploy_sequence_obj = models.sequence.objects.get(task=task_obj, segment__isDeploy=True)
                if deploy_sequence_obj.implemented:
                    deploy_sequence_obj.implemented = False
                    deploy_sequence_obj.executeCursor = True
                    deploy_sequence_obj.executeDate = None
                    deploy_sequence_obj.executor = None
                    deploy_sequence_obj.remarks = None
                    deploy_sequence_obj.save()
                    sequences = models.sequence.objects.filter(task=task_obj, priority__gt=deploy_sequence_obj.priority)
                    for i in range(len(sequences)):
                        sequences[i].executeCursor = False
                        sequences[i].implemented = False
                        sequences[i].executeDate = None
                        sequences[i].executor = None
                        sequences[i].remarks = None
                        sequences[i].save()

                ret = {
                    'role': True,
                    'proCheck': False
                }
            else:
                ret = {
                    'role': True,
                    'proCheck': True
                }
        else:
            if plan_obj.uatCheck:
                plan_obj.uatCheck = False
                plan_obj.uatRemark = None
                plan_obj.uatCheckDate = None
                plan_obj.uatCheckMember = None
                plan_obj.save()

                ret = {
                    'role': True,
                    'uatCheck': True
                }
            else:
                ret = {
                    'role': True,
                    'uatCheck': False
                }

    else:
        ret = {
            'role': False
        }

    return HttpResponse(json.dumps(ret), "application/json")


# 选择部署节点
@login_required
@accept_websocket
def ws_selectNodesDeploy(request):
    if request.is_websocket():
        ips = request.websocket.wait()
        uniteKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
        project_plan_obj = models.project_plan.objects.get(id=str(ips, encoding="utf-8").split(',')[0])
        production_members = models.production_member.objects.filter(production=project_plan_obj.plan.production)
        member_obj = models.member.objects.get(user=request.user)
        task_obj = models.task.objects.get(plan=project_plan_obj.plan)
        isMember = False
        buildMessages = list()
        flag = True
        for m in range(len(production_members)):
            if member_obj == production_members[m].member:
                isMember = True
        if isMember and member_obj.user.has_perm('mysite.can_deploy_project'):
            sequence_obj = models.sequence.objects.get(task=task_obj, segment__isCheck=True)
            if not sequence_obj.implemented:
                if not project_plan_obj.proOnBuilding:
                    uatBranchCreateDate = int(project_plan_obj.uatBranchCreateDate.strftime('%Y%m%d%H%M'))
                    post_project_plans = models.project_plan.objects.filter(project=project_plan_obj.project,
                                                                            proBuildStatus=1)
                    isBranchOutOfDate = False
                    for item in range(len(post_project_plans)):
                        if post_project_plans[item].mergeDate:
                            post_project_plan_mergeDate = int(post_project_plans[item].mergeDate.strftime('%Y%m%d%H%M'))
                            if post_project_plan_mergeDate > uatBranchCreateDate:
                                isBranchOutOfDate = True
                                break
                        else:
                            continue
                    if not isBranchOutOfDate:
                        jenkinsPro_obj = models.jenkinsPro.objects.get(project=project_plan_obj.project)
                        params = dict()
                        params.update(eval(jenkinsPro_obj.param))
                        relVersion = project_plan_obj.lastPackageId
                        project_plan_obj.proOnBuilding = True
                        project_plan_obj.save()
                        servers = str(ips, encoding="utf-8").split(',')[1:]
                        total = len(servers)
                        buildMessages.append(total)
                        request.websocket.send(json.dumps(buildMessages))
                        if relVersion:
                            if servers:
                                fail_deploys = True
                                for i in servers:
                                    server_obj = models.server.objects.get(ip=i)
                                    deployDetail_obj = models.deployDetail.objects.get(project_plan=project_plan_obj,
                                                                                       server=server_obj)
                                    uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                                    params.update(SERVER_IP=server_obj.ip, REL_VERSION=relVersion)
                                    pythonJenkins_obj = pythonJenkins(jenkinsPro_obj.name, params)
                                    buildNumber = pythonJenkins_obj.realConsole()
                                    status = pythonJenkins_obj.deploy()
                                    if status:
                                        buildInfo = pythonJenkins_obj.get_building_info()
                                        while not buildInfo:
                                            time.sleep(1)
                                            buildInfo = pythonJenkins_obj.get_building_info()
                                        url = buildInfo['url'] + "console"
                                        buildMessages.append("start_deploy")
                                        buildMessages.append(url)
                                        request.websocket.send(json.dumps(buildMessages))
                                        info = pythonJenkins_obj.get_build_console(buildNumber)
                                        consoleOpt = info['consoleOpt']
                                        isAbort = consoleOpt.find("Finished: ABORTED")
                                        if isAbort == -1:
                                            isSuccess = consoleOpt.find("Finished: SUCCESS")
                                            if isSuccess == -1:
                                                fail_deploys = False
                                                project_plan_obj.proOnBuilding = False
                                                project_plan_obj.proBuildStatus = 2
                                                project_plan_obj.save()
                                                deployDetail_obj.buildStatus = False
                                                deployDetail_obj.save()
                                                res = "项目: %s ,版本号: %s, 服务器: %s, 发布出错!" % (
                                                    project_plan_obj.project.name, relVersion, server_obj.name)
                                                logger.info(res)
                                                buildMessages.append('deploy_failed')
                                                buildMessages.append(res)
                                                buildMessages.append(uniqueKey)
                                                request.websocket.send(json.dumps(buildMessages))
                                                request.websocket.close()
                                                consoleOpt_obj = models.consoleOpt(type=1, plan=project_plan_obj.plan,
                                                                                   project=project_plan_obj.project,
                                                                                   content=consoleOpt,
                                                                                   packageId=relVersion,
                                                                                   buildStatus=False,
                                                                                   deployUser=member_obj,
                                                                                   uniqueKey=uniqueKey,
                                                                                   uniteKey=uniteKey)
                                                consoleOpt_obj.save()
                                                break
                                            else:
                                                res = "项目: %s ,版本号: %s, 服务器: %s, 发布完成！" % (
                                                    project_plan_obj.project.name, relVersion, server_obj.name)
                                                logger.info(res)
                                                buildMessages.append(res)
                                                buildMessages.append(uniqueKey)
                                                request.websocket.send(json.dumps(buildMessages))
                                                consoleOpt_obj = models.consoleOpt(type=1, plan=project_plan_obj.plan,
                                                                                   project=project_plan_obj.project,
                                                                                   content=consoleOpt,
                                                                                   packageId=relVersion,
                                                                                   buildStatus=True,
                                                                                   deployUser=member_obj,
                                                                                   uniqueKey=uniqueKey,
                                                                                   uniteKey=uniteKey)
                                                consoleOpt_obj.save()
                                                deployDetail_obj.buildStatus = True
                                                deployDetail_obj.save()
                                        else:
                                            flag = False
                                            consoleOpt_obj = models.consoleOpt(type=1, plan=project_plan_obj.plan,
                                                                               project=project_plan_obj.project,
                                                                               content=consoleOpt,
                                                                               packageId=relVersion,
                                                                               buildStatus=False,
                                                                               deployUser=member_obj,
                                                                               uniqueKey=uniqueKey,
                                                                               uniteKey=uniteKey)
                                            consoleOpt_obj.save()
                                            logger.info("项目%s已终止发布！" % project_plan_obj.project.name)
                                            break
                                    else:
                                        logger.error("Jenkins JOB %s不存在" % jenkinsPro_obj.name)
                                        res = "Jenkins JOB %s不存在" % jenkinsPro_obj.name
                                        buildMessages.append('no_jenkinsJob')
                                        buildMessages.append(res)
                                        request.websocket.send(json.dumps(buildMessages))
                                        request.websocket.close()
                                        flag = False
                                        break
                                project_plan_obj.proOnBuilding = False
                                project_plan_obj.save()
                                taskBuildHistory_obj = models.taskBuildHistory(task=task_obj, uniteKey=uniteKey,
                                                                               deployUser=member_obj)
                                taskBuildHistory_obj.save()

                                if flag:
                                    if fail_deploys:
                                        res = "项目：%s，部署完成！" % project_plan_obj.project.name
                                        buildMessages.append('deploy_success')
                                        buildMessages.append(res)
                                        request.websocket.send(json.dumps(buildMessages))
                                        all_fail_deploys = models.deployDetail.objects.filter(
                                            project_plan=project_plan_obj,
                                            buildStatus=False)
                                        if not all_fail_deploys:
                                            project_plan_obj.proBuildStatus = 1
                                            project_plan_obj.save()
                                        project_plans = models.project_plan.objects.filter(
                                            plan=project_plan_obj.plan).filter(~Q(proBuildStatus=1))
                                        if not project_plans:
                                            sequence_obj = models.sequence.objects.filter(task=task_obj).get(
                                                segment__isDeploy=True)
                                            sequence_obj.implemented = True
                                            sequence_obj.executor = member_obj
                                            sequence_obj.executeDate = datetime.datetime.now()
                                            sequence_obj.remarks = "已部署"
                                            sequence_obj.executeCursor = False
                                            sequence_obj.save()
                                            nextSequence_obj = models.sequence.objects.filter(task=sequence_obj.task,
                                                                                              priority__gt=sequence_obj.priority).order_by(
                                                'priority')[0]
                                            nextSequence_obj.executeCursor = True
                                            nextSequence_obj.save()
                                            buildMessages.append('sequence_success')
                                            request.websocket.send(json.dumps(buildMessages))
                                        request.websocket.close()
                        else:
                            logger.info("项目：%s，没有发布版本号，请先在预发创建，或者没有发布服务器，请核实！" % project_plan_obj.project.name)
                            res = "项目：%s，没有发布版本号，请先在预发创建，或者没有发布服务器，请核实！" % project_plan_obj.project.name
                            buildMessages.append(res)
                            buildMessages.append('no_reversion')
                            request.websocket.send(json.dumps(buildMessages))
                            request.websocket.close()
                    else:
                        buildMessages.append('out_of_date')
                        request.websocket.send(json.dumps(buildMessages))
                        request.websocket.close()
                else:
                    buildMessages.append('on_building')
                    request.websocket.send(json.dumps(buildMessages))
                    request.websocket.close()
            else:
                buildMessages.append('already_proCheck')
                request.websocket.send(json.dumps(buildMessages))
                request.websocket.close()
        else:
            buildMessages.append('no_role')
            request.websocket.send(json.dumps(buildMessages))
            request.websocket.close()


# 生产终止发布
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def ajax_stopDeploy(request):
    project_plan_id = request.POST['id']
    project_plan_obj = models.project_plan.objects.get(id=project_plan_id)
    production_members = models.production_member.objects.filter(production=project_plan_obj.plan.production)
    member_obj = models.member.objects.get(user=request.user)
    isMember = False
    for m in range(len(production_members)):
        if member_obj == production_members[m].member:
            isMember = True
    if isMember and member_obj.user.has_perm('mysite.can_deploy_project'):
        if project_plan_obj.proOnBuilding:
            project_plan_obj.proOnBuilding = False
            project_plan_obj.save()
            proJenkins_obj = models.jenkinsPro.objects.get(project=project_plan_obj.project)
            pythonJenkins_obj = pythonJenkins(proJenkins_obj.name, {})
            buildNumber = pythonJenkins_obj.get_building_info()['number']
            if buildNumber:
                info = pythonJenkins_obj.stop_build(buildNumber)
                consoleOpt = info['consoleOpt']
                isAbort = consoleOpt.find("Finished: ABORTED")
                isSuccess = consoleOpt.find("Finished: SUCCESS")
                if isAbort == -1:
                    if isSuccess == -1:
                        ret = {
                            'role': True,
                            'stop': False,
                            'build': False,
                            'project': project_plan_obj.project.name
                        }
                    else:
                        ret = {
                            'role': True,
                            'stop': False,
                            'build': True,
                            'project': project_plan_obj.project.name
                        }
                else:
                    ret = {
                        'role': True,
                        'stop': True,
                        'build': False,
                        'project': project_plan_obj.project.name
                    }
            else:
                ret = {
                    'role': True,
                    'start': False,
                }
        else:
            ret = {
                'role': True,
                'start': False
            }
    else:
        ret = {
            'role': False
        }

    return HttpResponse(json.dumps(ret), "application/json")


# 释放预发独占锁
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def ajax_releaseExclusiveKey(request):
    ids = request.POST.getlist('ids')
    if ids:
        project_plan_obj = models.project_plan.objects.get(id=ids[0])
        production_members = models.production_member.objects.filter(production=project_plan_obj.plan.production)
        member_obj = models.member.objects.get(user=request.user)
        isMember = False
        for m in range(len(production_members)):
            if member_obj == production_members[m].member:
                isMember = True
        if isMember and member_obj.user.has_perm('mysite.can_check_project'):
            for project_plan_id in ids:
                project_plan_obj = models.project_plan.objects.get(id=project_plan_id)
                if project_plan_obj.exclusiveKey:
                    project_plan_obj.exclusiveKey = False
                    project_plan_obj.save()
            ret = {
                'role': True,
                'release': True
            }
        else:
            ret = {
                'role': False
            }
        return HttpResponse(json.dumps(ret), "application/json")


# 生产验收
@login_required
@accept_websocket
def ws_checkSuccess(request):
    if request.is_websocket():
        for combination in request.websocket:
            if combination:
                remark = str(combination, encoding="utf-8").split('-')[0]
                sequenceId = str(combination, encoding="utf-8").split('-')[1]
                if sequenceId:
                    sequence_obj = models.sequence.objects.get(id=sequenceId)
                    production_members = models.production_member.objects.filter(
                        production=sequence_obj.task.plan.production)
                    member_obj = models.member.objects.get(user=request.user)
                    isMember = False
                    buildMessages = []
                    for m in range(len(production_members)):
                        if member_obj == production_members[m].member:
                            isMember = True
                    if isMember and member_obj.user.has_perm('mysite.can_check_project'):
                        sequence_obj.implemented = True
                        sequence_obj.remarks = remark
                        sequence_obj.executor = member_obj
                        sequence_obj.executeDate = datetime.datetime.now()
                        sequence_obj.executeCursor = False
                        sequence_obj.save()
                        project_plans = models.project_plan.objects.filter(plan=sequence_obj.task.plan)
                        total = len(project_plans)
                        buildMessages.append(remark)
                        buildMessages.append(total)
                        request.websocket.send(json.dumps(buildMessages))
                        mail_to = []
                        for k in range(len(production_members)):
                            mail_to.append(production_members[k].member.user.email)
                        email_proCheck(sequence_obj, mail_from, mail_to, mail_cc, email_url_obj)

                        for i in range(len(project_plans)):
                            branch_obj = branch(project_plans[i].project.project_dir, gitCmd_obj.param)
                            status = branch_obj.create_tag(project_plans[i].deployBranch)
                            if status:
                                res = "项目%s，预发分支%s,tag创建成功！" % (
                                    project_plans[i].project.name, project_plans[i].uatBranch)
                            else:
                                res = "项目%s，预发分支%s,tag创建失败！" % (
                                    project_plans[i].project.name, project_plans[i].uatBranch)
                            logger.info(res)
                            buildMessages.append(res)
                            request.websocket.send(json.dumps(buildMessages))
                        request.websocket.close()
                        try:
                            nextSequence_obj = models.sequence.objects.filter(task=sequence_obj.task).filter(
                                priority__gt=sequence_obj.priority).order_by('priority')[0]
                            nextSequence_obj.executeCursor = True
                            nextSequence_obj.save()
                        except IndexError:
                            print("已是最后一个环节")
                    else:
                        buildMessages.append('no_role')
                        request.websocket.send(json.dumps(buildMessages))
                        request.websocket.close()
