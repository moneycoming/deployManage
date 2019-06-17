#!/usr/bin/python3
# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User


# 服务器信息表
class ServerInfo(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name="服务器名称")
    serverIp = models.CharField(max_length=15, unique=True, verbose_name="服务器IP")

    class Meta:
        verbose_name = u'服务器信息'
        verbose_name_plural = verbose_name


# jenkins项目表
class jenkins_job(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Jenkins项目名称")
    desc = models.CharField(max_length=50, blank=True, verbose_name="Jenkins项目描述")
    serverIp = models.ManyToManyField(ServerInfo, through='JenkinsJob_ServerInfo')
    param = models.CharField(max_length=200, blank=False, verbose_name="构建参数")
    applicationName = models.CharField(max_length=50, unique=True, verbose_name="项目名称")
    createBy = models.ForeignKey(User, on_delete=models.CASCADE)
    createDate = models.DateTimeField(auto_now_add=True, verbose_name="创建日期")

    def user_name(self):
        name = self.createBy.last_name + self.createBy.first_name
        return name

    user_name.short_description = "创建者"

    class Meta:
        verbose_name = u'Jenkins任务'
        verbose_name_plural = verbose_name


# Jenkins项目和服务器信息关系表
class JenkinsJob_ServerInfo(models.Model):
    jenkinsJob = models.ForeignKey(jenkins_job, on_delete=models.CASCADE)
    serverInfo = models.ForeignKey(ServerInfo, on_delete=models.CASCADE)

    def jenkinsJob_name(self):
        return self.jenkinsJob.name

    jenkinsJob_name.short_description = "Jenkins项目"

    def serverInfo_name(self):
        return self.serverInfo.name

    serverInfo_name.short_description = "关联服务器"

    class Meta:
        verbose_name = u'Jenkins项目和服务器信息关系表'
        verbose_name_plural = verbose_name


# uat 最新构建号
class uat_jenkins_job(models.Model):
    name = models.CharField(max_length=50, verbose_name="预发Jenkins job")
    jenkins_job = models.ForeignKey(jenkins_job, on_delete=models.CASCADE, verbose_name="生产Jenkins job")
    uat_buildId = models.IntegerField(default=0, verbose_name="预发构建号")

    def jenkinsJob_name(self):
        return self.jenkins_job.name

    jenkinsJob_name.short_description = "Jenkins项目"

    class Meta:
        verbose_name = u'预发构建号'
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


# 发布任务表
class TaskBar(models.Model):
    name = models.CharField(max_length=200, verbose_name="任务名称")
    jenkinsJob = models.ManyToManyField(jenkins_job, through='TaskDetail')
    plan = models.ForeignKey(deployPlan, on_delete=models.CASCADE, verbose_name="所属计划")
    createDate = models.DateTimeField(auto_now_add=True, verbose_name="创建日期")
    createUser = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者")
    onOff = models.IntegerField(verbose_name="关闭/重启")

    def user_name(self):
        name = self.createUser.last_name + self.createUser.first_name
        return name

    user_name.short_description = "创建者"

    class Meta:
        verbose_name = u'任务信息'
        verbose_name_plural = verbose_name


# 任务详情，用于任务回滚等
class TaskDetail(models.Model):
    jenkinsJob = models.ForeignKey(jenkins_job, on_delete=models.CASCADE)
    taskBar = models.ForeignKey(TaskBar, on_delete=models.CASCADE)
    buildID = models.IntegerField(default=0, verbose_name="构建号")
    createDate = models.DateTimeField(auto_now=True, verbose_name="最新构建日期")
    createUser = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="构建人")
    priority = models.IntegerField(verbose_name="项目执行顺序")

    def jenkinsJob_name(self):
        return self.jenkinsJob.name

    jenkinsJob_name.short_description = "Jenkins项目"

    def user_name(self):
        name = self.createUser.last_name + self.createUser.first_name
        return name

    user_name.short_description = "操作人"

    class Meta:
        verbose_name = u'任务详情'
        verbose_name_plural = verbose_name


# 操作历史表，用于记录操作历史和控制台信息
class OperationHistory(models.Model):
    taskDetail = models.ForeignKey(TaskDetail, on_delete=models.CASCADE)
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


class TaskHistory(models.Model):
    taskBar = models.ForeignKey(TaskBar, on_delete=models.CASCADE)
    operateUser = models.ForeignKey(User, on_delete=models.CASCADE)
    operateTime = models.DateTimeField(auto_now=True, verbose_name="操作时间")
    type = models.IntegerField(verbose_name="执行：1， 回滚：2")
    suuid = models.CharField(max_length=40, verbose_name="发布历史唯一标记号")

    def taskBar_name(self):
        return self.taskBar.name

    taskBar_name.short_description = "任务名称"

    def user_name(self):
        name = self.operateUser.last_name + self.operateUser.first_name
        return name

    user_name.short_description = "操作人"

    class Meta:
        verbose_name = u'任务历史'
        verbose_name_plural = verbose_name
