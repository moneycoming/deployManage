from django.contrib import admin
from mysite.models import *


class ServerInfo_Admin(admin.ModelAdmin):
    list_display = ('name', 'serverIp')
    search_fields = ('name', 'serverIp')
    list_filter = ('name', 'serverIp')


class uat_jenkins_job_Admin(admin.ModelAdmin):
    list_display = ('name', 'jenkinsJob_name', 'uat_buildId')
    search_fields = ('name', 'jenkins_job', 'uat_buildId')
    list_filter = ('name', 'jenkins_job', 'uat_buildId')


class jenkins_job_Admin(admin.ModelAdmin):
    list_display = ('name', 'desc', 'param', 'applicationName', 'user_name', 'createDate')
    search_fields = ('name', 'desc', 'param', 'applicationName', 'createBy', 'createDate')
    list_filter = ('name', 'desc', 'param', 'applicationName', 'createBy', 'createDate')


class TaskBar_Admin(admin.ModelAdmin):
    list_display = ('name', 'createDate', 'user_name', 'onOff')
    search_fields = ('name', 'createDate', 'createUser', 'onOff')
    list_filter = ('name', 'createDate', 'createUser', 'onOff')


class TaskDetail_Admin(admin.ModelAdmin):
    list_display = ('jenkinsJob_name', 'buildID', 'createDate', 'user_name', 'priority')
    search_fields = ('buildID', 'createDate', 'createUser', 'priority')
    list_filter = ('buildID', 'createDate', 'createUser', 'priority')


class OperationHistory_Admin(admin.ModelAdmin):
    list_display = ('console_opt', 'operateTime', 'server_name', 'type', 'user_name', 'suuid')
    search_fields = ('console_opt', 'operateTime', 'type', 'operateUser', 'suuid')
    list_filter = ('console_opt', 'operateTime', 'type', 'operateUser', 'suuid')


class TaskHistory_Admin(admin.ModelAdmin):
    list_display = ('taskBar_name', 'user_name', 'operateTime', 'type', 'suuid')
    search_fields = ('operateTime', 'type', 'suuid')
    list_filter = ('operateTime', 'type', 'suuid')


class JenkinsJob_ServerInfo_Admin(admin.ModelAdmin):
    list_display = ('jenkinsJob_name', 'serverInfo_name')


admin.site.register(uat_jenkins_job, uat_jenkins_job_Admin)
admin.site.register(ServerInfo, ServerInfo_Admin)
admin.site.register(jenkins_job, jenkins_job_Admin)
admin.site.register(TaskBar, TaskBar_Admin)
admin.site.register(TaskDetail, TaskDetail_Admin)
admin.site.register(OperationHistory, OperationHistory_Admin)
admin.site.register(TaskHistory, TaskHistory_Admin)
admin.site.register(JenkinsJob_ServerInfo, JenkinsJob_ServerInfo_Admin)

