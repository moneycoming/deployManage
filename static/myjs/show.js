// 时间格式化
function nowtime(time) {//将当前时间转换成yyyymmdd格式
    var datetime = new Date();
    datetime.setTime(time);
    var year = datetime.getFullYear();
    var month = datetime.getMonth() + 1 < 10 ? "0" + (datetime.getMonth() + 1) : datetime.getMonth() + 1;
    var date = datetime.getDate() < 10 ? "0" + datetime.getDate() : datetime.getDate();
    var hour = datetime.getHours() < 10 ? "0" + datetime.getHours() : datetime.getHours();
    var minute = datetime.getMinutes() < 10 ? "0" + datetime.getMinutes() : datetime.getMinutes();
    var second = datetime.getSeconds() < 10 ? "0" + datetime.getSeconds() : datetime.getSeconds();
    return year + "-" + month + "-" + date + " " + hour + ":" + minute + ":" + second;
}

//获取URL中指定字段信息
function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == variable) {
            return pair[1];
        }
    }
    return (false);
}

// 实时显示预发/生产控制台信息
function getBuildResult(arg) {
    $.ajax({
        url: '/getBuildResult',
        type: 'GET',
        data: arg,

        success: function (data) {
            html = "";
            console.log(data[0]);
            if (data.length > 1) {
                for (var i = 1; i < data.length; i++) {
                    html += "<div class=\"layui-colla-item\">\n" +
                        "                                        <h2 class=\"layui-colla-title\">项目详情</h2>\n" +
                        "                                        <div class=\"layui-colla-content layui-show\">\n" +
                        "                                            <p><pre>" + data[i] + "</pre></p>\n" +
                        "                                        </div>\n" +
                        "                                    </div>"
                }

            }
            else {
                html += "<div class=\"layui-colla-item\">\n" +
                    "                                        <h2 class=\"layui-colla-title\">项目详情</h2>\n" +
                    "                                        <div class=\"layui-colla-content layui-show\">\n" +
                    "                                            <p><pre>项目正在构建中，请等待。。。</pre></p>\n" +
                    "                                        </div>\n" +
                    "                                    </div>"
            }
            if(data[0] === 'uat'){
                $(`.uatBuildResult`).html(html);
            }else {
                $(`.proBuildResult`).html(html);
            }

        },
        error: function () {
            console.log('error');
        }
    })
}

// 任务回滚定时器
function getRollBackResult(task) {
    $.ajax({
        url: '/getBuildResult',
        type: 'GET',
        data: task,

        success: function (data) {
            html = "";
            if (data.length > 0) {
                for (var i = 0; i < data.length; i++) {
                    html += "<div class=\"layui-colla-item\">\n" +
                        "                                        <h2 class=\"layui-colla-title\">项目详情</h2>\n" +
                        "                                        <div class=\"layui-colla-content layui-show\">\n" +
                        "                                            <p><pre>" + data[i] + "</pre></p>\n" +
                        "                                        </div>\n" +
                        "                                    </div>"
                }
            }
            else {
                html += "<div class=\"layui-colla-item\">\n" +
                    "                                        <h2 class=\"layui-colla-title\">项目详情</h2>\n" +
                    "                                        <div class=\"layui-colla-content layui-show\">\n" +
                    "                                            <p><pre>项目正在构建中，请等待。。。</pre></p>\n" +
                    "                                        </div>\n" +
                    "                                    </div>"
            }
            $(`.RollBackResult`).html(html);
        },
        error: function () {
            console.log('error');
        }
    })
}

//任务执行
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    var timer;
    $("body").on("click", ".runTask", runBuild);

    function runBuild() {
        var myDate = nowtime(new Date().getTime());
        var type = $(this).data('type');
        var task = {};
        var id = getQueryVariable("tid");
        task['id'] = id;
        task['time'] = myDate;
        if (timer) {
            getBuildResult(task);
        } else {
            timer = setInterval(() => {
                getBuildResult(task)
            }, 3000)
        }

        $.ajax({
            url: '/ajax_RunBuild',
            type: 'POST',
            data: task,

            success: function (arg) {
                if (arg === "done") {
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '发布成功'
                        , id: 'layerDemo' + type//防止重复弹出
                        , content: '<div style="padding: 20px 100px;">' + "发布成功！" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else {
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '发布异常'
                        , id: 'layerDemo' + type//防止重复弹出
                        , content: '<div style="padding: 20px 100px;">' + arg + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                }
            },
            error: function () {
                console.log('error');
            }
        })
    }
});
//任务回滚
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    var timer;
    $("body").on("click", ".rollback", function () {
        var myDate = nowtime(new Date().getTime());
        var type = $(this).data('type');
        var task = {};
        var id = getQueryVariable("tid")
        task['id'] = id;
        task['time'] = myDate;
        if (timer) {
            getRollBackResult(task);
        } else {
            timer = setInterval(() => {
                getRollBackResult(task)
            }, 3000)
        }

        $.ajax({
            url: '/ajax_RollBack',
            type: 'POST',
            data: task,

            success: function (arg) {
                if (arg === "done") {
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '回滚成功'
                        , id: 'layerDemo' + type//防止重复弹出
                        , content: '<div style="padding: 20px 100px;">' + "回滚成功！" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else {
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '回滚异常'
                        , id: 'layerDemo' + type//防止重复弹出
                        , content: '<div style="padding: 20px 100px;">' + arg + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                }
            },
            error: function () {
                console.log('error');
            }
        })
    });
});
//预发构建执行
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    var timer;
    $("body").on("click", ".uatBuild", uatBuild);

    function uatBuild() {
        var myDate = nowtime(new Date().getTime());
        var type = $(this).data('type');
        var postData = {};
        var projectId = getQueryVariable("prjId");
        var planId = getQueryVariable("pid");
        postData['prjId'] = projectId;
        postData['pid'] = planId;
        postData['time'] = myDate;
        postData['envSort'] = 'uat';
        if (timer) {
            getBuildResult(postData);
        } else {
            timer = setInterval(() => {
                getBuildResult(postData)
            }, 3000)
        }

        $.ajax({
            url: '/ajax_uatBuild',
            type: 'POST',
            data: postData,

            success: function (arg) {
                if (arg) {
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '发布成功'
                        , id: 'layerDemo' + type//防止重复弹出
                        , content: '<div style="padding: 20px 100px;">' + "部署成功！" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else {
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '发布异常'
                        , id: 'layerDemo' + type//防止重复弹出
                        , content: '<div style="padding: 20px 100px;">' + "部署失败！" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                }
            },
            error: function () {
                console.log('error');
            }
        })
    }
});
//面板
layui.use(['element', 'layer'], function () {
    var element = layui.element;
    var layer = layui.layer;

    //监听折叠
    element.on('collapse(test)', function (data) {
        layer.msg('展开状态：' + data.show);
    });
});
//任务关闭/激活
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery;

    $("body").on("click", ".closeBtn", function () {
        str = $(this).text() === "关闭" ? "激活" : "关闭";
        $(this).text(str);
        var postData = {};
        var taskId = $(this).closest("tr").find("#taskId").text();
        console.log(taskId);
        postData['id'] = taskId;
        if (str === '关闭') {
            postData['onOff'] = 1;
        } else {
            postData['onOff'] = 0;
        }

        $.ajax({
            url: '/ajax_showTask',
            type: 'POST',
            data: postData,

            success: function (arg) {
                if (arg.length > 0) {
                    location.reload(true);
                }
            },
            error: function () {
                console.log("error");
            }
        })
    });
});
//任务执行环节已执行/未执行
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", ".segmentBtn", function () {
        var step = $(this).parent().attr('id');
        str = $(this).text();
        $(this).text(str);
        var postData = {};
        var sequenceId = $(this).attr("id");
        var remark = $(this).parent().children("#remark").val();
        postData['id'] = sequenceId;
        postData['implemented'] = 1;
        postData['remark'] = remark;

        $.ajax({
            url: '/ajax_taskImplement',
            type: 'POST',
            data: postData,

            success: function (data) {
                if (data[0] === 'implemented') {
                    $(`#${step} #p1`).removeClass("fade").html(data[1]);
                    $(`#${step} .segmentBtn`).hide();
                    $(`#${step} #remark`).hide();
                    $(`#${step} #nextBtn`).removeClass("fade").show();
                } else {
                    layer.open({
                        type: 1
                        // , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '执行异常'
                        // , id: 'layerDemo123' + type //防止重复弹出
                        , content: '<div style="padding: 20px 100px;">' + "您没有执行此环节的权限！！！" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                }
            },
            error: function () {
                console.log("error");
            }
        })
    });
});
//定时局部显示控制台信息
// layui.use(['element', 'layer'], function () {
//     var $ = layui.jquery
//         , element = layui.element, layer = layui.layer;
//
//     //触发事件
//     var timer;
//     $("body").on("click", ".showBuildResult", resultTimer);
//
//     function resultTimer() {
//         if (timer) {
//             getBuildResult();
//         } else {
//             console.log('no timer');
//             timer = setInterval(() => {
//                 getBuildResult()
//             }, 3000)
//         }
//     }
//
//     function getBuildResult() {
//         var postData = {};
//         var projectId = getQueryVariable("priId");
//         var planId = getQueryVariable("pid");
//         postData['prjId'] = projectId;
//         postData['pid'] = planId;
//
//         $.ajax({
//             url: '/getBuildResult',
//             type: 'POST',
//             data: postData,
//
//             success: function (data) {
//                 html = "";
//                 if (data) {
//                     html += "<div class=\"layui-colla-item\">\n" +
//                         "                                        <h2 class=\"layui-colla-title\">项目详情</h2>\n" +
//                         "                                        <div class=\"layui-colla-content layui-show\">\n" +
//                         "                                            <p><pre>" + data + "</pre></p>\n" +
//                         "                                        </div>\n" +
//                         "                                    </div>"
//                 }
//                 else {
//                     html += "<div class=\"layui-colla-item\">\n" +
//                         "                                        <h2 class=\"layui-colla-title\">项目详情</h2>\n" +
//                         "                                        <div class=\"layui-colla-content layui-show\">\n" +
//                         "                                            <p><pre>项目正在构建中，请等待。。。</pre></p>\n" +
//                         "                                        </div>\n" +
//                         "                                    </div>"
//                 }
//                 $(`.uatBuildResult`).html(html);
//             },
//             error: function () {
//                 console.log('error');
//             }
//         })
//     }
// });
//执行代码自动合并
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", ".autoCodeMerge", function () {
        var step = $(this).parent().attr('id');
        var postData = {};
        var id = getQueryVariable("tid");
        var remark = $(this).siblings("#remark").val();
        console.log(remark);
        postData['id'] = id;
        postData['checked'] = 1;
        postData['remark'] = remark;


        $.ajax({
            url: '/ajax_autoCodeMerge',
            type: 'POST',
            data: postData,

            success: function (arg) {
                if (arg[0] === "no_role") {
                    layer.open({
                        type: 1
                        , title: '合并结果'
                        , content: '<div style="padding: 20px 100px;">' + arg[1] + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else {
                    layer.open({
                        type: 1
                        , title: '合并结果'
                        , content: '<div style="padding: 20px 100px;">' + arg[0] + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                    $(`#${step} #p1`).removeClass("fade").html(arg[1]);
                    $(`#${step} .autoCodeMerge`).hide();
                    $(`#${step} #remark`).hide();
                    $(`#${step} #nextBtn`).removeClass("fade").show();
                }
            },
            error: function () {
                console.log("error");
            }
        })
    });
});
//创建预发分支
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", ".createUatBranch", function () {
        var postData = {};
        var selected = $("input[name='uatBranchChoose']:checked").val();
        if (selected === "option1") {
            var uatBranch = $(" input[ name='uatBranch' ] ").val();
            postData['uatBranch'] = uatBranch;
            postData['radio'] = 'option1';
        }
        else {
            postData['radio'] = 'option2';
        }
        var planId = getQueryVariable("pid");
        var projectId = getQueryVariable("prjId");
        postData['pid'] = planId;
        postData['prjId'] = projectId;


        $.ajax({
            url: '/ajax_createUatBranch',
            type: 'POST',
            data: postData,

            success: function (arg) {
                layer.open({
                    type: 1
                    , title: '结果'
                    , content: '<div style="padding: 20px 100px;">' + arg[0] + '</div>'
                    , btn: '关闭'
                    , btnAlign: 'c' //按钮居中
                    , area: '500px;'
                    , shade: 0.5 //不显示遮罩
                    , yes: function () {
                        layer.closeAll();
                    }
                });
                $(`#uatBranch`).html(arg[1]);
            },
            error: function () {
                console.log("error");
            }
        })
    });
});

