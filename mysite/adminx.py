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


class production_admin(object):
    list_display = ['name', 'planCounts', 'createDate', 'user_name']
    search_fields = ['name']
    list_filter = ['name']


class production_member_admin(object):
    list_display = ['name', 'member_name']
    search_fields = ['name']
    list_filter = ['name']


xadmin.site.register(production, production_admin)
xadmin.site.register(production_member, production_member_admin)
# xadmin.site.register(project, jenkins_job_Admin)
# xadmin.site.register(task, TaskBar_Admin)
# xadmin.site.register(taskDetail, TaskDetail_Admin)
# xadmin.site.register(operationHistory, OperationHistory_Admin)
# xadmin.site.register(taskHistory, TaskHistory_Admin)
# xadmin.site.register(jenkinsPro_serverInfo, JenkinsJob_ServerInfo_Admin)
# xadmin.site.register(production, production_Admin)
