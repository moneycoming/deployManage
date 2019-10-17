import json
from django.http import JsonResponse
from zentao.function import __get_productBugPercent_response_json_dict
from zentao.function import __get_productTaskPercent_response_json_dict
from zentao.function import __get_productTaskStatusPercent_response_json_dict
from zentao.function import __get_productScorePercent_response_json_dict
from zentao.function import __get_productTaskWorkingHour_dic
from django.db import connections


# 根据项目id查询bug状态分布占比分布和等级分布
def get_productBugPercent(request):
    productId = request.GET['productId']
    cursor = connections['zentao'].cursor()
    query = "select `status`,count(*) as Count from `zt_bug` where product = %s and deleted = '0' group by `status`"
    cursor.execute(query, productId)
    allData = cursor.fetchall()
    active = resolved = closed = 0
    for j in range(len(allData)):
        if allData[j][0] == 'active':
            active = list(allData[j])[1]
        elif allData[j][0] == 'resolved':
            resolved = list(allData[j])[1]
        elif allData[j][0] == 'closed':
            closed = list(allData[j])[1]

    cursor2 = connections['zentao'].cursor()
    query2 = "select 'bugCount',count(*) as Count from `zt_bug` where product = %s and deleted = '0'"
    cursor2.execute(query2, productId)
    allData2 = cursor2.fetchall()
    count = 0
    if len(allData2) > 0:
        count = list(allData2[0])[1]

    cursor3 = connections['zentao'].cursor()
    query3 = "select `pri`,count(*) as Count from `zt_bug` where product = %s and deleted = '0' group by `pri`"
    cursor3.execute(query3, productId)
    allData3 = cursor3.fetchall()
    p1 = p2 = p3 = p4 = 0
    for i in range(len(allData3)):
        if allData3[i][0] == 1:
            p1 = allData3[i][1]
        elif allData3[i][0] == 2:
            p2 = allData3[i][1]
        elif allData3[i][0] == 3:
            p3 = allData3[i][1]
        elif allData3[i][0] == 4:
            p4 = allData3[i][1]

    bugStatus = {
        "count": count,
        "active": active,
        "resolved": resolved,
        "closed": closed
    }
    bugLevel = {
        "p1": p1,
        "p2": p2,
        "p3": p3,
        "p4": p4
    }

    if productId:
        result = "true"
        message = ""
    else:
        result = "false"
        message = "服务器开小差了"

    return JsonResponse(__get_productBugPercent_response_json_dict(result, productId, bugStatus, bugLevel, message))


# 根据项目id查询关联所有迭代已完成任务和目标任务数量
def get_productTaskPercent(request):
    productId = request.GET['productId']
    cursor = connections['zentao'].cursor()
    query = "select 'taskCount',count(*) as Count from `zt_task` where project in (select project from `zt_projectproduct` where product = %s) and deleted = '0'"
    cursor.execute(query, productId)
    allData = cursor.fetchall()
    count = list(allData[0])[1]

    cursor2 = connections['zentao'].cursor()
    query2 = "select 'ActualQuantity',count(*) as Count from `zt_task` where project in (select project from `zt_projectproduct` where product = %s) and deleted = '0' and `status` in ('done','closed')"
    cursor2.execute(query2, productId)
    allData2 = cursor2.fetchall()
    actualQuantity = list(allData2[0])[1]

    cursor3 = connections['zentao'].cursor()
    query3 = "select 'TargetQuantity',count(*) as Count from `zt_task` where project in (select project from `zt_projectproduct` where product = %s) and deleted = '0' and deadline<DATE_FORMAT(NOW(),'%%Y-%%m-%%d') and `status` != 'cancel'"
    cursor3.execute(query3, productId)
    allData3 = cursor3.fetchall()
    targetQuantity = list(allData3[0])[1]

    if productId:
        result = "true"
        message = ""
    else:
        result = "false"
        message = "服务器开小差了"

    return JsonResponse(
        __get_productTaskPercent_response_json_dict(result, productId, count, actualQuantity, targetQuantity, message))


# 根据项目id查询关联所有迭代任务分布状态比例
def get_productTaskStatusPercent(request):
    productId = request.GET['productId']
    cursor = connections['zentao'].cursor()
    query = "select 'taskCount',count(*) as Count from `zt_task` where project in (select project from `zt_projectproduct` where product = %s) and deleted = '0'"
    cursor.execute(query, productId)
    allData = cursor.fetchall()
    count = 0
    if len(allData):
        count = list(allData[0])[1]

    cursor2 = connections['zentao'].cursor()
    query2 = "select `status`,count(*) as Count from `zt_task` where project in (select project from `zt_projectproduct` where product = %s) and deleted = '0' group by `status`"
    cursor2.execute(query2, productId)
    allData2 = cursor2.fetchall()
    wait = done = doing = pause = cancel = closed = 0
    for i in range(len(allData2)):
        if allData2[i][0] == 'wait':
            wait = allData2[i][1]
        elif allData2[i][0] == 'done':
            done = allData2[i][1]
        elif allData2[i][0] == 'doing':
            doing = allData2[i][1]
        elif allData2[i][0] == 'pause':
            pause = allData2[i][1]
        elif allData2[i][0] == 'cancel':
            cancel = allData2[i][1]
        elif allData2[i][0] == 'closed':
            closed = allData2[i][1]

    if productId:
        result = "true"
        message = ""
    else:
        result = "false"
        message = "服务器开小差了"

    return JsonResponse(
        __get_productTaskStatusPercent_response_json_dict(result, productId, count, wait, doing, done, pause, cancel,
                                                          closed, message))


# 根据项目id查看故障分（固定项目）
def get_productScorePercent(request):
    productId = request.GET['productId']
    nowScore = allScore = 0
    cursor = connections['zentao'].cursor()
    query = "select product,sum(keywords) as nowScore from `zt_bug` where deleted = '0' and type = 'bugonline' and product = %s"
    cursor.execute(query, productId)
    allData = cursor.fetchall()
    if allData[0][1]:
        nowScore = allData[0][1]

    cursor2 = connections['zentao'].cursor()
    query2 = "select productID,onlineScore as 'allScore' from `zt_productScore` where productID = %s"
    cursor2.execute(query2, productId)
    allData2 = cursor2.fetchall()
    if (len(allData2)) > 0:
        allScore = allData2[0][1]

    if productId:
        result = "true"
        message = ""
    else:
        result = "false"
        message = "服务器开小差了"

    return JsonResponse(
        __get_productScorePercent_response_json_dict(result, productId, int(nowScore), allScore, message))


# 根据项目id查询项目任务工时消耗
def get_productTaskWorkingHour(request):
    productId = request.GET['productId']
    cursor = connections['zentao'].cursor()
    query = "select 'total',sum(estimate) as expHour, sum(consumed) as workingHour from zt_task where project in (select project from `zt_projectproduct` where product = %s) and deleted = '0' and status = 'done'"
    cursor.execute(query, productId)
    allData = cursor.fetchall()
    totalExpHour = totalWorkingHour = 0
    if allData[0][1]:
        totalExpHour = int(allData[0][1])
    if allData[0][2]:
        totalWorkingHour = int(allData[0][2])

    cursor2 = connections['zentao'].cursor()
    query2 = "select (select realname from zt_user where account = finishedby) as username,sum(estimate) as expHour, sum(consumed) as workingHour,round(sum(consumed)/sum(estimate),2) as rate from zt_task where project in (select project from `zt_projectproduct` where product = %s) and deleted = '0' and status = 'done' group by username order by rate desc"
    cursor2.execute(query2, productId)
    allData2 = cursor2.fetchall()
    memberList = []
    for i in range(len(allData2)):
        name = allData2[i][0]
        expHour = int(allData2[i][1])
        workingHour = int(allData2[i][2])
        rate = allData2[i][3]
        perDetail = {
            'name': name,
            'expHour': expHour,
            'workingHour': workingHour,
            'rate': rate
        }
        memberList.append(perDetail)

    total = {
        'expHour': totalExpHour,
        'workingHour': totalWorkingHour
    }

    if productId:
        result = "true"
        message = ""
    else:
        result = "false"
        message = "服务器开小差了"

    return JsonResponse(__get_productTaskWorkingHour_dic(result, productId, total, memberList, message))
