#!/usr/bin/python3
# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser


# 服务器信息表
class server(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name="服务器名称")
    ip = models.CharField(max_length=15, unique=True, verbose_name="服务器IP")
    type = models.IntegerField(verbose_name="0:代表预发， 1:代表生产")

    class Meta:
        verbose_name = u'服务器信息'
        verbose_name_plural = verbose_name


# 成员表
class member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="extension")
    name = models.CharField(max_length=50, verbose_name="姓名中文表示")


# 项目表
class project(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="项目名称")
    server = models.ManyToManyField(server, through="project_server")
    desc = models.CharField(max_length=50, blank=True, verbose_name="项目描述")
    applicationName = models.CharField(max_length=50, unique=True, verbose_name="项目名称")
    project_dir = models.CharField(max_length=200, blank=False, verbose_name="代码仓库")
    createBy = models.ForeignKey(User, on_delete=models.CASCADE)
    createDate = models.DateTimeField(auto_now_add=True, verbose_name="创建日期")

    def user_name(self):
        name = self.createBy.last_name + self.createBy.first_name
        return name

    user_name.short_description = "创建者"

    class Meta:
        verbose_name = u'Jenkins任务'
        verbose_name_plural = verbose_name


# 产品分类表
class production(models.Model):
    name = models.CharField(max_length=20, verbose_name="产品名称")
    planCounts = models.IntegerField(verbose_name="任务总数")
    createDate = models.DateTimeField(auto_now_add=True, verbose_name="创建日期")
    createUser = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者")

    def user_name(self):
        name = self.createUser.last_name + self.createUser.first_name
        return name

    user_name.short_description = "创建者"

    class Meta:
        verbose_name = u'产品信息'
        verbose_name_plural = verbose_name


# 发布类型表
class kind(models.Model):
    name = models.CharField(max_length=10, verbose_name="类型名")
    description = models.CharField(max_length=200, verbose_name="描述")


# 发布计划表
class plan(models.Model):
    title = models.CharField(max_length=200, verbose_name="标题")
    kind = models.ForeignKey(kind, verbose_name="发布类型")
    project = models.ManyToManyField(project, through="project_plan")
    description = models.TextField(verbose_name="说明")
    member = models.ManyToManyField(member, related_name="计划成员", through="plan_member")
    production = models.ForeignKey(production, on_delete=models.CASCADE, verbose_name="所属产品")
    createUser = models.ForeignKey(User, related_name="创建者", verbose_name="创建者")
    createDate = models.DateTimeField(auto_now_add=True, verbose_name="创建日期")

    def production_name(self):
        name = self.production.name
        return name

    production_name.short_description = "所属产品"

    def user_name(self):
        name = self.createUser.last_name + self.createUser.first_name
        return name

    user_name.short_description = "创建者"

    class Meta:
        verbose_name = u'发布计划'
        verbose_name_plural = verbose_name


# 分支表
class devBranch(models.Model):
    name = models.CharField(max_length=100, verbose_name="分支名称")
    project = models.ForeignKey(project, on_delete=models.CASCADE, verbose_name="所属项目")


# pro Jenkins job
class jenkinsPro(models.Model):
    name = models.CharField(max_length=50, verbose_name="生产Jenkins Job")
    project = models.ForeignKey(project, on_delete=models.CASCADE, verbose_name="所属项目")
    param = models.CharField(max_length=200, blank=False, verbose_name="构建参数")


# uat Jenkins job
class jenkinsUat(models.Model):
    name = models.CharField(max_length=50, verbose_name="预发Jenkins job")
    project = models.ForeignKey(project, on_delete=models.CASCADE, verbose_name="所属项目")
    param = models.CharField(max_length=200, verbose_name="构建参数")

    def project_name(self):
        return self.project.name

    project_name.short_description = "项目"

    class Meta:
        verbose_name = u'预发构建号'
        verbose_name_plural = verbose_name


# Jenkins控制台信息表
class consoleOpt(models.Model):
    project = models.ForeignKey(project, on_delete=models.CASCADE)
    plan = models.ForeignKey(plan, on_delete=models.CASCADE)
    type = models.IntegerField(verbose_name="0:代表预发， 1:代表生产")
    content = models.TextField(verbose_name="控制台信息")
    packageId = models.IntegerField(verbose_name="生产发布包编号")
    result = models.BooleanField(verbose_name="构建成功，失败")
    deployTime = models.DateTimeField(auto_now_add=True, verbose_name="最新操作日期")
    deployUser = models.ForeignKey(member, verbose_name="执行人")
    signId = models.CharField(max_length=40, verbose_name="发布历史唯一标记号")


# 项目服务器信息关系表
class project_server(models.Model):
    project = models.ForeignKey(project, on_delete=models.CASCADE)
    server = models.ForeignKey(server, on_delete=models.CASCADE)


# 项目发布计划表
class project_plan(models.Model):
    project = models.ForeignKey(project, on_delete=models.CASCADE)
    plan = models.ForeignKey(plan, on_delete=models.CASCADE)
    devBranch = models.ForeignKey(devBranch, on_delete=models.CASCADE, verbose_name="开发分支")
    uatBranch = models.CharField(max_length=50, null=True, verbose_name="预发分支")
    lastPackageId = models.CharField(max_length=3, null=True, verbose_name="最新生产发布包编号")
    order = models.IntegerField(verbose_name="执行顺序")


# 计划成员表
class plan_member(models.Model):
    member = models.ForeignKey(member, on_delete=models.CASCADE, verbose_name="成员")
    plan = models.ForeignKey(plan, on_delete=models.CASCADE, verbose_name="计划")


# 任务执行环节
class segment(models.Model):
    name = models.CharField(max_length=20, verbose_name="任务执行环节")
    description = models.CharField(max_length=200, verbose_name="描述")
    isDeploy = models.BooleanField(default=False, verbose_name="是否为项目部署环节")


# Jenkins发布任务表
class task(models.Model):
    name = models.CharField(max_length=200, verbose_name="任务名称")
    proJenkins = models.ManyToManyField(jenkinsPro, through='taskDetail')
    segment = models.ManyToManyField(segment, through='sequence')
    plan = models.ForeignKey(plan, on_delete=models.CASCADE, verbose_name="所属计划")
    createDate = models.DateTimeField(auto_now_add=True, verbose_name="创建日期")
    createUser = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者", related_name='user_create')
    checkUser = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, verbose_name="验证者", related_name='user_check')
    checkDate = models.DateTimeField(auto_now_add=True, blank=True, verbose_name="验证日期")
    onOff = models.IntegerField(verbose_name="关闭/重启")
    checked = models.BooleanField(default=False, verbose_name="验证通过？是：否")
    remark = models.TextField(blank=True, verbose_name="备注")

    def user_name(self):
        name = self.createUser.last_name + self.createUser.first_name
        return name

    user_name.short_description = "创建者"

    class Meta:
        verbose_name = u'任务信息'
        verbose_name_plural = verbose_name


# 任务执行队列
class sequence(models.Model):
    segment = models.ForeignKey(segment, on_delete=models.CASCADE)
    task = models.ForeignKey(task, on_delete=models.CASCADE)
    pre_segment = models.IntegerField(verbose_name="上个节点序号")
    next_segment = models.IntegerField(verbose_name="下个节点序号")
    executeDate = models.DateTimeField(auto_now_add=True, blank=True, verbose_name="最新操作日期")
    executor = models.ForeignKey(User, blank=True, verbose_name="最新执行者")
    priority = models.IntegerField(verbose_name="任务执行顺序")
    implemented = models.BooleanField(default=False, verbose_name="是否执行")
    remarks = models.CharField(max_length=200, blank=True, verbose_name="备注")


# 任务详情，用于任务回滚等
class taskDetail(models.Model):
    proJenkins = models.ForeignKey(jenkinsPro, on_delete=models.CASCADE)
    task = models.ForeignKey(task, on_delete=models.CASCADE)
    packageId = models.IntegerField(default=0, verbose_name="生产发布包编号")
    branch = models.CharField(max_length=100, verbose_name="分支")
    priority = models.IntegerField(verbose_name="项目执行顺序")

    def proJenkins_name(self):
        return self.proJenkins.name

    proJenkins_name.short_description = "Jenkins项目"

    class Meta:
        verbose_name = u'任务详情'
        verbose_name_plural = verbose_name
        permissions = (
            ('can_deploy_project', '发布项目'),
            ('can_check_project', '线上验证'),
        )


# 操作历史表，用于记录操作历史和控制台信息
class operationHistory(models.Model):
    taskDetail = models.ForeignKey(taskDetail, on_delete=models.CASCADE)
    console_opt = models.CharField(max_length=10000, verbose_name="控制台信息")
    operateTime = models.DateTimeField(auto_now=True, verbose_name="操作时间")
    type = models.IntegerField(verbose_name="执行：1， 回滚;2")
    server = models.ForeignKey(server, on_delete=models.CASCADE)
    operateUser = models.ForeignKey(User, on_delete=models.CASCADE)
    suuid = models.CharField(max_length=40, verbose_name="发布历史唯一标记号")

    def user_name(self):
        name = self.operateUser.last_name + self.operateUser.first_name
        return name

    user_name.short_description = "操作人"

    def server_name(self):
        return self.server.name

    server_name.short_description = "关联服务器"

    class Meta:
        verbose_name = u'操作历史'
        verbose_name_plural = verbose_name


class taskHistory(models.Model):
    task = models.ForeignKey(task, on_delete=models.CASCADE)
    operateUser = models.ForeignKey(User, on_delete=models.CASCADE)
    operateTime = models.DateTimeField(auto_now=True, verbose_name="操作时间")
    type = models.IntegerField(verbose_name="执行：1， 回滚：2")
    suuid = models.CharField(max_length=40, verbose_name="发布历史唯一标记号")

    def task_name(self):
        return self.task.name

    task_name.short_description = "任务名称"

    def user_name(self):
        name = self.operateUser.last_name + self.operateUser.first_name
        return name

    user_name.short_description = "操作人"

    class Meta:
        verbose_name = u'任务历史'
        verbose_name_plural = verbose_name
