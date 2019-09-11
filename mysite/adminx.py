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
    list_display = ['name', 'planCounts', 'createDate', 'createUser', 'member']
    search_fields = ['name', 'planCounts', 'createDate', 'createUser']
    list_filter = ['name', 'planCounts', 'createDate', 'createUser']


class production_member_admin(object):
    list_display = ['production', 'member']
    search_fields = ['production', 'member']
    list_filter = ['production', 'member']


class server_admin(object):
    list_display = ['name', 'ip', 'type']
    search_fields = ['name', 'ip', 'type']
    list_filter = ['name', 'ip', 'type']


class member_admin(object):
    list_display = ['name']
    search_fields = ['name']
    list_filter = ['name']


class project_admin(object):
    list_display = ['name', 'desc', 'applicationName', 'project_dir', 'createBy', 'createDate']
    search_fields = ['name', 'createBy']
    list_filter = ['name', 'createBy']


class kind_admin(object):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']
    list_filter = ['name', 'description']


class plan_admin(object):
    list_display = ['name', 'kind', 'project', 'description', 'production', 'createUser', 'createDate']
    search_fields = ['name', 'kind', 'project', 'description', 'production', 'createUser', 'createDate']
    list_filter = ['name', 'kind', 'project', 'description', 'production', 'createUser', 'createDate']


class devBranch_admin(object):
    list_display = ['name', 'project']
    search_fields = ['name', 'project']
    list_filter = ['name', 'project']


class jenkinsPro_admin(object):
    list_display = ['name', 'project', 'param']
    search_fields = ['name', 'project', 'param']
    list_filter = ['name', 'project', 'param']


class jenkinsUat_admin(object):
    list_display = ['name', 'project', 'param']
    search_fields = ['name', 'project', 'param']
    list_filter = ['name', 'project', 'param']


class consoleOpt_admin(object):
    list_display = ['project', 'plan', 'type', 'content', 'packageId', 'result', 'deployTime', 'deployUser',
                    'uniqueKey', 'uniteKey']
    search_fields = ['project', 'plan', 'type', 'content', 'packageId', 'result', 'deployTime', 'deployUser']
    list_filter = ['project', 'plan', 'type', 'content', 'packageId', 'result', 'deployTime', 'deployUser']


class project_server_admin(object):
    list_display = ['project', 'server']
    search_fields = ['project', 'server']
    list_filter = ['project', 'server']


class project_plan_admin(object):
    list_display = ['plan', 'project', 'devBranch', 'uatBranch', 'lastPackageId', 'order', 'cursor', 'buildStatus']
    search_fields = ['plan', 'project', 'devBranch', 'uatBranch', 'lastPackageId', 'order', 'cursor', 'buildStatus']
    list_filter = ['plan', 'project', 'devBranch', 'uatBranch', 'lastPackageId', 'order', 'cursor', 'buildStatus']


class segment_admin(object):
    list_display = ['name', 'description', 'isDeploy']
    search_fields = ['name', 'description']
    list_filter = ['name', 'description']


class task_admin(object):
    list_display = ['name', 'segment', 'plan', 'createDate', 'createUser', 'checkUser', 'checkDate', 'onOff', 'checked',
                    'remark']
    search_fields = ['name', 'segment', 'plan', 'createDate', 'createUser', 'checkUser', 'checkDate', 'onOff',
                     'checked', 'remark']
    list_filter = ['name', 'segment', 'plan', 'createDate', 'createUser', 'checkUser', 'checkDate', 'onOff', 'checked',
                   'remark']


class sequence_admin(object):
    list_display = ['task', 'segment', 'pre_segment', 'next_segment', 'executeDate', 'executor', 'priority',
                    'implemented', 'remarks']
    search_fields = ['task', 'segment', 'pre_segment', 'next_segment', 'executeDate', 'executor', 'priority',
                     'implemented', 'remarks']
    list_filter = ['task', 'segment', 'pre_segment', 'next_segment', 'executeDate', 'executor', 'priority',
                   'implemented', 'remarks']


xadmin.site.register(production, production_admin)
xadmin.site.register(production_member, production_member_admin)
xadmin.site.register(server, server_admin)
xadmin.site.register(member, member_admin)
xadmin.site.register(project, project_admin)
xadmin.site.register(kind, kind_admin)
xadmin.site.register(plan, plan_admin)
xadmin.site.register(devBranch, devBranch_admin)
xadmin.site.register(jenkinsPro, jenkinsPro_admin)
xadmin.site.register(jenkinsUat, jenkinsUat_admin)
xadmin.site.register(consoleOpt, consoleOpt_admin)
xadmin.site.register(project_server, project_server_admin)
xadmin.site.register(project_plan, project_plan_admin)
xadmin.site.register(segment, segment_admin)
xadmin.site.register(task, task_admin)
xadmin.site.register(sequence, sequence_admin)
