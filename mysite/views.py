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

# 定时获取dev_branch
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
    plans = models.plan.objects.filter(isSubPlan=False, production__member=member_obj).order_by('-createDate')

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
            project_plan_obj = models.project_plan(plan=plan_obj, project=project_obj, devBranch=devBranchList[j],
                                                   order=j)
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
        sub_plans = models.plan.objects.filter(fatherPlanId=plan_obj.id)
        father_plans = models.plan.objects.filter(subPlanId=plan_obj.id)
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


# 创建子计划
@login_required
def createSubPlan(request):
    father_plan_obj = models.plan.objects.get(id=request.GET['pid'])
    if father_plan_obj:
        projects = models.project.objects.all()
        member_obj = models.member.objects.get(user=request.user)
        production_obj = father_plan_obj.production
        if request.method == 'POST':
            production_members = models.production_member.objects.filter(production=production_obj)
            isMember = False
            for m in range(len(production_members)):
                if member_obj == production_members[m].member:
                    isMember = True
            if isMember and member_obj.user.has_perm('mysite.add_plan'):
                projectList = request.POST.getlist('project')
                devBranchList = request.POST.getlist('devBranch')
                kind_obj = father_plan_obj.kind
                plan_obj = models.plan(name=request.POST['title'], description=request.POST['desc'], kind=kind_obj,
                                       fatherPlanId=father_plan_obj.id, isSubPlan=True, production=production_obj,
                                       createUser=member_obj, createDate=datetime.datetime.now())
                plan_obj.save()
                father_plan_obj.subPlanId = plan_obj.id
                father_plan_obj.save()
                for j in range(len(projectList)):
                    project_obj = models.project.objects.get(name=projectList[j])
                    # dev_branch_obj = models.devBranch.objects.filter(project=project_obj).get(name=devBranchList[j])
                    project_plan_obj = models.project_plan(plan=plan_obj, project=project_obj, devBranch=devBranchList[j],
                                                           order=j)
                    project_plan_obj.save()
                    project_servers = models.project_server.objects.filter(project=project_obj).filter(server__type=1)
                    for i in range(len(project_servers)):
                        deployDetail_obj = models.deployDetail(project_plan=project_plan_obj,
                                                               server=project_servers[i].server)
                        deployDetail_obj.save()

                project_plans = models.project_plan.objects.filter(plan=plan_obj)
                production_members = models.production_member.objects.filter(production=production_obj)
                mail_to = []
                for k in range(len(production_members)):
                    mail_to.append(production_members[k].member.user.email)
                email_createPlan(project_plans, mail_from, mail_to, mail_cc, email_url_obj)
                return HttpResponseRedirect('/planDetail?pid=%s' % plan_obj.id)

    template = get_template('createSubPlan.html')
    html = template.render(context=locals(), request=request)
    return HttpResponse(html)


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
            if plan_obj.id:
                sub_plans = models.plan.objects.filter(fatherPlanId=plan_obj.id)
                for i in range(len(sub_plans)):
                    sub_plans[i].delete()

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
        project_plans = models.project_plan.objects.filter(plan=task_obj.plan).order_by('order')
        upToImplementSequence = models.sequence.objects.filter(task=task_obj).get(executeCursor=1)
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


# 预发部署
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
                if not project_plans[j].uatBuildStatus:
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
            option = request.POST.get('radio')
            if option == "option1":
                uatBranch = request.POST.get('uatBranch')
                status = True
            else:
                t = datetime.datetime.now()
                branchCode = str(t.year) + str(t.month) + str(t.day) + str(t.hour) + str(t.minute)
                uatBranch = "uat-"
                uatBranch += branchCode
                branch_obj.create_branch(uatBranch)
                status = branch_obj.merge_branch(project_plan_obj.devBranch, uatBranch)

            if status:
                if project_plan_obj.uatBranch:
                    delStatus = branch_obj.delete_branch(project_plan_obj.uatBranch)
                    if not delStatus:
                        logger.info("原预发分支%s删除失败！" % project_plan_obj.uatBranch)
                project_plan_obj.uatBranch = uatBranch
                project_plan_obj.save()
                res = "预发分支：%s创建成功！" % uatBranch
                ret = {
                    'role': 1,
                    'result': 1,
                    'res': res,
                    'uatBranch': uatBranch
                }
            else:
                res = "预发分支：%s创建失败,分支合并冲突，请手工处理！" % uatBranch
                ret = {
                    'role': 1,
                    'result': 0,
                    'res': res
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
            sequence_obj.implemented = 1
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


# 任务验收通过
@login_required
@csrf_exempt
def ajax_checkSuccess(request):
    sequenceId = request.POST.get('sequenceId')
    if sequenceId:
        sequence_obj = models.sequence.objects.get(id=sequenceId)
        production_members = models.production_member.objects.filter(production=sequence_obj.task.plan.production)
        member_obj = models.member.objects.get(user=request.user)
        isMember = False
        for m in range(len(production_members)):
            if member_obj == production_members[m].member:
                isMember = True
        if isMember and member_obj.user.has_perm('mysite.can_check_project'):
            sequence_obj.implemented = True
            sequence_obj.remarks = request.POST['remark']
            sequence_obj.executor = member_obj
            sequence_obj.executeDate = datetime.datetime.now()
            sequence_obj.executeCursor = False
            sequence_obj.save()
            project_plans = models.project_plan.objects.filter(plan=sequence_obj.task.plan)
            for i in range(len(project_plans)):
                branch_obj = branch(project_plans[i].project.project_dir, gitCmd_obj.param)
                status = branch_obj.create_tag(project_plans[i].deployBranch)
                if status:
                    logger.info("项目%s，预发分支%s,tag创建成功！" % (project_plans[i].project.name, project_plans[i].uatBranch))
                if project_plans[i].exclusiveKey:
                    project_plans[i].exclusiveKey = False
                    project_plans[i].save()
            try:
                nextSequence_obj = models.sequence.objects.filter(task=sequence_obj.task).filter(
                    priority__gt=sequence_obj.priority).order_by('priority')[0]
                nextSequence_obj.executeCursor = True
                nextSequence_obj.save()
            except IndexError:
                print("已是最后一个环节")
            ret = {
                'role': 1,
                'remark': sequence_obj.remarks
            }

            mail_to = []
            for k in range(len(production_members)):
                mail_to.append(production_members[k].member.user.email)
            email_proCheck(sequence_obj, mail_from, mail_to, mail_cc, email_url_obj)
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
                    proBuildStatus=False).order_by('order')
                production_members = models.production_member.objects.filter(production=task_obj.plan.production)
                member_obj = models.member.objects.get(user=request.user)
                sequence_obj = models.sequence.objects.filter(task=task_obj).get(segment__isDeploy=True)
                isMember = False
                for m in range(len(production_members)):
                    if member_obj == production_members[m].member:
                        isMember = True
                buildMessages = []
                if isMember and member_obj.user.has_perm("mysite.can_deploy_project"):
                    if not task_obj.onBuilding:
                        projectBean_obj = projectBean(project_plans, gitCmd_obj.param)
                        total = projectBean_obj.countDeploySum(1, 0)
                        buildMessages.append(total)
                        request.websocket.send(json.dumps(buildMessages))
                        failedProjects = []
                        task_obj.onBuilding = True
                        task_obj.save()
                        for i in range(len(project_plans)):
                            if len(failedProjects) == 0:
                                all_project_plans = models.project_plan.objects.filter(plan=task_obj.plan)
                                for n in range(len(all_project_plans)):
                                    if all_project_plans[n].cursor:
                                        all_project_plans[n].cursor = False
                                        all_project_plans[n].save()
                                project_plans[i].cursor = True
                                project_plans[i].save()
                                project_obj = project_plans[i].project
                                deployDetails = models.deployDetail.objects.filter(
                                    project_plan=project_plans[i]).order_by(
                                    'buildStatus')
                                jenkinsPro_obj = models.jenkinsPro.objects.get(project=project_obj)
                                param = eval(jenkinsPro_obj.param)
                                relVersion = project_plans[i].lastPackageId
                                for j in range(len(deployDetails)):
                                    if len(failedProjects) == 0:
                                        params = {}
                                        params.update(param)
                                        server_obj = deployDetails[j].server
                                        if relVersion and sequence_obj:
                                            uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                                            params.update(SERVER_IP=server_obj.ip, REL_VERSION=relVersion)
                                            pythonJenkins_obj = pythonJenkins(jenkinsPro_obj.name, params)
                                            buildNumber = pythonJenkins_obj.realConsole()
                                            url = "http://jenkinspro.bestjlb.cn/view/PRO-Server/job/" + jenkinsPro_obj.name + "/" + str(
                                                buildNumber) + "/console"
                                            buildMessages.append('url')
                                            buildMessages.append(url)
                                            request.websocket.send(json.dumps(buildMessages))
                                            info = pythonJenkins_obj.deploy()
                                            consoleOpt = info['consoleOpt']
                                            isSuccess = consoleOpt.find("Finished: SUCCESS")
                                            if isSuccess == -1:
                                                project_plans[i].proBuildStatus = False
                                                project_plans[i].save()
                                                deployDetails[j].buildStatus = False
                                                deployDetails[j].save()
                                                res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 发布出错!" % \
                                                      (task_obj.name, project_obj.name, relVersion, server_obj.name)
                                                logger.info(res)
                                                buildMessages.append(res)
                                                buildMessages.append(uniqueKey)
                                                buildMessages.append('deploy_failed')
                                                request.websocket.send(json.dumps(buildMessages))
                                                request.websocket.close()
                                                consoleOpt_obj = models.consoleOpt(type=1, plan=task_obj.plan,
                                                                                   project=project_obj,
                                                                                   content=consoleOpt,
                                                                                   packageId=relVersion,
                                                                                   buildStatus=False,
                                                                                   deployUser=member_obj,
                                                                                   uniqueKey=uniqueKey,
                                                                                   uniteKey=uniteKey)
                                                consoleOpt_obj.save()
                                                failedProjects.append(project_obj.name)
                                                break
                                            else:
                                                res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 发布完成！" % (
                                                    task_obj.name, project_obj.name, relVersion, server_obj.name)
                                                logger.info(res)
                                                buildMessages.append(res)
                                                buildMessages.append(uniqueKey)
                                                request.websocket.send(json.dumps(buildMessages))
                                                consoleOpt_obj = models.consoleOpt(type=1, plan=task_obj.plan,
                                                                                   project=project_obj,
                                                                                   content=consoleOpt,
                                                                                   packageId=relVersion,
                                                                                   buildStatus=True,
                                                                                   deployUser=member_obj,
                                                                                   uniqueKey=uniqueKey,
                                                                                   uniteKey=uniteKey)
                                                consoleOpt_obj.save()
                                                project_plans[i].proBuildStatus = True
                                                project_plans[i].save()
                                                deployDetails[j].buildStatus = True
                                                deployDetails[j].save()
                                        else:
                                            logger.info("项目：%s，没有发布版本号，请先在预发创建，或者没有发布服务器，请核实！" % project_obj.name)
                                            res = "项目：%s，没有发布版本号，请先在预发创建，或者没有发布服务器，请核实！" % project_obj.name
                                            buildMessages.append(res)
                                            buildMessages.append('no_reversion')
                                            request.websocket.send(json.dumps(buildMessages))
                                            request.websocket.close()
                                            failedProjects.append(project_obj.name)
                                            break
                                    else:
                                        task_obj.onBuilding = False
                                        task_obj.save()
                                        break
                            else:
                                task_obj.onBuilding = False
                                task_obj.save()
                                break
                        task_obj.onBuilding = False
                        task_obj.save()
                        taskBuildHistory_obj = models.taskBuildHistory(task=task_obj, uniteKey=uniteKey,
                                                                       deployUser=member_obj)
                        taskBuildHistory_obj.save()
                        fail_project_plans = models.project_plan.objects.filter(plan=task_obj.plan,
                                                                                proBuildStatus=False)
                        if len(fail_project_plans) == 0:
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
                            res = "任务：%s，部署完成！" % task_obj.name
                            buildMessages.append(res)
                            buildMessages.append('deploy_success')
                            request.websocket.send(json.dumps(buildMessages))
                            request.websocket.close()
                    else:
                        buildMessages.append('on_building')
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
                    proBuildStatus=False).order_by('order')
                sequence_obj = models.sequence.objects.filter(task=task_obj).get(segment__isDeploy=True)
                production_members = models.production_member.objects.filter(production=task_obj.plan.production)
                member_obj = models.member.objects.get(user=request.user)
                isMember = False
                for m in range(len(production_members)):
                    if member_obj == production_members[m].member:
                        isMember = True
                buildMessages = []
                if isMember and member_obj.user.has_perm("mysite.can_deploy_project"):
                    order = 0
                    for i in range(len(project_plans)):
                        if project_plans[i].cursor:
                            order = project_plans[i].order
                            break
                    project_plans_news = project_plans.filter(order__gte=order).order_by('order')
                    projectBean_obj = projectBean(project_plans_news, gitCmd_obj.param)
                    total = projectBean_obj.countDeploySum(1, order)
                    buildMessages.append(total)
                    request.websocket.send(json.dumps(buildMessages))
                    failedProjects = []
                    task_obj.onBuilding = True
                    task_obj.save()
                    for j in range(len(project_plans_news)):
                        if len(failedProjects) == 0:
                            all_project_plans = models.project_plan.objects.filter(plan=task_obj.plan)
                            for n in range(len(all_project_plans)):
                                if all_project_plans[n].cursor:
                                    all_project_plans[n].cursor = False
                                    all_project_plans[n].save()
                            project_plans_news[j].cursor = True
                            project_plans_news[j].save()
                            project_obj = project_plans_news[j].project
                            deployDetails = models.deployDetail.objects.filter(
                                project_plan=project_plans_news[j]).order_by(
                                'buildStatus')
                            project_servers = models.project_server.objects.filter(project=project_obj)
                            jenkinsPro_obj = models.jenkinsPro.objects.get(project=project_obj)
                            param = eval(jenkinsPro_obj.param)
                            relVersion = project_plans_news[j].lastPackageId
                            for k in range(len(deployDetails)):
                                if len(failedProjects) == 0:
                                    params = {}
                                    params.update(param)
                                    server_obj = deployDetails[k].server
                                    if relVersion and server_obj:
                                        uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                                        params.update(SERVER_IP=server_obj.ip, REL_VERSION=relVersion)
                                        pythonJenkins_obj = pythonJenkins(jenkinsPro_obj.name, params)
                                        buildNumber = pythonJenkins_obj.realConsole()
                                        url = "http://jenkinspro.bestjlb.cn/view/PRO-Server/job/" + jenkinsPro_obj.name + "/" + str(
                                            buildNumber) + "/console"
                                        buildMessages.append('url')
                                        buildMessages.append(url)
                                        request.websocket.send(json.dumps(buildMessages))
                                        info = pythonJenkins_obj.deploy()
                                        consoleOpt = info['consoleOpt']
                                        isSuccess = consoleOpt.find("Finished: SUCCESS")
                                        if isSuccess == -1:
                                            project_plans_news[j].proBuildStatus = False
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
                                            consoleOpt_obj = models.consoleOpt(type=1, plan=task_obj.plan,
                                                                               project=project_obj,
                                                                               content=consoleOpt, packageId=relVersion,
                                                                               buildStatus=False, deployUser=member_obj,
                                                                               uniqueKey=uniqueKey, uniteKey=uniteKey)
                                            consoleOpt_obj.save()
                                            deployDetails[k].buildStatus = False
                                            deployDetails[k].save()
                                            failedProjects.append(project_obj.name)
                                            break
                                        else:
                                            res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 发布完成！" % (
                                                task_obj.name, project_obj.name, relVersion,
                                                project_servers[k].server.name)
                                            logger.info(res)
                                            buildMessages.append(res)
                                            buildMessages.append(uniqueKey)
                                            request.websocket.send(json.dumps(buildMessages))
                                            consoleOpt_obj = models.consoleOpt(type=1, plan=task_obj.plan,
                                                                               project=project_obj, content=consoleOpt,
                                                                               packageId=relVersion, buildStatus=True,
                                                                               deployUser=member_obj,
                                                                               uniqueKey=uniqueKey, uniteKey=uniteKey)
                                            consoleOpt_obj.save()
                                            project_plans_news[j].proBuildStatus = True
                                            project_plans_news[j].save()
                                            deployDetails[k].buildStatus = True
                                            deployDetails[k].save()
                                    else:
                                        logger.info("项目：%s，没有发布版本号，请先在预发创建，或者没有发布服务器，请核实！" % project_obj.name)
                                        res = "项目：%s，没有发布版本号，请先在预发创建，或者没有发布服务器，请核实！" % project_obj.name
                                        buildMessages.append(res)
                                        buildMessages.append('no_reversion')
                                        request.websocket.send(json.dumps(buildMessages))
                                        request.websocket.close()
                                        failedProjects.append(project_obj.name)
                                        break
                                else:
                                    task_obj.onBuilding = False
                                    task_obj.save()
                                    break
                        else:
                            task_obj.onBuilding = False
                            task_obj.save()
                            break
                    taskBuildHistory_obj = models.taskBuildHistory(task=task_obj, uniteKey=uniteKey,
                                                                   deployUser=member_obj)
                    taskBuildHistory_obj.save()
                    task_obj.onBuilding = False
                    task_obj.save()
                    fail_project_plans = models.project_plan.objects.filter(plan=task_obj.plan, proBuildStatus=False)
                    if len(fail_project_plans) == 0:
                        sequence_obj.implemented = True
                        sequence_obj.executeCursor = False
                        sequence_obj.executor = member_obj
                        sequence_obj.executeDate = datetime.datetime.now()
                        sequence_obj.remarks = "已部署"
                        sequence_obj.save()
                        nextSequence_obj = models.sequence.objects.filter(task=sequence_obj.task,
                                                                          priority__gt=sequence_obj.priority).order_by(
                            'priority')[0]
                        nextSequence_obj.executeCursor = True
                        nextSequence_obj.save()
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
                all_project_plans = models.project_plan.objects.filter(plan=task_obj.plan)
                project_plans = models.project_plan.objects.filter(plan=task_obj.plan).filter(
                    proBuildStatus=False).order_by('order')
                production_members = models.production_member.objects.filter(production=task_obj.plan.production)
                member_obj = models.member.objects.get(user=request.user)
                isMember = False
                for m in range(len(production_members)):
                    if member_obj == production_members[m].member:
                        isMember = True
                buildMessages = []
                if isMember and member_obj.user.has_perm("mysite.can_deploy_project"):
                    order = 0
                    for i in range(len(project_plans)):
                        if project_plans[i].cursor:
                            order = project_plans[i].order
                            break
                    project_plans_news = project_plans.filter(order__gt=order).order_by('order')
                    if project_plans_news:
                        projectBean_obj = projectBean(project_plans_news, gitCmd_obj.param)
                        total = projectBean_obj.countDeploySum(1, order)
                        buildMessages.append(total)
                        request.websocket.send(json.dumps(buildMessages))
                        failedProjects = []
                        task_obj.onBuilding = True
                        task_obj.save()
                        for j in range(len(project_plans_news)):
                            if len(failedProjects) == 0:
                                project_obj = project_plans_news[j].project
                                deployDetails = models.deployDetail.objects.filter(
                                    project_plan=project_plans_news[j]).order_by('buildStatus')
                                jenkinsPro_obj = models.jenkinsPro.objects.get(project=project_obj)
                                param = eval(jenkinsPro_obj.param)
                                relVersion = project_plans_news[j].lastPackageId
                                for k in range(len(deployDetails)):
                                    if len(failedProjects) == 0:
                                        params = {}
                                        params.update(param)
                                        server_obj = deployDetails[k].server
                                        if relVersion and server_obj:
                                            uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                                            params.update(SERVER_IP=server_obj.ip, REL_VERSION=relVersion)
                                            pythonJenkins_obj = pythonJenkins(jenkinsPro_obj.name, params)
                                            buildNumber = pythonJenkins_obj.realConsole()
                                            url = "http://jenkinspro.bestjlb.cn/view/PRO-Server/job/" + jenkinsPro_obj.name + "/" + str(
                                                buildNumber) + "/console"
                                            buildMessages.append('url')
                                            buildMessages.append(url)
                                            request.websocket.send(json.dumps(buildMessages))
                                            info = pythonJenkins_obj.deploy()
                                            for n in range(len(all_project_plans)):
                                                if all_project_plans[n].cursor:
                                                    all_project_plans[n].cursor = False
                                                    all_project_plans[n].save()
                                            project_plans_news[j].cursor = True
                                            project_plans_news[j].save()
                                            consoleOpt = info['consoleOpt']
                                            isSuccess = consoleOpt.find("Finished: SUCCESS")
                                            if isSuccess == -1:
                                                project_plans_news[j].proBuildStatus = False
                                                project_plans_news[j].save()
                                                deployDetails[k].buildStatus = False
                                                deployDetails[k].save()
                                                res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 发布出错!" % \
                                                      (task_obj.name, project_obj.name, relVersion, server_obj.name)
                                                logger.info(res)
                                                buildMessages.append(res)
                                                buildMessages.append(uniqueKey)
                                                buildMessages.append('deploy_failed')
                                                request.websocket.send(json.dumps(buildMessages))
                                                request.websocket.close()
                                                consoleOpt_obj = models.consoleOpt(type=1, plan=task_obj.plan,
                                                                                   project=project_obj,
                                                                                   content=consoleOpt,
                                                                                   packageId=relVersion,
                                                                                   buildStatus=False,
                                                                                   deployUser=member_obj,
                                                                                   uniqueKey=uniqueKey,
                                                                                   uniteKey=uniteKey)
                                                consoleOpt_obj.save()
                                                failedProjects.append(project_obj.name)
                                                break
                                            else:
                                                res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 发布完成！" % (
                                                    task_obj.name, project_obj.name, relVersion, server_obj.name)
                                                logger.info(res)
                                                buildMessages.append(res)
                                                buildMessages.append(uniqueKey)
                                                request.websocket.send(json.dumps(buildMessages))
                                                consoleOpt_obj = models.consoleOpt(type=1, plan=task_obj.plan,
                                                                                   project=project_obj,
                                                                                   content=consoleOpt,
                                                                                   packageId=relVersion,
                                                                                   buildStatus=True,
                                                                                   deployUser=member_obj,
                                                                                   uniqueKey=uniqueKey,
                                                                                   uniteKey=uniteKey)
                                                consoleOpt_obj.save()
                                                project_plans_news[j].proBuildStatus = True
                                                project_plans_news[j].save()
                                                deployDetails[k].buildStatus = True
                                                deployDetails[k].save()
                                        else:
                                            logger.info("项目：%s，没有发布版本号，请先在预发创建，或者没有发布服务器，请核实！" % project_obj.name)
                                            res = "项目：%s，没有发布版本号，请先在预发创建，或者没有发布服务器，请核实！" % project_obj.name
                                            buildMessages.append(res)
                                            buildMessages.append('no_reversion')
                                            request.websocket.send(json.dumps(buildMessages))
                                            request.websocket.close()
                                            break
                                    else:
                                        break
                            else:
                                task_obj.onBuilding = False
                                task_obj.save()
                                break
                        taskBuildHistory_obj = models.taskBuildHistory(task=task_obj, uniteKey=uniteKey,
                                                                       deployUser=member_obj)
                        taskBuildHistory_obj.save()
                        task_obj.onBuilding = False
                        task_obj.save()
                        for p in range(len(project_plans)):
                            if not project_plans[p].proBuildStatus:
                                failedProjects.append(project_plans[p])
                        if len(failedProjects) == 0:
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
                if isMember and member_obj.user.has_perm("mysite.can_deploy_project"):
                    deployDetails = models.deployDetail.objects.filter(project_plan=project_plan_obj).order_by(
                        'buildStatus')
                    total = len(deployDetails)
                    buildMessages.append(total)
                    request.websocket.send(json.dumps(buildMessages))
                    try:
                        pre_project_plan_obj = \
                            models.project_plan.objects.filter(project=project_obj, proBuildStatus=True,
                                                               lastPackageId__lt=project_plan_obj.lastPackageId).order_by(
                                '-lastPackageId')[0]
                        failedProjects = []
                        task_obj.onBuilding = True
                        task_obj.save()
                        for i in range(len(deployDetails)):
                            if len(failedProjects) == 0:
                                jenkinsPro_obj = models.jenkinsPro.objects.get(project=project_plan_obj.project)
                                param = eval(jenkinsPro_obj.param)
                                params = {}
                                params.update(param)
                                relVersion = pre_project_plan_obj.lastPackageId
                                server_obj = deployDetails[i].server
                                uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                                params.update(SERVER_IP=server_obj.ip, REL_VERSION=relVersion)
                                pythonJenkins_obj = pythonJenkins(jenkinsPro_obj.name, params)
                                buildNumber = pythonJenkins_obj.realConsole()
                                url = "http://jenkinspro.bestjlb.cn/view/PRO-Server/job/" + jenkinsPro_obj.name + "/" + str(
                                    buildNumber) + "/console"
                                buildMessages.append('url')
                                buildMessages.append(url)
                                request.websocket.send(json.dumps(buildMessages))
                                info = pythonJenkins_obj.deploy()
                                consoleOpt = info['consoleOpt']
                                isSuccess = consoleOpt.find("Finished: SUCCESS")
                                if isSuccess == -1:
                                    res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 回滚出错!" % \
                                          (task_obj.name, project_obj.name, relVersion, server_obj.name)
                                    logger.info(res)
                                    buildMessages.append(res)
                                    buildMessages.append(uniqueKey)
                                    buildMessages.append("deploy_failed")
                                    request.websocket.send(json.dumps(buildMessages))
                                    request.websocket.close()
                                    consoleOpt_obj_new = models.consoleOpt(type=1, plan=task_obj.plan,
                                                                           project=project_obj,
                                                                           content=consoleOpt, packageId=relVersion,
                                                                           deployUser=member_obj, uniqueKey=uniqueKey,
                                                                           uniteKey=uniteKey)
                                    consoleOpt_obj_new.save()
                                    failedProjects.append(project_obj.id)
                                    deployDetails[i].buildStatus = False
                                    deployDetails[i].save()
                                else:
                                    res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 回滚完成！" % (
                                        task_obj.name, project_obj.name, relVersion, server_obj.name)
                                    logger.info(res)
                                    buildMessages.append(res)
                                    buildMessages.append(uniqueKey)
                                    request.websocket.send(json.dumps(buildMessages))
                                    consoleOpt_obj_new = models.consoleOpt(type=1, plan=task_obj.plan,
                                                                           project=project_obj,
                                                                           content=consoleOpt, packageId=relVersion,
                                                                           buildStatus=True, deployUser=member_obj,
                                                                           uniqueKey=uniqueKey, uniteKey=uniteKey)
                                    consoleOpt_obj_new.save()
                                    deployDetails[i].buildStatus = True
                                    deployDetails[i].save()
                            else:
                                task_obj.onBuilding = False
                                task_obj.save()
                                break
                        task_obj.onBuilding = False
                        task_obj.save()
                        if len(failedProjects) == 0:
                            taskBuildHistory_obj = models.taskBuildHistory(task=task_obj, category=1, uniteKey=uniteKey,
                                                                           deployUser=member_obj)
                            taskBuildHistory_obj.save()
                            res = "项目：%s，所有节点都已回滚！" % project_obj.name
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
                project_plans = models.project_plan.objects.filter(plan=task_obj.plan,
                                                                   order__lte=project_plan_obj.order)
                buildMessages = []
                production_members = models.production_member.objects.filter(production=task_obj.plan.production)
                member_obj = models.member.objects.get(user=request.user)
                isMember = False
                for m in range(len(production_members)):
                    if member_obj == production_members[m].member:
                        isMember = True
                if isMember and member_obj.user.has_perm("mysite.can_deploy_project"):
                    cursor = failedProjects = []
                    task_obj.onBuilding = True
                    task_obj.save()
                    projectBean_obj = projectBean(project_plans, gitCmd_obj.param)
                    total = projectBean_obj.countDeploySum2(1, project_plan_obj.order)
                    buildMessages.append(total)
                    request.websocket.send(json.dumps(buildMessages))
                    for k in range(len(project_plans)):
                        if len(failedProjects) == 0:
                            project_obj = project_plans[k].project
                            deployDetails = models.deployDetail.objects.filter(project_plan=project_plans[k]).order_by(
                                'buildStatus')
                            try:
                                pre_project_plan_obj = \
                                    models.project_plan.objects.filter(project=project_obj, proBuildStatus=True,
                                                                       lastPackageId__lt=project_plans[
                                                                           k].lastPackageId).order_by('-lastPackageId')[
                                        0]
                                for i in range(len(deployDetails)):
                                    if len(failedProjects) == 0:
                                        project_plans[k].proBuildStatus = False
                                        project_plans[k].save()
                                        jenkinsPro_obj = models.jenkinsPro.objects.get(project=project_plans[k].project)
                                        param = eval(jenkinsPro_obj.param)
                                        params = {}
                                        params.update(param)
                                        relVersion = pre_project_plan_obj.lastPackageId
                                        server_obj = deployDetails[i].server
                                        uniqueKey = ''.join(str(uuid.uuid4()).split('-'))[0:10]
                                        params.update(SERVER_IP=server_obj.ip, REL_VERSION=relVersion)
                                        pythonJenkins_obj = pythonJenkins(jenkinsPro_obj.name, params)
                                        buildNumber = pythonJenkins_obj.realConsole()
                                        url = "http://jenkinspro.bestjlb.cn/view/PRO-Server/job/" + jenkinsPro_obj.name + "/" + str(
                                            buildNumber) + "/console"
                                        buildMessages.append('url')
                                        buildMessages.append(url)
                                        request.websocket.send(json.dumps(buildMessages))
                                        info = pythonJenkins_obj.deploy()
                                        consoleOpt = info['consoleOpt']
                                        isSuccess = consoleOpt.find("Finished: SUCCESS")
                                        if isSuccess == -1:
                                            res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 回滚出错!" % \
                                                  (task_obj.name, project_obj.name, relVersion, server_obj.name)
                                            logger.info(res)
                                            buildMessages.append(res)
                                            buildMessages.append(uniqueKey)
                                            buildMessages.append("deploy_failed")
                                            request.websocket.send(json.dumps(buildMessages))
                                            request.websocket.close()
                                            consoleOpt_obj2 = models.consoleOpt(type=1, plan=task_obj.plan,
                                                                                project=project_obj, content=consoleOpt,
                                                                                packageId=relVersion, buildStatus=False,
                                                                                deployUser=member_obj,
                                                                                uniqueKey=uniqueKey,
                                                                                uniteKey=uniteKey)
                                            consoleOpt_obj2.save()
                                            cursor.append(project_obj.id)
                                            deployDetails[i].buildStatus = False
                                            deployDetails[i].save()
                                            failedProjects.append(project_obj.name)
                                        else:
                                            res = "任务: %s, 项目: %s ,版本号: %s, 服务器: %s, 回滚完成！" % (
                                                task_obj.name, project_obj.name, relVersion, server_obj.name)
                                            logger.info(res)
                                            buildMessages.append(res)
                                            buildMessages.append(uniqueKey)
                                            request.websocket.send(json.dumps(buildMessages))
                                            consoleOpt_obj = models.consoleOpt(type=1, plan=task_obj.plan,
                                                                               project=project_obj,
                                                                               content=consoleOpt,
                                                                               packageId=relVersion, buildStatus=True,
                                                                               deployUser=member_obj,
                                                                               uniqueKey=uniqueKey,
                                                                               uniteKey=uniteKey)
                                            consoleOpt_obj.save()
                                            deployDetails[i].buildStatus = True
                                            deployDetails[i].save()
                                    else:
                                        break

                            except IndexError:
                                logger.info("项目：%s，已是最初版本，无法回滚！" % project_obj.name)
                                res = "项目：%s，已是最初版本，无法回滚！" % project_obj.name
                                buildMessages.append(res)
                                buildMessages.append('no_reversion')
                                request.websocket.send(json.dumps(buildMessages))
                                cursor.append(project_obj.id)
                        else:
                            task_obj.onBuilding = False
                            task_obj.save()
                            break
                    taskBuildHistory_obj = models.taskBuildHistory(task=task_obj, category=1, uniteKey=uniteKey,
                                                                   deployUser=member_obj)
                    taskBuildHistory_obj.save()
                    task_obj.onBuilding = False
                    task_obj.save()
                    if len(failedProjects) == 0:
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
                project_plans = models.project_plan.objects.filter(project=project_obj, exclusiveKey=True)
                exclusivePlan = []
                for k in range(len(project_plans)):
                    exclusivePlan.append(project_plans[k].plan.name)
                if not project_plans or project_plan_obj.exclusiveKey:
                    if project_plan_obj.uatBranch:
                        if not project_plan_obj.uatOnBuilding:
                            project_servers = models.project_server.objects.filter(project=project_obj, server__type=0)
                            jenkinsUat_obj = models.jenkinsUat.objects.get(project=project_obj)
                            project_plan_obj.exclusiveKey = True
                            project_plan_obj.uatOnBuilding = True
                            project_plan_obj.save()
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
                                url = "http://jenkinspro.bestjlb.cn/view/UAT-Server/job/" + jenkinsUat_obj.name + "/" + str(
                                    buildNumber) + "/console"
                                buildMessage.append("deploy")
                                buildMessage.append(url)
                                request.websocket.send(json.dumps(buildMessage))
                                info = pythonJenkins_obj.deploy()
                                if info:
                                    consoleOpt = info['consoleOpt']
                                    isSuccess = consoleOpt.find("Finished: SUCCESS")
                                    if isSuccess != -1:
                                        result = True
                                        project_plan_obj.uatBuildStatus = True
                                        project_plan_obj.lastPackageId = info['buildId']
                                        project_plan_obj.save()
                                        res = "分支%s部署成功" % project_plan_obj.uatBranch
                                        logger.info("分支%s部署成功" % project_plan_obj.uatBranch)
                                        buildMessage.append("success")
                                        buildMessage.append(res)
                                        buildMessage.append(buildNumber)
                                        request.websocket.send(json.dumps(buildMessage))
                                        request.websocket.close()
                                    else:
                                        result = False
                                        res = "分支%s部署失败" % project_plan_obj.uatBranch
                                        logger.error("分支%s部署失败" % project_plan_obj.uatBranch)
                                        project_plan_obj.uatBuildStatus = False
                                        project_plan_obj.save()
                                        buildMessage.append("fail")
                                        buildMessage.append(res)
                                        buildMessage.append(uniqueKey)
                                        request.websocket.send(json.dumps(buildMessage))
                                        request.websocket.close()
                                    consoleOpt_obj = models.consoleOpt(type=0, plan=plan_obj, project=project_obj,
                                                                       content=consoleOpt, packageId=buildNumber,
                                                                       buildStatus=result, deployTime=deployTime,
                                                                       deployUser=member_obj, uniqueKey=uniqueKey,
                                                                       uniteKey=uniteKey)
                                    consoleOpt_obj.save()
                                    project_plan_obj.deployBranch = project_plan_obj.uatBranch
                                    project_plan_obj.save()
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
                            project_plans[i].save()
                            res = "项目%s合并完成" % project_plans[i].project.name
                            buildMessages.append(res)
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
            for m in range(len(production_members)):
                if member_obj == production_members[m].member:
                    isMember = True
            if isMember and member_obj.user.has_perm("mysite.can_deploy_project"):
                if not project_plan_obj.proOnBuilding:
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
                            url = "http://jenkinspro.bestjlb.cn/view/PRO-Server/job/" + jenkinsPro_obj.name + "/" + str(
                                buildNumber) + "/console"
                            buildMessages.append('start_deploy')
                            buildMessages.append(url)
                            request.websocket.send(json.dumps(buildMessages))
                            info = pythonJenkins_obj.deploy()
                            consoleOpt = info['consoleOpt']
                            isSuccess = consoleOpt.find("Finished: SUCCESS")
                            if isSuccess == -1:
                                project_plan_obj.proOnBuilding = False
                                project_plan_obj.proBuildStatus = False
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
                                                                   content=consoleOpt, packageId=relVersion,
                                                                   buildStatus=False, deployUser=member_obj,
                                                                   uniqueKey=uniqueKey, uniteKey=uniteKey)
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
                                                                   project=project_obj, content=consoleOpt,
                                                                   packageId=relVersion, buildStatus=True,
                                                                   deployUser=member_obj,
                                                                   uniqueKey=uniqueKey, uniteKey=uniteKey)
                                consoleOpt_obj.save()
                                deployDetails[i].buildStatus = True
                                deployDetails[i].save()
                        project_plan_obj.proOnBuilding = False
                        project_plan_obj.save()
                        fail_deploys = models.deployDetail.objects.filter(project_plan=project_plan_obj,
                                                                          buildStatus=False)
                        taskBuildHistory_obj = models.taskBuildHistory(task=task_obj, uniteKey=uniteKey,
                                                                       deployUser=member_obj)
                        taskBuildHistory_obj.save()
                        if not fail_deploys:
                            project_plan_obj.proBuildStatus = True
                            project_plan_obj.save()
                            res = "项目：%s，部署完成！" % project_obj.name
                            buildMessages.append('deploy_success')
                            buildMessages.append(res)
                            request.websocket.send(json.dumps(buildMessages))
                            project_plans = models.project_plan.objects.filter(plan=project_plan_obj.plan,
                                                                               proBuildStatus=False)
                            if not project_plans:
                                sequence_obj = models.sequence.objects.filter(task=task_obj).get(segment__isDeploy=True)
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
                    buildMessages.append('on_building')
                    request.websocket.send(json.dumps(buildMessages))
                    request.websocket.close()
            else:
                buildMessages.append('no_role')
                request.websocket.send(json.dumps(buildMessages))
                request.websocket.close()
