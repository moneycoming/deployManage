#!/usr/bin/python3
# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User


# 服务器信息表
class ServerInfo(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name="服务器名称")
    serverIp = models.CharField(max_length=15, unique=True, verbose_name="服务器IP")


# jenkins项目表
class jenkins_job(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Jenkins项目名称")
    desc = models.CharField(max_length=50, blank=True, verbose_name="Jenkins项目描述")
    serverIp = models.ManyToManyField(ServerInfo, through='JenkinsJob_ServerInfo')
    healthPort = models.CharField(max_length=5, default="1", verbose_name="监控端口")
    applicationName = models.CharField(max_length=50, unique=True, verbose_name="项目名称")
    createBy = models.ForeignKey(User, on_delete=models.CASCADE)
    createDate = models.DateTimeField(auto_now_add=True, verbose_name="创建日期")


# Jenkins项目和服务器信息关系表
class JenkinsJob_ServerInfo(models.Model):
    jenkinsJob = models.ForeignKey(jenkins_job, on_delete=models.CASCADE)
    serverInfo = models.ForeignKey(ServerInfo, on_delete=models.CASCADE)


# uat 最新构建号
class uat_jenkins_job(models.Model):
    name = models.CharField(max_length=50, verbose_name="预发Jenkins job")
    jenkins_job = models.ForeignKey(jenkins_job, on_delete=models.CASCADE, verbose_name="生产Jenkins job")
    uat_buildId = models.IntegerField(default=0, verbose_name="预发构建号")


# 发布任务表
class TaskBar(models.Model):
    name = models.CharField(max_length=200, verbose_name="任务名称")
    jenkinsJob = models.ManyToManyField(jenkins_job, through='TaskDetail')
    createDate = models.DateTimeField(auto_now_add=True, verbose_name="创建日期")
    createUser = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者")
    onOff = models.IntegerField(verbose_name="关闭/重启")


# 任务详情，用于任务回滚等
class TaskDetail(models.Model):
    jenkinsJob = models.ForeignKey(jenkins_job, on_delete=models.CASCADE)
    taskBar = models.ForeignKey(TaskBar, on_delete=models.CASCADE)
    buildID = models.IntegerField(default=0, verbose_name="构建号")
    createDate = models.DateTimeField(auto_now=True, verbose_name="最新构建日期")
    createUser = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="构建人")
    priority = models.IntegerField(verbose_name="项目执行顺序")


# 操作历史表，用于记录操作历史和控制台信息
class OperationHistory(models.Model):
    taskDetail = models.ForeignKey(TaskDetail, on_delete=models.CASCADE)
    console_opt = models.CharField(max_length=10000, verbose_name="控制台信息")
    operateTime = models.DateTimeField(auto_now=True, verbose_name="操作时间")
    type = models.IntegerField(verbose_name="执行：1， 回滚;2")
    server = models.ForeignKey(ServerInfo, on_delete=models.CASCADE)
    operateUser = models.ForeignKey(User, on_delete=models.CASCADE)
    suuid = models.CharField(max_length=40, verbose_name="发布历史唯一标记号")


class TaskHistory(models.Model):
    taskBar = models.ForeignKey(TaskBar, on_delete=models.CASCADE)
    operateUser = models.ForeignKey(User, on_delete=models.CASCADE)
    operateTime = models.DateTimeField(auto_now=True, verbose_name="操作时间")
    type = models.IntegerField(verbose_name="执行：1， 回滚：2")
    suuid = models.CharField(max_length=40, verbose_name="发布历史唯一标记号")
