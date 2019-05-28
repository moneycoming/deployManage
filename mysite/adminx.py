# -*- coding:utf-8 -*-
import xadmin
from .models import *
from xadmin import views


# 设置主题效果
class BaseSetting(object):
    enable_themes = True
    use_bootswatch = True


xadmin.site.register(views.BaseAdminView, BaseSetting)


# 头部系统名称和底部版权及导航折叠设置
class GlobalSettings(object):
    site_title = '接力棒内部管理系统'
    site_footer = '接力棒内部管理系统,接力棒内部管理系统版权所有'
    menu_style = 'accordion'  # 设置数据库管理导航折叠


xadmin.site.register(views.CommAdminView, GlobalSettings)


class ServerInfo_Admin(object):
    list_display = ['name', 'serverIp']
    search_fields = ['name', 'serverIp']
    list_filter = ['name', 'serverIp']


class uat_jenkins_job_Admin(object):
    list_display = ['name', 'jenkinsJob_name', 'uat_buildId']
    search_fields = ['name', 'jenkins_job', 'uat_buildId']
    list_filter = ['name', 'jenkins_job', 'uat_buildId']


class jenkins_job_Admin(object):
    list_display = ['name', 'desc', 'healthPort', 'applicationName', 'user_name', 'createDate']
    search_fields = ['name', 'desc', 'healthPort', 'applicationName', 'createBy', 'createDate']
    list_filter = ['name', 'desc', 'healthPort', 'applicationName', 'createBy', 'createDate']


class TaskBar_Admin(object):
    list_display = ['name', 'createDate', 'user_name', 'onOff']
    search_fields = ['name', 'createDate', 'createUser', 'onOff']
    list_filter = ['name', 'createDate', 'createUser', 'onOff']


class TaskDetail_Admin(object):
    list_display = ['jenkinsJob_name', 'buildID', 'createDate', 'user_name', 'priority']
    search_fields = ['buildID', 'createDate', 'createUser', 'priority']
    list_filter = ['buildID', 'createDate', 'createUser', 'priority']


class OperationHistory_Admin(object):
    list_display = ['console_opt', 'operateTime', 'server_name', 'type', 'user_name', 'suuid']
    search_fields = ['console_opt', 'operateTime', 'type', 'operateUser', 'suuid']
    list_filter = ['console_opt', 'operateTime', 'type', 'operateUser', 'suuid']


class TaskHistory_Admin(object):
    list_display = ['taskBar_name', 'user_name', 'operateTime', 'type', 'suuid']
    search_fields = ['operateTime', 'type', 'suuid']
    list_filter = ['operateTime', 'type', 'suuid']


class JenkinsJob_ServerInfo_Admin(object):
    list_display = ['jenkinsJob_name', 'serverInfo_name']


xadmin.site.register(uat_jenkins_job, uat_jenkins_job_Admin)
xadmin.site.register(ServerInfo, ServerInfo_Admin)
xadmin.site.register(jenkins_job, jenkins_job_Admin)
xadmin.site.register(TaskBar, TaskBar_Admin)
xadmin.site.register(TaskDetail, TaskDetail_Admin)
xadmin.site.register(OperationHistory, OperationHistory_Admin)
xadmin.site.register(TaskHistory, TaskHistory_Admin)
xadmin.site.register(JenkinsJob_ServerInfo, JenkinsJob_ServerInfo_Admin)
