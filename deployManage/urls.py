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
# import xadmin

# xadmin.autodiscover()
# version模块自动注册需要版本控制的 Model
# from xadmin.plugins import xversion
#
# xversion.register_models()

urlpatterns = [
    # url(r'^admin/', include(admin.site.urls)),
    # url(r'^xadmin/', include(xadmin.site.urls)),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^$', views.index),
    url(r'^iosKey$', views.fileKeySearch, name='ios'),
    url(r'^showTask$', views.showTask, name='showTask'),
    url(r'^taskDetail', views.taskDetail, name='taskDetail'),
    url(r'^createTask$', views.CreateTask, name='CreateJob'),
    url(r'^ajax_RunBuild$', views.ajax_runBuild, name='runBuild'),
    url(r'^ajax_RollBack$', views.ajax_rollBack, name='rollBack'),
    url(r'^ajax_showTask$', views.ajax_showTask),
    url(r'^console_opt/(\w+)', views.console_opt, name='console'),
    url(r'^ajax_load_buildIds$', views.ajax_load_buildIds, name='load_buildIds'),
]
