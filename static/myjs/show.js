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

//生成随机数
function RandomNumBoth(Min, Max) {
    var Range = Max - Min;
    var Rand = Math.random();
    return Min + Math.round(Rand * Range); //四舍五入
    // return num;
}

//创建预发分支
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    $("body").on("click", ".createUatBranch", function () {
        $('.createUatBranch').hide();
        $('#createUatBranchText').html("分支创建中，请等待...");
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

            success: function (data) {
                if (data.role === 1) {
                    if (data.check === 0) {
                        if (data.result === 1) {
                            var html = "<div class=\"sufee-alert alert with-close alert-success alert-dismissible\">\n" +
                                "<span class=\"badge badge-pill badge-primary\">Success</span>\n" +
                                data.res +
                                "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                "aria-label=\"Close\">\n" +
                                "<span aria-hidden=\"true\">&times;</span>\n" +
                                "</button>\n" +
                                "</div>";
                            $('#create-uatBranch-message').html(html);
                            $('#createUatBranchText').html("分支创建完成");
                            $(`#uatBranch`).html(data.uatBranch);
                        } else {
                            var html2 = "<div class=\"sufee-alert alert with-close alert-danger alert-dismissible\">\n" +
                                "<span class=\"badge badge-pill badge-primary\">Failure</span>\n" +
                                data.res +
                                "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                "aria-label=\"Close\">\n" +
                                "<span aria-hidden=\"true\">&times;</span>\n" +
                                "</button>\n" +
                                "</div>";
                            $('#create-uatBranch-message').html(html2);
                            $('#createUatBranchText').html("分支创建失败");
                        }
                    } else {
                        layer.open({
                            type: 1
                            , title: '结果'
                            , content: '<div style="padding: 20px 100px;">' + "预发验收已通过，不能再创建分支！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $('#createUatBranchText').hide();
                    }
                } else {
                    layer.open({
                        type: 1
                        , title: '结果'
                        , content: '<div style="padding: 20px 100px;">' + "你没有创建预发分支的权限！" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                    $('#createUatBranchText').hide();
                }

            },
            error: function () {
                console.log("error");
            }
        })
    });
});
//预发部署
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer, element = layui.element;
    $("body").on("click", "#uatDeploy", uatBuild);

    function uatBuild() {
        var tr_id = $(this).closest("tr").attr("id");
        var myDate = nowtime(new Date().getTime());
        var type = $(this).data('type');
        var projectId = getQueryVariable("prjId");
        var planId = getQueryVariable("pid");
        var combination = projectId + '-' + planId + '-' + myDate;


        if ("WebSocket" in window) {
            console.log("您的浏览器支持 WebSocket!");

            // 打开一个 web socket
            var ws = new WebSocket("ws:" + window.location.host + "/ws_uatDeploy");

            ws.onopen = function () {
                ws.send(combination);
                console.log("数据已发送...");
            };

            ws.onmessage = function (evt) {
                var received_msg = JSON.parse(evt.data);
                var html3 = "";
                console.log("数据已接收...");
                if (received_msg[0] === 'no_role') {
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '发布结果'
                        , id: 'layerDemo' + type//防止重复弹出
                        , content: '<div style="padding: 20px 100px;">' + "你没有部署预发的权限！" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else if (received_msg[0] === 'already_uatCheck') {
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '发布结果'
                        , id: 'layerDemo' + type//防止重复弹出
                        , content: '<div style="padding: 20px 100px;">' + received_msg[1] + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else if (received_msg[0] === 'exclusive') {
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '发布结果'
                        , id: 'layerDemo' + type//防止重复弹出
                        , content: '<div style="padding: 20px 100px;">' + received_msg[1] + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else if (received_msg[0] === 'on_building') {
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '发布结果'
                        , id: 'layerDemo' + type//防止重复弹出
                        , content: '<div style="padding: 20px 100px;">' + received_msg[1] + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else if (received_msg[0] === 'no_branch') {
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '发布结果'
                        , id: 'layerDemo' + type//防止重复弹出
                        , content: '<div style="padding: 20px 100px;">' + "没有预发分支，请先创建！" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else if (received_msg[0] === 'out_of_date') {
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '发布结果'
                        , id: 'layerDemo' + type//防止重复弹出
                        , content: '<div style="padding: 20px 100px;">' + "该预发分支已经过时，请重新创建！" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else {
                    var html = "<div class=\"layui-progress layui-progress-\" lay-filter=\"uatDeploy\">\n" +
                        "  <div class=\"layui-progress-bar\" id='uatBuildProgress' lay-percent=\"0%\"></div>\n" +
                        "</div>";
                    $(`#${tr_id} #uatDeploy`).hide();
                    $(`#${tr_id} #uatProgress`).html(html);
                    $(`#${tr_id} #uatJenkinsConsole`).html("准备中...");
                    for (var i = 0; i < received_msg.length; i++) {
                        if (received_msg[i] === 'no_jenkinsJob') {
                            i += 1;
                            var html4 = "<div class=\"sufee-alert alert with-close alert-danger alert-dismissible\">\n" +
                                "<span class=\"badge badge-pill badge-primary\">Failure</span>\n" +
                                received_msg[i] +
                                "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                "aria-label=\"Close\">\n" +
                                "<span aria-hidden=\"true\">&times;</span>\n" +
                                "</button>\n" +
                                "</div>";
                            $(`#${tr_id} #uatDeploy`).show();
                            $(`#${tr_id} #uatStopDeploy`).hide();
                            $('#uatBuildMessage').html(html4);
                            $('#uatBuildProgress').addClass("layui-bg-red");
                            $(`#${tr_id} #uatBuildStatus`).html("部署终止")
                        }
                        if (received_msg[i] === 'deploy') {
                            i += 1;
                            element.progress('uatDeploy', '40%');
                            var html2 = "<a href='" + received_msg[i] + "' target='_blank' class='btn btn-link btn-sm'>去Jenkins上看</a><br>";
                            $(`#${tr_id} #uatJenkinsConsole`).html(html2);
                            $(`#${tr_id} #uatStopDeploy`).show();
                        } else if (received_msg[i] === 'success') {
                            i += 1;
                            html3 += "<div class=\"sufee-alert alert with-close alert-success alert-dismissible\">\n" +
                                "<span class=\"badge badge-pill badge-primary\">Success</span>\n" +
                                received_msg[i] +
                                "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                "aria-label=\"Close\">\n" +
                                "<span aria-hidden=\"true\">&times;</span>\n" +
                                "</button>\n" +
                                "</div>";
                            $('#uatBuildMessage').html(html3);
                            $(`#${tr_id} #uatDeploy`).show();
                            $(`#${tr_id} #uatStopDeploy`).hide();
                            i += 1;
                            element.progress('uatDeploy', '100%');
                            $(`#${tr_id} #uatBuildStatus`).html("部署成功");
                            $(`#${tr_id} #uatPackageId`).html(received_msg[i]);
                        } else if (received_msg[i] === 'fail') {
                            i += 1;
                            html3 += "<div class=\"sufee-alert alert with-close alert-danger alert-dismissible\">\n" +
                                "<span class=\"badge badge-pill badge-primary\">Failure</span>\n" +
                                received_msg[i] +
                                "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                "aria-label=\"Close\">\n" +
                                "<span aria-hidden=\"true\">&times;</span>\n" +
                                "</button>\n" +
                                "</div>";
                            $('#uatBuildMessage').html(html3);
                            $(`#${tr_id} #uatDeploy`).show();
                            $(`#${tr_id} #uatStopDeploy`).hide();
                            $('#uatBuildProgress').addClass("layui-bg-red");
                            $(`#${tr_id} #uatBuildStatus`).html("部署失败")
                        }
                    }
                }
            };

            ws.onclose = function () {
                // 关闭 websocket
                console.log("连接已关闭...");
            };
        }

        else {
            // 浏览器不支持 WebSocket
            console.alert("您的浏览器不支持 WebSocket!");
        }
    }
});
//预发终止部署
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", "#uatStopDeploy", function () {
        var tr_id = $(this).closest("tr").attr("id");
        var projectId = getQueryVariable("prjId");
        var planId = getQueryVariable("pid");
        var postData = {};
        postData['projectId'] = projectId;
        postData['planId'] = planId;
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(tr_id, postData);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(tr_id, postData) {
            $.ajax({
                url: '/ajax_uatStopDeploy',
                type: 'POST',
                data: postData,

                success: function (data) {
                    if (data.role === 0) {
                        layer.open({
                            type: 1
                            , title: '警告'
                            , content: '<div style="padding: 20px 100px;">' + "你没有终止发布的权限" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                    } else if (data.start === false) {
                        var html = "<div class=\"sufee-alert alert with-close alert-success alert-dismissible\">\n" +
                            "<span class=\"badge badge-pill badge-primary\">Success</span>\n" +
                            data.project + "未进行发布！" +
                            "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                            "aria-label=\"Close\">\n" +
                            "<span aria-hidden=\"true\">&times;</span>\n" +
                            "</button>\n" +
                            "</div>";
                        $('#uatBuildMessage').html(html);
                        $(`#${tr_id} #uatProgress`).html("未进行");
                        $(`#${tr_id} #uatJenkinsConsole`).html("无");
                    }
                    else if (data.stop === true) {
                        var html2 = "<div class=\"sufee-alert alert with-close alert-success alert-dismissible\">\n" +
                            "<span class=\"badge badge-pill badge-primary\">Success</span>\n" +
                            data.project + "已经终止发布！" +
                            "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                            "aria-label=\"Close\">\n" +
                            "<span aria-hidden=\"true\">&times;</span>\n" +
                            "</button>\n" +
                            "</div>";
                        $('#uatBuildMessage').html(html2);
                        $(`#${tr_id} #uatDeploy`).show();
                        $(`#${tr_id} #uatStopDeploy`).hide();
                        $(`#${tr_id} #uatBuildStatus`).html("部署终止");
                        $(`#${tr_id} #uatProgress`).html("已结束");
                    } else if (data.build === true) {
                        var html3 = "<div class=\"sufee-alert alert with-close alert-success alert-dismissible\">\n" +
                            "<span class=\"badge badge-pill badge-primary\">Success</span>\n" +
                            data.project + "已经发布完成！" +
                            "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                            "aria-label=\"Close\">\n" +
                            "<span aria-hidden=\"true\">&times;</span>\n" +
                            "</button>\n" +
                            "</div>";
                        $('#uatBuildMessage').html(html3);
                        $(`#${tr_id} #uatDeploy`).show();
                        $(`#${tr_id} #uatStopDeploy`).hide();
                        $(`#${tr_id} #uatBuildStatus`).html("部署完成");
                        $(`#${tr_id} #uatProgress`).html("已结束");
                    }
                    else {
                        var html4 = "<div class=\"sufee-alert alert with-close alert-warning alert-dismissible\">\n" +
                            "<span class=\"badge badge-pill badge-primary\">Fail</span>\n" +
                            data.project + "已经发布，并且发布失败！" +
                            "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                            "aria-label=\"Close\">\n" +
                            "<span aria-hidden=\"true\">&times;</span>\n" +
                            "</button>\n" +
                            "</div>";
                        $('#uatBuildMessage').html(html4);
                        $(`#${tr_id} #uatDeploy`).show();
                        $(`#${tr_id} #uatStopDeploy`).hide();
                        $(`#${tr_id} #uatBuildStatus`).html("部署失败");
                        $(`#${tr_id} #uatProgress`).html("已结束");
                    }
                },
                error: function () {
                    console.log("error");
                }
            })
        }
    });
});
//预发验收通过
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", ".uatCheckBtn", function () {
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok();
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok() {
            var postData = {};
            var planId = getQueryVariable("pid");
            var uatRemark = $('#uatRemark').val();
            postData['planId'] = planId;
            postData['remark'] = uatRemark;

            $.ajax({
                url: '/ajax_uatCheck',
                type: 'POST',
                data: postData,

                success: function (data) {
                    if (data.role === 0) {
                        layer.open({
                            type: 1
                            , title: '警告'
                            , content: '<div style="padding: 20px 100px;">' + "你没有预发验收的权限！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                    } else {
                        if (data.deployed === 0) {
                            layer.open({
                                type: 1
                                ,
                                title: '警告'
                                ,
                                content: '<div style="padding: 20px 100px;">' + "预发项目" + data.projects + "还没有部署！" + '</div>'
                                ,
                                btn: '关闭'
                                ,
                                btnAlign: 'c' //按钮居中
                                ,
                                area: '500px;'
                                ,
                                shade: 0.5 //不显示遮罩
                                ,
                                yes: function () {
                                    layer.closeAll();
                                }
                            });
                        } else {
                            console.log(data);
                            $('#uatForm').hide();
                            var html = "<br>验收通过\n" +
                                "<br>验收人：" + data.uatCheckMember + "\n" +
                                "<br>验收日期：" + data.uatCheckDate + "\n" +
                                "<br>备注：" + data.uatRemark;
                            $("#uatP1").show().html(html);
                        }
                    }
                },
                error: function () {
                    console.log("error");
                }
            })
        }
    });
});
//重新上预发
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", "#restartUatDeploy", function () {
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok();
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok() {
            var postData = {};
            var planId = getQueryVariable('pid');
            postData['planId'] = planId;

            $.ajax({
                url: '/ajax_restartUatDeploy',
                type: 'POST',
                data: postData,

                success: function (data) {
                    if (data.role === false) {
                        layer.open({
                            type: 1
                            , title: '警告'
                            , content: '<div style="padding: 20px 100px;">' + "你没有重新上预发的权限！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                    } else if (data.uatCheck === false) {
                        layer.open({
                            type: 1
                            , title: '警告'
                            , content: '<div style="padding: 20px 100px;">' + "预发未验收！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                    } else if (data.uatCheck === true) {
                        location.reload();
                    } else if (data.proCheck === true) {
                        layer.open({
                            type: 1
                            , title: '警告'
                            , content: '<div style="padding: 20px 100px;">' + "生产已验收，不能再上预发！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                    }
                    else {
                        location.reload();
                    }
                },
                error: function () {
                    console.log("error");
                }
            })
        }
    });
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
        var remark = $(this).parent().children("#remark").val();
        var sequenceId = $(this).attr("id");
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(step, remark, sequenceId);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(step, remark, sequenceId) {
            var taskId = getQueryVariable("tid");
            var postData = {};
            postData['id'] = sequenceId;
            postData['remark'] = remark;
            postData['taskId'] = taskId;

            $.ajax({
                url: '/ajax_taskImplement',
                type: 'POST',
                data: postData,

                success: function (data) {
                    if (data.role === 1) {
                        $(`#${step} #p1`).removeClass("fade").html(data.remark);
                        $(`#${step} .segmentBtn`).hide();
                        $(`#${step} #remark`).hide();
                        $(`#${step} #nextBtn`).show();
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
        }

    });
});
//合并代码
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    var type = $(this).data('type');
    $("body").on("click", ".startCodeMerge", startCodeMerge);

    function startCodeMerge() {
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok();
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok() {
            var taskId = getQueryVariable("tid");
            $('#codeMergeText').text("代码合并进行中，请等待...");
            $('.codeMergeProgress').show();
            $('#codeMerge').width(5 + '%').text('5%');
            $('#codeMergeOpt').show();
            $('.startCodeMerge').hide();
            if ("WebSocket" in window) {
                console.log("您的浏览器支持 WebSocket!");

                // 打开一个 web socket
                var ws = new WebSocket("ws:" + window.location.host + "/ws_codeMerge");

                ws.onopen = function () {
                    ws.send(taskId);
                    console.log("数据已发送...");
                };

                ws.onmessage = function (evt) {
                    var received_msg = JSON.parse(evt.data);
                    console.log("数据已接收...");
                    if (received_msg[0] === 'no_role') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "你没有合并分支的权限！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $('#codeMergeText').hide();
                        $('.codeMergeProgress').hide();
                        $('#codeMergeOpt').hide();
                    } else {
                        var html = "";
                        var sumPoints = received_msg[0];
                        var realPoints = 0;
                        for (var i = 1; i < received_msg.length; i++) {
                            if (received_msg[i] === 'startMerge') {
                                realPoints++;
                                $('#codeMergeText').text("代码合并进行中，共" + sumPoints + "个，完成第" + realPoints + "个");
                                var widthTemp = (realPoints / sumPoints) * 100;
                                $('#codeMergeProgressLine').width(widthTemp + '%').text(widthTemp + '%');
                                html += "<br>" + received_msg[i + 1];
                            }
                            else if (received_msg[i] === 'complete') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '合并结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + "合并结束！" + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                            }
                        }
                        $(`.codeMergeResult`).html(html);
                        if (realPoints === sumPoints) {
                            $('#codeMergeText').text("合并完成");
                        }
                    }
                };

                ws.onclose = function () {
                    // 关闭 websocket
                    console.log("连接已关闭...");
                };
            }

            else {
                // 浏览器不支持 WebSocket
                console.alert("您的浏览器不支持 WebSocket!");
            }
        }
    }
});
//生产发布历史刷新
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery;
    $("body").on("click", "#proConsoleOptRefresh", proConsoleOptRefresh);

    function proConsoleOptRefresh() {
        var taskId = getQueryVariable("tid");
        if ("WebSocket" in window) {
            console.log("您的浏览器支持 WebSocket!");

            // 打开一个 web socket
            var ws = new WebSocket("ws:" + window.location.host + "/ws_proConsoleOptRefresh");

            ws.onopen = function () {
                ws.send(taskId);
                console.log("数据已发送...");
            };

            ws.onmessage = function (evt) {
                var received_msg = JSON.parse(evt.data);
                var html = "";
                console.log("数据已接收...");
                for (var i = 0; i < received_msg.length; i++) {
                    if (received_msg[i] === 'console') {
                        html += "<li class=\"layui-timeline-item\">\n" +
                            "                                                                        <i class=\"layui-icon layui-timeline-axis\">&#xe63f;</i>\n" +
                            "                                                                        <div class=\"layui-timeline-content layui-text\">\n" +
                            "                                                                            <h3 class=\"layui-timeline-title\">"
                        html += received_msg[i + 1];
                        html += "<h3><p>";
                        if (received_msg[i + 2] === 0) {
                            html += "操作：发布";
                        } else {
                            html += "操作：回滚";
                        }
                        html += "<br>执行人：" + received_msg[i + 3];
                        html += "<br><a href='/pro_console_opt/" + received_msg[i + 4] + "'>查看控制台信息</a>"
                        html += "</p></div></li>"
                    }
                }
                $('.proConsoleOptRefresh').html(html);
            };

            ws.onclose = function () {
                // 关闭 websocket
                console.log("连接已关闭...");
            };
        }

        else {
            // 浏览器不支持 WebSocket
            console.alert("您的浏览器不支持 WebSocket!");
        }
    }
});
//预发发布历史刷新
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery;
    $("body").on("click", "#uatConsoleOptRefresh", uatConsoleOptRefresh);

    function uatConsoleOptRefresh() {
        var projectId = getQueryVariable("prjId");
        var planId = getQueryVariable("pid");
        var combination = projectId + '-' + planId;
        if ("WebSocket" in window) {
            console.log("您的浏览器支持 WebSocket!");

            // 打开一个 web socket
            var ws = new WebSocket("ws:" + window.location.host + "/ws_uatConsoleOptRefresh");

            ws.onopen = function () {
                ws.send(combination);
                console.log("数据已发送...");
            };

            ws.onmessage = function (evt) {
                var received_msg = JSON.parse(evt.data);
                var html = "";
                console.log("数据已接收...");
                for (var i = 0; i < received_msg.length; i++) {
                    if (received_msg[i] === 'console') {
                        html += "<li class=\"layui-timeline-item\">\n" +
                            "                                                                        <i class=\"layui-icon layui-timeline-axis\">&#xe63f;</i>\n" +
                            "                                                                        <div class=\"layui-timeline-content layui-text\">\n" +
                            "                                                                            <h3 class=\"layui-timeline-title\">"
                        html += received_msg[i + 1];
                        html += "<h3><p>";
                        html += "<br>执行人：" + received_msg[i + 2];
                        html += "<br><a href='/pro_console_opt/" + received_msg[i + 3] + "'>查看控制台信息</a>"
                        html += "</p></div></li>"
                    }
                }
                $('.uatConsoleOptRefresh').html(html);
            };

            ws.onclose = function () {
                // 关闭 websocket
                console.log("连接已关闭...");
            };
        }

        else {
            // 浏览器不支持 WebSocket
            console.alert("您的浏览器不支持 WebSocket!");
        }
    }
});
//任务删除
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", ".deleteTask", function () {
        var tr = $(this).parent().parent();
        var taskId = tr.children("td#taskId").text();
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(tr, taskId);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(tr, taskId) {
            var postData = {};
            postData['id'] = taskId;

            $.ajax({
                url: '/ajax_deleteTask',
                type: 'POST',
                data: postData,

                success: function (data) {
                    if (data.role === 0) {
                        layer.open({
                            type: 1
                            , title: '警告'
                            , content: '<div style="padding: 20px 100px;">' + "你没有删除任务的权限" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                    } else {
                        tr.remove();
                    }
                },
                error: function () {
                    console.log("error");
                }
            })
        }
    });
});
//计划删除
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", ".deletePlan", function () {
        var tr = $(this).parent().parent();
        var planId = tr.children("td#planId").text();
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(tr, planId);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(tr, planId) {
            var postData = {};
            postData['id'] = planId;

            $.ajax({
                url: '/ajax_deletePlan',
                type: 'POST',
                data: postData,

                success: function (data) {
                    if (data.role === 0) {
                        layer.open({
                            type: 1
                            , title: '警告'
                            , content: '<div style="padding: 20px 100px;">' + "你没有删除计划的权限" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                    } else {
                        tr.remove();
                    }
                },
                error: function () {
                    console.log("error");
                }
            })
        }
    });
});
//添加项目
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", "#addProject", function () {
        var project = $('#project').find('option:selected').text();
        var branch = $('#branch').find('option:selected').text();
        var planId = getQueryVariable("pid");
        var postData = {};
        postData['id'] = planId;
        postData['project'] = project;
        postData['branch'] = branch;

        $.ajax({
            url: '/ajax_addProject',
            type: 'POST',
            data: postData,

            success: function (data) {
                console.log(data.params, data.project, data.branch);
                if (data.role === false) {
                    layer.open({
                        type: 1
                        , title: '警告'
                        , content: '<div style="padding: 20px 100px;">' + "你没有添加计划的权限" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else if (data.checked === true) {
                    layer.open({
                        type: 1
                        , title: '警告'
                        , content: '<div style="padding: 20px 100px;">' + "预发已验收，不能添加项目！" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else if (data.params === false) {
                    layer.open({
                        type: 1
                        , title: '警告'
                        , content: '<div style="padding: 20px 100px;">' + "项目或分支没有选择！" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else {
                    location.reload();
                }
            },
            error: function () {
                console.log("error");
            }
        })
    });
});
//删除项目
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", ".deleteProject", function () {
        var tr = $(this).parent().parent();
        var project_plan_id = tr.children("td#project_plan_id").text();
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(tr, project_plan_id);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(tr, project_plan_id) {
            var postData = {};
            postData['id'] = project_plan_id;

            $.ajax({
                url: '/ajax_deleteProject',
                type: 'POST',
                data: postData,

                success: function (data) {
                    if (data.role === false) {
                        layer.open({
                            type: 1
                            , title: '警告'
                            , content: '<div style="padding: 20px 100px;">' + "你没有删除项目的权限" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                    } else if (data.checked === true) {
                        layer.open({
                            type: 1
                            , title: '警告'
                            , content: '<div style="padding: 20px 100px;">' + "预发已验收，不能删除项目！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                    }
                    else {
                        tr.remove();
                    }
                },
                error: function () {
                    console.log("error");
                }
            })
        }
    });
});
//部署单个节点
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer, element = layui.element;
    $("body").on("click", "#startOneDeploy", startOneDeploy);

    function startOneDeploy() {
        var type = $(this).data('type');
        var id = $(this).closest("tr").find("#project_plan_id").text();
        var tr_id = $(this).closest("tr").attr("id");
        var step = $(this).parent().parent().parent().parent().parent().parent().attr('id');
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(id, type, step, tr_id);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(id, type, step, tr_id) {
            $(`#${tr_id} #startOneDeploy`).hide();
            $(`#${tr_id} #select-nodes-deploy`).hide();

            if ("WebSocket" in window) {
                console.log("您的浏览器支持 WebSocket!");

                // 打开一个 web socket
                var ws = new WebSocket("ws:" + window.location.host + "/ws_proOneProjectDeploy");

                ws.onopen = function () {
                    ws.send(id);
                    console.log("数据已发送...");
                };

                ws.onmessage = function (evt) {
                    var received_msg = JSON.parse(evt.data);
                    console.log("数据已接收...");
                    if (received_msg[0] === 'no_role') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "你没有发布的权限！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else if (received_msg[0] === 'already_proCheck') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "生产已经验收通过，不能重复发布！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else if (received_msg[0] === 'on_building') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "项目正在发布中，不能重复发布，请等待发布完成后再重新发布！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else if (received_msg[0] === 'no_reversion') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "项目没有发布版本，请检查预发环境是否部署！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else if (received_msg[0] === 'out_of_date') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "项目预发分支已经过时，请重新创建！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else {
                        var sumPoints = received_msg[0];
                        var realPoints = 0;
                        var html = "";
                        var html2 = "";
                        var html3 = "";
                        var num = new Array(sumPoints);
                        for (var j = 1; j <= sumPoints; j++) {
                            num[j] = RandomNumBoth(10000, 100000);
                            html += "IP" + j + "：\n" +
                                "<div class=\"layui-progress\" lay-filter=\"proOneDeploy" + num[j] + "\">\n" +
                                "<div class=\"layui-progress-bar\"\n" +
                                "id=\"proBuildProgress" + num[j] + "\" lay-percent=\"0%\"></div>\n" +
                                "</div>";
                        }
                        $(`#${tr_id} #progress`).html(html);
                        $(`#${tr_id} #jenkinsConsole`).html("准备中...");
                        for (var i = 1; i < received_msg.length; i++) {
                            if (received_msg[i] === 'no_jenkinsJob') {
                                i += 1;
                                html4 += "<div class=\"sufee-alert alert with-close alert-danger alert-dismissible\">\n" +
                                    "<span class=\"badge badge-pill badge-primary\">Failure</span>\n" +
                                    received_msg[i] +
                                    "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                    "aria-label=\"Close\">\n" +
                                    "<span aria-hidden=\"true\">&times;</span>\n" +
                                    "</button>\n" +
                                    "</div>";
                                $('#buildMessage').html(html4);
                                $(`#proBuildProgress${num[realPoints]}`).addClass("layui-bg-red");
                                $(`#${tr_id} #proBuildStatus`).html("部署终止");
                                $(`#${tr_id} #startOneDeploy`).show();
                                $(`#${tr_id} #select-nodes-deploy`).show();
                                $(`#${tr_id} #stopDeploy`).hide();
                            } else if (received_msg[i] === 'start_deploy') {
                                realPoints++;
                                i += 1;
                                element.progress(`proOneDeploy${num[realPoints]}`, '40%');
                                html3 += "IP" + realPoints + "：\n" +
                                    "<a href='" + received_msg[i] + "' target='_blank' class='btn btn-link btn-sm'>去Jenkins上看</a><br>";
                                $(`#${tr_id} #jenkinsConsole`).html(html3);
                                $(`#${tr_id} #stopDeploy`).show();
                            } else if (received_msg[i].length === 10) {
                                element.progress(`proOneDeploy${num[realPoints]}`, '100%');
                                $(`#${tr_id} #stopDeploy`).hide();
                            } else if (received_msg[i] === 'deploy_failed') {
                                i += 1;
                                html2 += "<div class=\"sufee-alert alert with-close alert-danger alert-dismissible\">\n" +
                                    "<span class=\"badge badge-pill badge-primary\">Failure</span>\n" +
                                    received_msg[i] +
                                    "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                    "aria-label=\"Close\">\n" +
                                    "<span aria-hidden=\"true\">&times;</span>\n" +
                                    "</button>\n" +
                                    "</div>";
                                $('#buildMessage').html(html2);
                                $(`#proBuildProgress${num[realPoints]}`).addClass("layui-bg-red");
                                $(`#${tr_id} #proBuildStatus`).html("部署失败")
                                $(`#${tr_id} #startOneDeploy`).show();
                                $(`#${tr_id} #select-nodes-deploy`).show();
                                $(`#${tr_id} #stopDeploy`).hide();
                            } else if (received_msg[i] === 'deploy_success') {
                                i += 1;
                                html2 += "<div class=\"sufee-alert alert with-close alert-success alert-dismissible\">\n" +
                                    "<span class=\"badge badge-pill badge-primary\">Success</span>\n" +
                                    received_msg[i] +
                                    "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                    "aria-label=\"Close\">\n" +
                                    "<span aria-hidden=\"true\">&times;</span>\n" +
                                    "</button>\n" +
                                    "</div>";
                                $('#buildMessage').html(html2);
                                $(`#${tr_id} #proBuildStatus`).html("部署成功");
                                $(`#${tr_id} #startOneDeploy`).show();
                                $(`#${tr_id} #select-nodes-deploy`).show();
                                $(`#${tr_id} #stopDeploy`).hide();
                            } else if (received_msg[i] === 'sequence_success') {
                                $(`#${step} #nextBtn`).show();
                            }
                        }
                    }
                };

                ws.onclose = function () {
                    // 关闭 websocket
                    console.log("连接已关闭...");
                };
            }

            else {
                // 浏览器不支持 WebSocket
                console.alert("您的浏览器不支持 WebSocket!");
            }
        }

    }
});
//选节点部署
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer, element = layui.element;
    $("body").on("click", "#selectNodesDeploy", selectNodesDeploy);

    function selectNodesDeploy() {
        var id = $('#select-nodes').find('td:eq(1)').text();
        var step = $('#build-table').parent().attr('id');
        var tr_id = 'proBuild' + id;
        var type = $(this).data('type');
        var arrayObj = new Array();
        arrayObj.push(id);
        $.each($('input:checkbox:checked'), function () {
            arrayObj.push($(this).parent().parent().children().eq(3).html());
        });
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(type, arrayObj, step);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(type, arrayObj, step) {
            $(`#${tr_id} #startOneDeploy`).hide();
            $(`#${tr_id} #select-nodes-deploy`).hide();

            if ("WebSocket" in window) {
                console.log("您的浏览器支持 WebSocket!");

                // 打开一个 web socket
                var ws = new WebSocket("ws:" + window.location.host + "/ws_selectNodesDeploy");

                ws.onopen = function () {
                    ws.send(arrayObj);
                    console.log("数据已发送...");
                };

                ws.onmessage = function (evt) {
                    var received_msg = JSON.parse(evt.data);
                    console.log("数据已接收...");
                    if (received_msg[0] === 'no_role') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "你没有发布的权限！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else if (received_msg[0] === 'already_proCheck') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "生产已经验收通过，不能重复发布！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else if (received_msg[0] === 'on_building') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "项目正在发布中，不能重复发布，请等待发布完成后再重新发布！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else if (received_msg[0] === 'out_of_date') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "项目预发分支已经过时，请重新创建后部署！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else if (received_msg[0] === 'no_reversion') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "项目没有发布版本，请检查预发环境是否部署！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else {
                        var sumPoints = received_msg[0];
                        var realPoints = 0;
                        var html = "";
                        var html2 = "";
                        var html3 = "";
                        var html4 = "";
                        var num = new Array(sumPoints);
                        if (sumPoints === 0) {
                            layer.open({
                                type: 1
                                , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                , title: '发布结果'
                                , id: 'layerDemo' + type//防止重复弹出
                                , content: '<div style="padding: 20px 100px;">' + "没有选择需要发布的IP！" + '</div>'
                                , btn: '关闭'
                                , btnAlign: 'c' //按钮居中
                                , area: '500px;'
                                , shade: 0.5 //不显示遮罩
                                , yes: function () {
                                    layer.closeAll();
                                }
                            });
                            $(`#${tr_id} #startOneDeploy`).show();
                            $(`#${tr_id} #select-nodes-deploy`).show();
                            $(`#${tr_id} #stopDeploy`).hide();
                        } else {
                            for (var j = 1; j <= sumPoints; j++) {
                                num[j] = RandomNumBoth(10000, 100000);
                                html += "IP" + j + "：\n" +
                                    "<div class=\"layui-progress\" lay-filter=\"proOneDeploy" + num[j] + "\">\n" +
                                    "<div class=\"layui-progress-bar\"\n" +
                                    "id=\"proBuildProgress" + num[j] + "\" lay-percent=\"0%\"></div>\n" +
                                    "</div>"
                            }
                            $(`#${tr_id} #jenkinsConsole`).html("准备中...");
                            $(`#${tr_id} #progress`).html(html);
                            for (var i = 1; i < received_msg.length; i++) {
                                if (received_msg[i] === 'no_jenkinsJob') {
                                    i += 1;
                                    html4 += "<div class=\"sufee-alert alert with-close alert-danger alert-dismissible\">\n" +
                                        "<span class=\"badge badge-pill badge-primary\">Failure</span>\n" +
                                        received_msg[i] +
                                        "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                        "aria-label=\"Close\">\n" +
                                        "<span aria-hidden=\"true\">&times;</span>\n" +
                                        "</button>\n" +
                                        "</div>";
                                    $('#buildMessage').html(html4);
                                    $(`#proBuildProgress${num[realPoints]}`).addClass("layui-bg-red");
                                    $(`#${tr_id} #proBuildStatus`).html("部署终止");
                                    $(`#${tr_id} #startOneDeploy`).show();
                                    $(`#${tr_id} #select-nodes-deploy`).show();
                                    $(`#${tr_id} #stopDeploy`).hide();
                                } else if (received_msg[i] === 'start_deploy') {
                                    realPoints++;
                                    i += 1;
                                    element.progress(`proOneDeploy${num[realPoints]}`, '40%');
                                    html3 += "IP" + realPoints + "：\n" +
                                        "<a href='" + received_msg[i] + "' target='_blank' class='btn btn-link btn-sm'>去Jenkins上看</a><br>";
                                    $(`#${tr_id} #jenkinsConsole`).html(html3);
                                    $(`#${tr_id} #stopDeploy`).show();
                                } else if (received_msg[i].length === 10) {
                                    element.progress(`proOneDeploy${num[realPoints]}`, '100%');
                                    $(`#${tr_id} #stopDeploy`).hide();
                                } else if (received_msg[i] === 'deploy_failed') {
                                    i += 1;
                                    html2 += "<div class=\"sufee-alert alert with-close alert-danger alert-dismissible\">\n" +
                                        "<span class=\"badge badge-pill badge-primary\">Failure</span>\n" +
                                        received_msg[i] +
                                        "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                        "aria-label=\"Close\">\n" +
                                        "<span aria-hidden=\"true\">&times;</span>\n" +
                                        "</button>\n" +
                                        "</div>";
                                    $('#buildMessage').html(html2);
                                    $(`#proBuildProgress${num[realPoints]}`).addClass("layui-bg-red");
                                    $(`#${tr_id} #proBuildStatus`).html("部署失败")
                                    $(`#${tr_id} #startOneDeploy`).show();
                                    $(`#${tr_id} #select-nodes-deploy`).show();
                                    $(`#${tr_id} #stopDeploy`).hide();
                                } else if (received_msg[i] === 'deploy_success') {
                                    i += 1;
                                    html2 += "<div class=\"sufee-alert alert with-close alert-success alert-dismissible\">\n" +
                                        "<span class=\"badge badge-pill badge-primary\">Success</span>\n" +
                                        received_msg[i] +
                                        "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                        "aria-label=\"Close\">\n" +
                                        "<span aria-hidden=\"true\">&times;</span>\n" +
                                        "</button>\n" +
                                        "</div>";
                                    $('#buildMessage').html(html2);
                                    $(`#${tr_id} #proBuildStatus`).html("部署成功");
                                    $(`#${tr_id} #startOneDeploy`).show();
                                    $(`#${tr_id} #select-nodes-deploy`).show();
                                    $(`#${tr_id} #stopDeploy`).hide();
                                    ;
                                } else if (received_msg[i] === 'sequence_success') {
                                    $(`#${step} #nextBtn`).show();
                                }
                            }
                        }
                    }
                };

                ws.onclose = function () {
                    // 关闭 websocket
                    console.log("连接已关闭...");
                };
            }

            else {
                // 浏览器不支持 WebSocket
                console.alert("您的浏览器不支持 WebSocket!");
            }
        }

    }
});
//生产终止发布
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", "#stopDeploy", function () {
        var tr = $(this).parent().parent().parent();
        var tr_id = tr.attr("id");
        var id = tr.children().eq(1).text();
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(tr, id, tr_id);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(tr, id, tr_id) {
            $.ajax({
                url: '/ajax_stopDeploy',
                type: 'POST',
                data: {'id': id},

                success: function (data) {
                    if (data.role === 0) {
                        layer.open({
                            type: 1
                            , title: '警告'
                            , content: '<div style="padding: 20px 100px;">' + "你没有终止发布的权限" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                    } else if (data.start === false) {
                        var html = "<div class=\"sufee-alert alert with-close alert-success alert-dismissible\">\n" +
                            "<span class=\"badge badge-pill badge-primary\">Success</span>\n" +
                            data.project + "未进行发布！" +
                            "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                            "aria-label=\"Close\">\n" +
                            "<span aria-hidden=\"true\">&times;</span>\n" +
                            "</button>\n" +
                            "</div>";
                        $('#buildMessage').html(html);
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                        tr.children("td#progress").html("无");
                        tr.children("td#jenkinsConsole").html("无");
                    }
                    else if (data.stop === true) {
                        var html2 = "<div class=\"sufee-alert alert with-close alert-success alert-dismissible\">\n" +
                            "<span class=\"badge badge-pill badge-primary\">Success</span>\n" +
                            data.project + "已经终止发布！" +
                            "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                            "aria-label=\"Close\">\n" +
                            "<span aria-hidden=\"true\">&times;</span>\n" +
                            "</button>\n" +
                            "</div>";
                        $('#buildMessage').html(html2);
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                        tr.children("td#progress").html("已终止");
                    } else if (data.build === true) {
                        var html3 = "<div class=\"sufee-alert alert with-close alert-success alert-dismissible\">\n" +
                            "<span class=\"badge badge-pill badge-primary\">Success</span>\n" +
                            data.project + "已经发布完成！" +
                            "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                            "aria-label=\"Close\">\n" +
                            "<span aria-hidden=\"true\">&times;</span>\n" +
                            "</button>\n" +
                            "</div>";
                        $('#buildMessage').html(html3);
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                        tr.children("td#progress").html("发布成功");
                    }
                    else {
                        var html4 = "<div class=\"sufee-alert alert with-close alert-warning alert-dismissible\">\n" +
                            "<span class=\"badge badge-pill badge-primary\">Fail</span>\n" +
                            data.project + "已经发布，并且发布失败！" +
                            "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                            "aria-label=\"Close\">\n" +
                            "<span aria-hidden=\"true\">&times;</span>\n" +
                            "</button>\n" +
                            "</div>";
                        $('#buildMessage').html(html4);
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                        tr.children("td#progress").html("发布失败");
                    }
                },
                error: function () {
                    console.log("error");
                }
            })
        }
    });
});
//释放预发独占锁
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", "#releaseExclusiveKey", function () {
        var arrayObj = new Array();
        $.each($('input:checkbox:checked'), function () {
            arrayObj.push($(this).parent().parent().children().eq(1).html());
        });
        console.log(arrayObj[0]);

        $.ajax({
            url: '/ajax_releaseExclusiveKey',
            type: 'POST',
            traditional: true,
            dataType: "json",
            data: {'ids': arrayObj},

            success: function (data) {
                if (data.role === false) {
                    layer.open({
                        type: 1
                        , title: '警告'
                        , content: '<div style="padding: 20px 100px;">' + "你没有释放预发独占锁的权限" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                } else if (data.release === true) {
                    layer.open({
                        type: 1
                        , title: '警告'
                        , content: '<div style="padding: 20px 100px;">' + "预发独占锁已经释放！" + '</div>'
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
//生产回滚
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer, element = layui.element;
    $("body").on("click", "#rollback", rollback);

    function rollback() {
        var step = $('#build-table').parent().attr('id');
        var type = $(this).data('type');
        var tr = $(this).closest("tr");
        var tr_id = tr.attr('id');
        var id = tr.children().eq(1).text();

        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(id, type, tr_id, step);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(id, type, tr_id, step) {
            $(`#${tr_id} #startOneDeploy`).hide();
            $(`#${tr_id} #select-nodes-deploy`).hide();

            if ("WebSocket" in window) {
                console.log("您的浏览器支持 WebSocket!");

                // 打开一个 web socket
                var ws = new WebSocket("ws:" + window.location.host + "/ws_rollback");

                ws.onopen = function () {
                    ws.send(id);
                    console.log("数据已发送...");
                };

                ws.onmessage = function (evt) {
                    var received_msg = JSON.parse(evt.data);
                    console.log("数据已接收...");
                    if (received_msg[0] === 'no_role') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "你没有回滚的权限！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else if (received_msg[0] === 'already_proCheck') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "生产已经验收通过，不能回滚！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else if (received_msg[0] === 'no_deploy') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "生产未部署，不需要回滚！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else if (received_msg[0] === 'on_building') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "项目正在发布中，不能回滚，请等待发布完成后再回滚！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                    } else if (received_msg[0] === 'first_version') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "已经是最早的版本，无法回滚！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $(`#${tr_id} #startOneDeploy`).show();
                        $(`#${tr_id} #select-nodes-deploy`).show();
                        $(`#${tr_id} #stopDeploy`).hide();
                    } else {
                        var sumPoints = received_msg[0];
                        var realPoints = 0;
                        var html = "";
                        var html2 = "";
                        var html3 = "";
                        var num = new Array(sumPoints);
                        for (var j = 1; j <= sumPoints; j++) {
                            num[j] = RandomNumBoth(10000, 100000);
                            html += "IP" + j + "：\n" +
                                "<div class=\"layui-progress\" lay-filter=\"proOneDeploy" + num[j] + "\">\n" +
                                "<div class=\"layui-progress-bar\"\n" +
                                "id=\"proBuildProgress" + num[j] + "\" lay-percent=\"0%\"></div>\n" +
                                "</div>";
                        }
                        $(`#${tr_id} #progress`).html(html);
                        $(`#${tr_id} #jenkinsConsole`).html("准备中...");
                        for (var i = 1; i < received_msg.length; i++) {
                            if (received_msg[i] === 'no_jenkinsJob') {
                                i += 1;
                                html4 += "<div class=\"sufee-alert alert with-close alert-danger alert-dismissible\">\n" +
                                    "<span class=\"badge badge-pill badge-primary\">Failure</span>\n" +
                                    received_msg[i] +
                                    "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                    "aria-label=\"Close\">\n" +
                                    "<span aria-hidden=\"true\">&times;</span>\n" +
                                    "</button>\n" +
                                    "</div>";
                                $('#buildMessage').html(html4);
                                $(`#proBuildProgress${num[realPoints]}`).addClass("layui-bg-red");
                                $(`#${tr_id} #proBuildStatus`).html("回滚终止");
                                $(`#${tr_id} #startOneDeploy`).show();
                                $(`#${tr_id} #select-nodes-deploy`).show();
                                $(`#${tr_id} #stopDeploy`).hide();
                            } else if (received_msg[i] === 'start_deploy') {
                                realPoints++;
                                i += 1;
                                element.progress(`proOneDeploy${num[realPoints]}`, '40%');
                                html3 += "IP" + realPoints + "：\n" +
                                    "<a href='" + received_msg[i] + "' target='_blank' class='btn btn-link btn-sm'>去Jenkins上看</a><br>";
                                $(`#${tr_id} #jenkinsConsole`).html(html3);
                                $(`#${tr_id} #stopDeploy`).show();
                            } else if (received_msg[i].length === 10) {
                                element.progress(`proOneDeploy${num[realPoints]}`, '100%');
                                $(`#${tr_id} #stopDeploy`).hide();
                            } else if (received_msg[i] === 'deploy_failed') {
                                i += 1;
                                html2 += "<div class=\"sufee-alert alert with-close alert-danger alert-dismissible\">\n" +
                                    "<span class=\"badge badge-pill badge-primary\">Failure</span>\n" +
                                    received_msg[i] +
                                    "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                    "aria-label=\"Close\">\n" +
                                    "<span aria-hidden=\"true\">&times;</span>\n" +
                                    "</button>\n" +
                                    "</div>";
                                $('#buildMessage').html(html2);
                                $(`#proBuildProgress${num[realPoints]}`).addClass("layui-bg-red");
                                $(`#${tr_id} #proBuildStatus`).html("回滚失败")
                                $(`#${tr_id} #startOneDeploy`).show();
                                $(`#${tr_id} #select-nodes-deploy`).show();
                                $(`#${tr_id} #stopDeploy`).hide();
                            } else if (received_msg[i] === 'deploy_success') {
                                i += 1;
                                html2 += "<div class=\"sufee-alert alert with-close alert-success alert-dismissible\">\n" +
                                    "<span class=\"badge badge-pill badge-primary\">Success</span>\n" +
                                    received_msg[i] +
                                    "<button type=\"button\" class=\"close\" data-dismiss=\"alert\"\n" +
                                    "aria-label=\"Close\">\n" +
                                    "<span aria-hidden=\"true\">&times;</span>\n" +
                                    "</button>\n" +
                                    "</div>";
                                $('#buildMessage').html(html2);
                                $(`#${tr_id} #proBuildStatus`).html("回滚成功");
                                $(`#${tr_id} #startOneDeploy`).show();
                                $(`#${tr_id} #select-nodes-deploy`).show();
                                $(`#${tr_id} #stopDeploy`).hide();
                            }
                        }
                        $(`#${step} #nextBtn`).hide();
                    }
                };

                ws.onclose = function () {
                    // 关闭 websocket
                    console.log("连接已关闭...");
                };
            }

            else {
                // 浏览器不支持 WebSocket
                console.alert("您的浏览器不支持 WebSocket!");
            }
        }

    }
});
//生产验收
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    $("body").on("click", ".checkSuccess", checkSuccess);

    function checkSuccess() {
        var step = $(this).parent().parent().attr('id');
        var remark = $(this).siblings("#remark").val();
        var sequenceId = $(this).attr("id");
        var combination = remark + '-' + sequenceId;
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(step, combination);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(step, combination) {

            if ("WebSocket" in window) {
                console.log("您的浏览器支持 WebSocket!");

                // 打开一个 web socket
                var ws = new WebSocket("ws:" + window.location.host + "/ws_checkSuccess");

                ws.onopen = function () {
                    ws.send(combination);
                    console.log("数据已发送...");
                };

                ws.onmessage = function (evt) {
                    var received_msg = JSON.parse(evt.data);
                    console.log("数据已接收...");

                    if (received_msg[0] === 'no_role') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "你没有生产验收的权限！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                    } else {
                        $(`#${step} .checkSuccess`).hide();
                        $(`#${step} #remark`).hide();
                        $(`#${step} .createTag`).show();
                        $(`#${step} #createTagText`).text("tag创建中，请等待...");
                        $(`#${step} #createTagProgressLine`).width(5 + '%').text('5%');
                        $(`#${step} #p1`).removeClass("fade").html(received_msg[0]);
                        var html = "";
                        var sumPoints = received_msg[1];
                        var realPoints = 0;
                        for (var i = 2; i < received_msg.length; i++) {
                            realPoints++;
                            $('#createTagText').text("正在创建tag，共" + sumPoints + "个，完成第" + realPoints + "个");
                            var widthTemp = (realPoints / sumPoints) * 100;
                            $('#createTagProgressLine').width(widthTemp + '%').text(widthTemp + '%');
                            html += "<br>" + received_msg[i];
                        }
                        $(`.createTagResult`).html(html);
                        if (realPoints === sumPoints) {
                            $(`#${step} #nextBtn`).show();
                        }
                    }
                };

                ws.onclose = function () {
                    // 关闭 websocket
                    console.log("连接已关闭...");
                };
            }

            else {
                // 浏览器不支持 WebSocket
                console.alert("您的浏览器不支持 WebSocket!");
            }
        }

    }
});