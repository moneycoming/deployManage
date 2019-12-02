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
        verbose_name = u'服务器列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# 成员表
class member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="extension")
    name = models.CharField(max_length=50, verbose_name="姓名中文表示")

    class Meta:
        verbose_name = u'人员列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# 项目表
class project(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="项目名称")
    server = models.ManyToManyField(server, through="project_server", verbose_name="服务器")
    desc = models.CharField(max_length=50, blank=True, verbose_name="项目描述")
    applicationName = models.CharField(max_length=50, unique=True, verbose_name="应用名称")
    project_dir = models.CharField(max_length=200, blank=False, verbose_name="代码仓库")
    createBy = models.ForeignKey(member, on_delete=models.CASCADE, verbose_name="由谁创建")
    createDate = models.DateTimeField(auto_now_add=True, verbose_name="创建日期")

    class Meta:
        verbose_name = u'项目列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# 产品分类表
class production(models.Model):
    name = models.CharField(max_length=20, verbose_name="产品名称")
    planCounts = models.IntegerField(null=True, default=0, verbose_name="发布总数")
    createDate = models.DateTimeField(auto_now_add=True, verbose_name="创建日期")
    createUser = models.ForeignKey(member, on_delete=models.CASCADE, related_name="createUser", verbose_name="由谁创建")
    member = models.ManyToManyField(member, through='production_member', related_name="teamMember", verbose_name="团队成员")

    class Meta:
        verbose_name = u'产品列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# 产品人员关系表
class production_member(models.Model):
    member = models.ForeignKey(member, verbose_name="成员")
    production = models.ForeignKey(production, verbose_name="产品")

    class Meta:
        verbose_name = u'团队管理'
        verbose_name_plural = verbose_name


# 发布类型表
class kind(models.Model):
    name = models.CharField(max_length=10, verbose_name="类型名")
    description = models.CharField(max_length=200, verbose_name="描述")

    class Meta:
        verbose_name = u'发布类型列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# 发布计划表
class plan(models.Model):
    name = models.CharField(max_length=200, verbose_name="标题")
    kind = models.ForeignKey(kind, verbose_name="发布类型")
    project = models.ManyToManyField(project, through="project_plan", verbose_name="包含项目")
    description = models.TextField(verbose_name="说明")
    production = models.ForeignKey(production, on_delete=models.CASCADE, verbose_name="所属产品")
    fatherPlanId = models.IntegerField(null=True, verbose_name="关联主计划的id")
    subPlanId = models.IntegerField(null=True, verbose_name="关联子计划的id")
    isSubPlan = models.BooleanField(default=False, verbose_name="是否为子计划")
    createUser = models.ForeignKey(member, verbose_name="由谁创建")
    createDate = models.DateTimeField(auto_now_add=True, verbose_name="创建日期")
    uatCheck = models.BooleanField(default=False, verbose_name="验证通过？")
    uatRemark = models.TextField(null=True, verbose_name="预发验收备注")
    uatCheckMember = models.ForeignKey(member, null=True, related_name="uatCheckMember", verbose_name="预发由谁验收")
    uatCheckDate = models.DateTimeField(auto_now_add=True, null=True, verbose_name="预发验收日期")

    class Meta:
        verbose_name = u'发布计划列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# 开发分支表
class devBranch(models.Model):
    name = models.CharField(max_length=100, verbose_name="分支名称")
    project = models.ForeignKey(project, on_delete=models.CASCADE, verbose_name="所属项目")

    class Meta:
        verbose_name = u'开发分支管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# pro Jenkins job
class jenkinsPro(models.Model):
    name = models.CharField(max_length=50, verbose_name="生产Jenkins Job")
    project = models.ForeignKey(project, on_delete=models.CASCADE, verbose_name="所属项目")
    param = models.CharField(max_length=200, blank=False, verbose_name="构建参数")

    class Meta:
        verbose_name = u'生产Jenkins管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# uat Jenkins job
class jenkinsUat(models.Model):
    name = models.CharField(max_length=50, verbose_name="预发Jenkins job")
    project = models.ForeignKey(project, on_delete=models.CASCADE, verbose_name="所属项目")
    param = models.CharField(max_length=200, verbose_name="构建参数")

    class Meta:
        verbose_name = u'预发Jenkins管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# 任务执行环节
class segment(models.Model):
    name = models.CharField(max_length=20, verbose_name="任务执行环节")
    description = models.CharField(max_length=200, verbose_name="描述")
    order = models.IntegerField(verbose_name="环节自带执行顺序")
    isDeploy = models.BooleanField(default=False, verbose_name="是否为项目部署环节")
    isCheck = models.BooleanField(default=False, verbose_name="是否为验收环节")
    isMerge = models.BooleanField(default=False, verbose_name="是否为分支合并环节")

    class Meta:
        verbose_name = u'任务执行环节列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# Jenkins发布任务表
class task(models.Model):
    name = models.CharField(max_length=200, verbose_name="任务名称")
    segment = models.ManyToManyField(segment, through='sequence', verbose_name="执行环节")
    plan = models.OneToOneField(plan, on_delete=models.CASCADE, verbose_name="所属计划")
    createDate = models.DateTimeField(auto_now_add=True, verbose_name="创建日期")
    createUser = models.ForeignKey(member, on_delete=models.CASCADE, verbose_name="由谁创建", related_name='taskCreateUser')
    onBuilding = models.BooleanField(default=False, verbose_name="是否部署中")
    onOff = models.IntegerField(verbose_name="关闭/重启")

    class Meta:
        verbose_name = u'任务列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# 任务执行队列
class sequence(models.Model):
    segment = models.ForeignKey(segment, on_delete=models.CASCADE, verbose_name="执行环节")
    task = models.ForeignKey(task, on_delete=models.CASCADE, verbose_name="所属任务")
    pre_segment = models.IntegerField(null=True, verbose_name="上个节点序号")
    next_segment = models.IntegerField(null=True, verbose_name="下个节点序号")
    executeDate = models.DateTimeField(auto_now_add=True, null=True, verbose_name="最新操作日期")
    executor = models.ForeignKey(member, null=True, verbose_name="最新执行者")
    priority = models.IntegerField(null=True, verbose_name="执行顺序")
    implemented = models.BooleanField(default=False, verbose_name="是否已执行")
    remarks = models.CharField(max_length=200, null=True, verbose_name="备注")
    executeCursor = models.BooleanField(default=False, verbose_name="执行环节记录点")

    class Meta:
        verbose_name = u'任务队列管理'
        verbose_name_plural = verbose_name


# Jenkins控制台信息表
class consoleOpt(models.Model):
    project = models.ForeignKey(project, on_delete=models.CASCADE, verbose_name="项目")
    plan = models.ForeignKey(plan, on_delete=models.CASCADE, verbose_name="计划")
    type = models.IntegerField(verbose_name="0:代表预发， 1:代表生产")
    content = models.TextField(verbose_name="控制台信息")
    packageId = models.IntegerField(null=True, verbose_name="版本号(生产)/构建号(预发)")
    buildStatus = models.BooleanField(default=False, verbose_name="部署状态")
    uniqueKey = models.CharField(max_length=40, verbose_name="发布历史唯一标记号")
    uniteKey = models.CharField(max_length=40, verbose_name="发布历史统一标记号")
    deployTime = models.DateTimeField(auto_now_add=True, verbose_name="最新操作日期")
    deployUser = models.ForeignKey(member, verbose_name="执行人")

    class Meta:
        verbose_name = u'后台信息管理'
        verbose_name_plural = verbose_name


# jenkins控制台信息按任务分类
class taskBuildHistory(models.Model):
    task = models.ForeignKey(task, on_delete=models.CASCADE, verbose_name="任务名")
    category = models.IntegerField(default=0, verbose_name="0:代表发布， 1：代表回滚")
    uniteKey = models.CharField(max_length=40, verbose_name="发布历史统一标记号")
    deployTime = models.DateTimeField(auto_now_add=True, verbose_name="最新操作日期")
    deployUser = models.ForeignKey(member, verbose_name="执行人")

    class Meta:
        verbose_name = u'生产发布记录'
        verbose_name_plural = verbose_name


# 项目服务器信息关系表
class project_server(models.Model):
    project = models.ForeignKey(project, on_delete=models.CASCADE, verbose_name="项目")
    server = models.ForeignKey(server, on_delete=models.CASCADE, verbose_name="服务器")

    class Meta:
        verbose_name = u'项目和服务器管理'
        verbose_name_plural = verbose_name


# 项目发布计划表
class project_plan(models.Model):
    project = models.ForeignKey(project, on_delete=models.CASCADE, verbose_name="项目")
    plan = models.ForeignKey(plan, on_delete=models.CASCADE, verbose_name="计划")
    devBranch = models.ForeignKey(devBranch, on_delete=models.CASCADE, verbose_name="开发分支")
    uatBranch = models.CharField(max_length=50, null=True, verbose_name="预发分支")
    deployBranch = models.CharField(max_length=50, null=True, verbose_name="预发部署分支")
    lastPackageId = models.IntegerField(null=True, verbose_name="最新生产发布包编号")
    order = models.IntegerField(verbose_name="生产部署顺序")
    cursor = models.BooleanField(default=False, verbose_name="生产部署游标")
    proBuildStatus = models.BooleanField(default=False, verbose_name="生产部署状态")
    uatBuildStatus = models.BooleanField(default=False, verbose_name="预发部署状态")
    uatOnBuilding = models.BooleanField(default=False, verbose_name="预发是否部署中")
    proOnBuilding = models.BooleanField(default=False, verbose_name="生产是否部署中")
    mergeStatus = models.BooleanField(default=False, verbose_name="代码合并状态")
    exclusiveKey = models.BooleanField(default=False, verbose_name="项目预发环境独占锁")

    class Meta:
        verbose_name = u'发布计划和项目管理'
        verbose_name_plural = verbose_name


class deployDetail(models.Model):
    project_plan = models.ForeignKey(project_plan, on_delete=models.CASCADE, verbose_name="计划-项目")
    server = models.ForeignKey(server, on_delete=models.CASCADE, verbose_name="服务器")
    buildStatus = models.BooleanField(default=False, verbose_name="项目当前状态")

    class Meta:
        verbose_name = u'生产环境发布细节'
        verbose_name_plural = verbose_name


# 环境配置表
class paramConfig(models.Model):
    name = models.CharField(max_length=50, verbose_name="参数名")
    param = models.CharField(max_length=200, verbose_name="参数值")

    class Meta:
        verbose_name = u'环境参数表'
        verbose_name_plural = verbose_name
