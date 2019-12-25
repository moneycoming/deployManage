#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""BranchManager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from mysite import views
import xadmin
from django.contrib import admin
# version模块自动注册需要版本控制的 Model
from xadmin.plugins import xversion

xversion.register_models()

xadmin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^xadmin/', include(xadmin.site.urls)),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^zentao/', include('zentao.urls')),
    url(r'^$', views.index, name='index'),
    url(r'^iosKey$', views.fileKeySearch, name='ios'),
    url(r'^showTask$', views.showTask, name='showTask'),
    url(r'^showPlan$', views.showPlan, name='showPlan'),
    url(r'productionKindChart', views.productionKindChart, name='productionKindChart'),
    url(r'^taskDetail', views.taskDetail, name='taskDetail'),
    url(r'^planDetail', views.planDetail, name='planDetail'),
    url(r'^createTask', views.createTask, name='createTask'),
    url(r'^createPlan$', views.createPlan, name='createPlan'),
    url(r'^ajax_addProject$', views.ajax_addProject, name='addProject'),
    url(r'^ajax_deleteProject', views.ajax_deleteProject, name='deleteProject'),
    url(r'^ajax_showTask$', views.ajax_showTask),
    url(r'^ajax_deleteTask$', views.ajax_deleteTask),
    url(r'^ajax_deletePlan$', views.ajax_deletePlan),
    url(r'^ajax_taskImplement', views.ajax_taskImplement),
    url(r'^ajax_load_info', views.ajax_load_info, name='load_info'),
    url(r'^ajax_get_ip', views.ajax_get_ip, name='get_ip'),
    url(r'^ajax_get_project', views.ajax_get_project, name='get_project'),
    url(r'^ajax_checkSuccess', views.ajax_checkSuccess, name='ajax_checkSuccess'),
    url(r'^ajax_createUatBranch', views.ajax_createUatBranch),
    url(r'^ajax_uatCheck', views.ajax_uatCheck),
    url(r'^ajax_stopDeploy', views.ajax_stopDeploy),
    url(r'^ajax_restartUatDeploy', views.ajax_restartUatDeploy),
    url(r'^ajax_releaseExclusiveKey', views.ajax_releaseExclusiveKey),
    url(r'^uat_console_opt/(\w+)', views.uat_console_opt, name='uat_console_opt'),
    url(r'^pro_console_opt/(\w+)', views.pro_console_opt, name='pro_console_opt'),
    url(r'^single_console_opt/(\w+)', views.single_console_opt, name='single_console'),
    url(r'^uatDetail', views.uatDetail),
    url(r'^uatDeploy', views.uatDeploy),
    url(r'^ws_uatDeploy', views.ws_uatDeploy, name='uatDeploy'),
    url(r'^ws_rollback', views.ws_rollback, name='rollback'),
    url(r'^ws_codeMerge', views.ws_codeMerge, name='codeMerge'),
    url(r'^ws_proConsoleOptRefresh', views.ws_proConsoleOptRefresh, name='proConsoleOptRefresh'),
    url(r'^ws_uatConsoleOptRefresh', views.ws_uatConsoleOptRefresh, name='uatConsoleOptRefresh'),
    url(r'^ws_proOneProjectDeploy', views.ws_proOneProjectDeploy, name='proOneProjectDeploy'),
    url(r'^ws_selectNodesDeploy', views.ws_selectNodesDeploy, name='selectNodesDeploy'),
]
