#!/usr/bin/python3
# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser


# 服务器信息表
class ServerInfo(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name="服务器名称")
    serverIp = models.CharField(max_length=15, unique=True, verbose_name="服务器IP")

    class Meta:
        verbose_name = u'服务器信息'
        verbose_name_plural = verbose_name


# 项目表
class project(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="项目名称")
    desc = models.CharField(max_length=50, blank=True, verbose_name="项目描述")
    applicationName = models.CharField(max_length=50, unique=True, verbose_name="项目名称")
    # branchList = models.TextField(verbose_name="所有分支")
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


# 分支表
class branch(models.Model):
    name = models.CharField(max_length=100, verbose_name="分支名称")
    project = models.ForeignKey(project, on_delete=models.CASCADE, verbose_name="所属项目")


# pro Jenkins job
class pro_jenkinsJob(models.Model):
    name = models.CharField(max_length=50, verbose_name="生产Jenkins Job")
    serverIp = models.ManyToManyField(ServerInfo, through='proJenkins_ServerInfo')
    project = models.ForeignKey(project, on_delete=models.CASCADE, verbose_name="所属项目")
    param = models.CharField(max_length=200, blank=False, verbose_name="构建参数")


# uat Jenkins job
class uat_jenkinsJob(models.Model):
    name = models.CharField(max_length=50, verbose_name="预发Jenkins job")
    project = models.ForeignKey(project, on_delete=models.CASCADE, verbose_name="所属项目")
    buildId = models.IntegerField(default=0, verbose_name="预发构建号")

    def project_name(self):
        return self.project.name

    project_name.short_description = "项目"

    class Meta:
        verbose_name = u'预发构建号'
        verbose_name_plural = verbose_name


# 项目和服务器信息关系表
class proJenkins_ServerInfo(models.Model):
    proJenkins = models.ForeignKey(pro_jenkinsJob, on_delete=models.CASCADE)
    serverInfo = models.ForeignKey(ServerInfo, on_delete=models.CASCADE)

    def proJenkins_name(self):
        return self.proJenkins.name

    proJenkins_name.short_description = "项目"

    def serverInfo_name(self):
        return self.serverInfo.name

    serverInfo_name.short_description = "关联服务器"

    class Meta:
        verbose_name = u'项目和服务器信息关系表'
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
class deployPlan(models.Model):
    title = models.CharField(max_length=200, verbose_name="标题")
    kind = models.ForeignKey(kind, verbose_name="发布类型")
    description = models.TextField(verbose_name="说明")
    production = models.ForeignKey(production, on_delete=models.CASCADE, verbose_name="所属产品")
    createUser = models.ForeignKey(User, verbose_name="创建者")
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


# 任务执行环节
class segment(models.Model):
    name = models.CharField(max_length=20, verbose_name="任务执行环节")
    description = models.CharField(max_length=200, verbose_name="描述")
    isDeploy = models.BooleanField(default=False, verbose_name="是否为项目部署环节")


# Jenkins发布任务表
class task(models.Model):
    name = models.CharField(max_length=200, verbose_name="任务名称")
    proJenkins = models.ManyToManyField(pro_jenkinsJob, through='taskDetail')
    segment = models.ManyToManyField(segment, through='sequence')
    plan = models.ForeignKey(deployPlan, on_delete=models.CASCADE, verbose_name="所属计划")
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
    proJenkins = models.ForeignKey(pro_jenkinsJob, on_delete=models.CASCADE)
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


# 操作历史表，用于记录操作历史和控制台信息
class operationHistory(models.Model):
    taskDetail = models.ForeignKey(taskDetail, on_delete=models.CASCADE)
    console_opt = models.CharField(max_length=10000, verbose_name="控制台信息")
    operateTime = models.DateTimeField(auto_now=True, verbose_name="操作时间")
    type = models.IntegerField(verbose_name="执行：1， 回滚;2")
    server = models.ForeignKey(ServerInfo, on_delete=models.CASCADE)
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
