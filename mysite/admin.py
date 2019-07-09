from django.contrib import admin
from mysite.models import *


class ServerInfo_Admin(admin.ModelAdmin):
    list_display = ('name', 'serverIp')
    search_fields = ('name', 'serverIp')
    list_filter = ('name', 'serverIp')


class pro_jenkins_job_Admin(admin.ModelAdmin):
    list_display = ('name', 'param')
    search_fields = ('name', 'param')
    list_filter = ('name', 'param')


class uat_jenkins_job_Admin(admin.ModelAdmin):
    list_display = ('name', 'buildId')
    search_fields = ('name', 'buildId')
    list_filter = ('name', 'buildId')


class project_job_Admin(admin.ModelAdmin):
    list_display = ('name', 'desc', 'applicationName', 'project_dir', 'createBy', 'createDate')
    search_fields = ('name', 'desc', 'applicationName', 'project_dir', 'createBy', 'createDate')
    list_filter = ('name', 'desc', 'applicationName', 'project_dir', 'createBy', 'createDate')


class TaskBar_Admin(admin.ModelAdmin):
    list_display = ('name', 'createDate', 'user_name', 'onOff')
    search_fields = ('name', 'createDate', 'createUser', 'onOff')
    list_filter = ('name', 'createDate', 'createUser', 'onOff')


class TaskDetail_Admin(admin.ModelAdmin):
    list_display = ('packageId', 'createDate', 'user_name', 'priority')
    search_fields = ('packageId', 'createDate', 'createUser', 'priority')
    list_filter = ('packageId', 'createDate', 'createUser', 'priority')


class OperationHistory_Admin(admin.ModelAdmin):
    list_display = ('console_opt', 'operateTime', 'server_name', 'type', 'user_name', 'suuid')
    search_fields = ('console_opt', 'operateTime', 'type', 'operateUser', 'suuid')
    list_filter = ('console_opt', 'operateTime', 'type', 'operateUser', 'suuid')


class TaskHistory_Admin(admin.ModelAdmin):
    list_display = ('task_name', 'user_name', 'operateTime', 'type', 'suuid')
    search_fields = ('operateTime', 'type', 'suuid')
    list_filter = ('operateTime', 'type', 'suuid')


class JenkinsJob_ServerInfo_Admin(admin.ModelAdmin):
    list_display = ('proJenkins_name', 'serverInfo_name')


admin.site.register(uat_jenkinsJob, uat_jenkins_job_Admin)
admin.site.register(ServerInfo, ServerInfo_Admin)
admin.site.register(project, project_job_Admin)
admin.site.register(pro_jenkinsJob, pro_jenkins_job_Admin)
admin.site.register(task, TaskBar_Admin)
admin.site.register(taskDetail, TaskDetail_Admin)
admin.site.register(operationHistory, OperationHistory_Admin)
admin.site.register(taskHistory, TaskHistory_Admin)
admin.site.register(proJenkins_ServerInfo, JenkinsJob_ServerInfo_Admin)

