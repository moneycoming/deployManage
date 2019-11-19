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

//生产项目部署
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    $("body").on("click", ".startDeploy", startDeploy);

    function startDeploy() {
        var type = $(this).data('type');
        var step = $(this).parent().parent().parent().parent().parent().attr('id');
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(step, type);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(step, type) {
            var taskId = getQueryVariable("tid");
            $('#proDeployText').text("发布进行中，请等待...");
            $('.proDeployProgress').removeClass('fade');
            $('#proBuildProgress').width(5 + '%').text('5%');
            $('.startDeploy').hide();
            $('#proConsoleOpt').removeClass('fade');
            if ("WebSocket" in window) {
                console.log("您的浏览器支持 WebSocket!");

                // 打开一个 web socket
                var ws = new WebSocket("ws:" + window.location.host + "/ws_startDeploy");

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
                            , content: '<div style="padding: 20px 100px;">' + "你没有发布的权限！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $('#proDeployText').hide();
                        $('.proDeployProgress').hide();
                        $('#proConsoleOpt').hide();
                    } else {
                        var html = "";
                        var html2 = "";
                        var sumPoints = received_msg[0];
                        var realPoints = 0;
                        for (var i = 1; i < received_msg.length; i++) {
                            if (received_msg[i].length === 10) {
                                realPoints++;
                                $('#proDeployText').text("发布进行中，共" + sumPoints + "个，完成第" + realPoints + "个");
                                var widthTemp = (realPoints / sumPoints) * 100;
                                $('#proBuildProgress').width(widthTemp + '%').text(widthTemp + '%');
                                html += "<a href='http://" + window.location.host + "/single_console_opt/"
                                    + received_msg[i] + "' target='_blank'>查看控制台信息</a>"
                            }else if (received_msg[i] === 'url') {
                                i += 1;
                                html += "<br><a href='" + received_msg[i] + "' target='_blank'>" + received_msg[i] + "</a>"
                            }else if (received_msg[i] === 'deploy_failed') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + "发布失败！" + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                                $('#proBuildProgress').removeClass("bg-success").addClass("bg-danger");
                                html2 = "<div class=\"btn-group\">\n" +
                                    "    <button type=\"button\"\n" +
                                    "        class=\"layui-btn layui-btn-primary restartDeploy\">重新发布\n" +
                                    "    </button>\n" +
                                    "    <button type=\"button\"\n" +
                                    "        class=\"layui-btn layui-btn-primary continueDeploy\">跳过继续下一个发布\n" +
                                    "    </button>\n" +
                                    "    <button type=\"button\"\n" +
                                    "        class=\"layui-btn layui-btn-primary rollbackOne\">回滚当前项目\n" +
                                    "    </button>\n" +
                                    "     <button type=\"button\"\n" +
                                    "        class=\"layui-btn layui-btn-primary rollbackAll\">回滚所有项目\n" +
                                    "    </button>\n" +
                                    "</div>";
                            } else if (received_msg[i] === 'no_reversion') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + "项目没有发布版本！" + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                            } else if (received_msg[i] === 'deploy_success') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + "发布完成！" + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                                $(`#${step} #nextBtn`).show();
                            }
                            else {
                                html += "<pre>" + received_msg[i] + "</pre>"
                            }
                        }
                        $(`.proBuildResult`).html(html);
                        $('#proDeployBarList').html(html2);
                        if (realPoints === sumPoints) {
                            $('#proDeployText').text("发布完成");
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
//重新发布
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    $("body").on("click", ".restartDeploy", restartDeploy);

    function restartDeploy() {
        var step = $(this).parent().parent().parent().parent().parent().parent().parent().attr('id');
        var type = $(this).data('type');
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(step, type);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(step, type) {
            var taskId = getQueryVariable("tid");
            $('#proDeployText').text("发布进行中，请等待...");
            $('.proDeployProgress').removeClass('fade');
            $('#proBuildProgress').width('5%').text('5%').removeClass("bg-danger").addClass("bg-success");
            $('#proConsoleOpt').removeClass('fade');
            $('.restartDeploy').hide();
            $('.continueDeploy').hide();
            $('.rollbackOne').hide();
            $('.rollbackAll').hide();
            $(`.proBuildResult`).hide();

            if ("WebSocket" in window) {
                console.log("您的浏览器支持 WebSocket!");

                // 打开一个 web socket
                var ws = new WebSocket("ws:" + window.location.host + "/ws_restartDeploy");

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
                            , content: '<div style="padding: 20px 100px;">' + "你没有发布的权限！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $('#proDeployText').addClass('fade');
                        $('.proDeployProgress').addClass('fade');
                        $('#proConsoleOpt').addClass('fade');
                    } else {
                        var html = "";
                        var sumPoints = received_msg[0];
                        var realPoints = 0;
                        for (var i = 1; i < received_msg.length; i++) {
                            if (received_msg[i].length === 10) {
                                realPoints++;
                                $('#proDeployText').text("发布进行中，共" + sumPoints + "个，完成第" + realPoints + "个");
                                var widthTemp = (realPoints / sumPoints) * 100;
                                $('#proBuildProgress').width(widthTemp + '%').text(widthTemp + '%');
                                html += "<a href='http://" + window.location.host + "/single_console_opt/"
                                    + received_msg[i] + "' target='_blank'>查看控制台信息</a>"
                            } else if (received_msg[i] === 'deploy_failed') {
                                $('.restartDeploy').show();
                                $('.continueDeploy').show();
                                $('.rollbackOne').show();
                                $('.rollbackAll').show();
                                $('#proBuildProgress').removeClass("bg-success").addClass("bg-danger");
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + "发布失败！" + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                            } else if (received_msg[i] === 'no_reversion') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + "项目没有发布版本！" + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                            } else if (received_msg[i] === 'deploy_success') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + "发布完成！" + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                                $(`#${step} #nextBtn`).show();
                            }
                            else {
                                html += "<pre>" + received_msg[i] + "</pre>"
                            }
                        }
                        $(`.proBuildResult`).show().html(html);
                        if (realPoints === sumPoints) {
                            $('#proDeployText').text("发布完成");
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
//跳过继续下一个发布
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    $("body").on("click", ".continueDeploy", continueDeploy);

    function continueDeploy() {
        var type = $(this).data('type');
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
            $('#proDeployText').text("发布进行中，请等待...");
            $('.proDeployProgress').removeClass('fade');
            $('#proBuildProgress').width('5%').text('5%').removeClass("bg-danger").addClass("bg-success");
            $('#proConsoleOpt').removeClass('fade');
            $('.restartDeploy').hide();
            $('.continueDeploy').hide();
            $('.rollbackOne').hide();
            $('.rollbackAll').hide();
            $(`.proBuildResult`).hide();

            if ("WebSocket" in window) {
                console.log("您的浏览器支持 WebSocket!");

                // 打开一个 web socket
                var ws = new WebSocket("ws:" + window.location.host + "/ws_continueDeploy");

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
                            , content: '<div style="padding: 20px 100px;">' + "你没有发布的权限！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $('#proDeployText').addClass('fade');
                        $('.proDeployProgress').addClass('fade');
                        $('#proConsoleOpt').addClass('fade');
                    } else if (received_msg[0] === 'last_one') {
                        layer.open({
                            type: 1
                            , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                            , title: '发布结果'
                            , id: 'layerDemo' + type//防止重复弹出
                            , content: '<div style="padding: 20px 100px;">' + "已经是最后一个项目，无法跳过！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $('.restartDeploy').show();
                        $('.rollbackOne').show();
                        $('.rollbackAll').show();
                    }
                    else {
                        var html = "";
                        var sumPoints = received_msg[0];
                        var realPoints = 0;
                        for (var i = 1; i < received_msg.length; i++) {
                            if (received_msg[i].length === 10) {
                                realPoints++;
                                $('#proDeployText').text("发布进行中，共" + sumPoints + "个，完成第" + realPoints + "个");
                                var widthTemp = (realPoints / sumPoints) * 100;
                                $('#proBuildProgress').width(widthTemp + '%').text(widthTemp + '%');
                                html += "<a href='http://" + window.location.host + "/single_console_opt/"
                                    + received_msg[i] + "' target='_blank'>查看控制台信息</a>"
                            } else if (received_msg[i] === 'deploy_failed') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + "发布失败！" + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                                $('#proBuildProgress').removeClass("bg-success").addClass("bg-danger");
                                $('.restartDeploy').show();
                                $('.continueDeploy').show();
                                $('.rollbackOne').show();
                                $('.rollbackAll').show();
                            } else if (received_msg[i] === 'no_reversion') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + "项目没有发布版本！" + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                                $('.restartDeploy').show();
                            } else if (received_msg[i] === 'deploy_success') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + "发布完成！" + '</div>'
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
                                html += "<pre>" + received_msg[i] + "</pre>"
                            }
                        }
                        $(`.proBuildResult`).show().html(html);
                        if (realPoints === sumPoints) {
                            $('#proDeployText').text("发布完成");
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
//回滚单个节点
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    $("body").on("click", ".rollbackOne", rollbackOne);

    function rollbackOne() {
        var type = $(this).data('type');
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(type);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(type) {
            var taskId = getQueryVariable("tid");
            $('#proDeployText').text("回滚进行中，请等待...");
            $('.proDeployProgress').removeClass('fade');
            $('#proBuildProgress').width(5 + '%').text('5%').removeClass("bg-danger").addClass("bg-success");
            $('#proConsoleOpt').removeClass('fade');
            $('.restartDeploy').hide();
            $('.continueDeploy').hide();
            $('.rollbackOne').hide();
            $('.rollbackAll').hide();
            $(`.proBuildResult`).hide();

            if ("WebSocket" in window) {
                console.log("您的浏览器支持 WebSocket!");

                // 打开一个 web socket
                var ws = new WebSocket("ws:" + window.location.host + "/ws_rollbackOne");

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
                            , content: '<div style="padding: 20px 100px;">' + "你没有发布的权限！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $('#proDeployText').addClass('fade');
                        $('.proDeployProgress').addClass('fade');
                        $('#proConsoleOpt').addClass('fade');
                    } else {
                        var html = "";
                        var sumPoints = received_msg[0];
                        var realPoints = 0;
                        for (var i = 1; i < received_msg.length; i++) {
                            if (received_msg[i].length === 10) {
                                realPoints++;
                                $('#proDeployText').text("回滚进行中，共" + sumPoints + "个，完成第" + realPoints + "个");
                                var widthTemp = (realPoints / sumPoints) * 100;
                                $('#proBuildProgress').width(widthTemp + '%').text(widthTemp + '%');
                                html += "<a href='http://" + window.location.host + "/single_console_opt/"
                                    + received_msg[i] + "' target='_blank'>查看控制台信息</a>";
                            } else if (received_msg[i] === 'no_reversion') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + "已是最初版本，无法回滚！" + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                                $('#proDeployText').addClass('fade');
                                $('.proDeployProgress').addClass('fade');
                                $('.restartDeploy').show();
                                $('.continueDeploy').show();
                                $('.rollbackOne').show();
                                $('.rollbackAll').show();
                            } else if (received_msg[i] === 'deploy_success') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + "所有节点都已回滚" + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                                $('.restartDeploy').show();
                                $('.continueDeploy').show();
                            } else if (received_msg[i] === 'deploy_failed') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + received_msg[i - 2] + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                                $('#proBuildProgress').removeClass("bg-success").addClass("bg-danger");
                                $('.restartDeploy').show();
                                $('.continueDeploy').show();
                                $('.rollbackOne').show();
                                $('.rollbackAll').show();
                            }
                            else {
                                html += "<pre>" + received_msg[i] + "</pre>"
                            }
                        }
                        $(`.proBuildResult`).show().html(html);
                        if (realPoints === sumPoints) {
                            $('#proDeployText').text("回滚结束");
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
//回滚所有节点
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    $("body").on("click", ".rollbackAll", rollbackAll);

    function rollbackAll() {
        var type = $(this).data('type');
        layer.confirm('确认执行？', {
            btn: ['确认', '取消'] //按钮
        }, function () {
            ok(type);
            layer.closeAll();
        }, function () {
            console.log('已取消');
        });

        function ok(type) {
            var taskId = getQueryVariable("tid");
            $('#proDeployText').text("回滚进行中，请等待...");
            $('.proDeployProgress').removeClass('fade');
            $('#proBuildProgress').width(5 + '%').text('5%').removeClass("bg-danger").addClass("bg-success");
            $('#proConsoleOpt').removeClass('fade');
            $('.restartDeploy').hide();
            $('.continueDeploy').hide();
            $('.rollbackOne').hide();
            $('.rollbackAll').hide();
            $(`.proBuildResult`).hide();

            if ("WebSocket" in window) {
                console.log("您的浏览器支持 WebSocket!");

                // 打开一个 web socket
                var ws = new WebSocket("ws:" + window.location.host + "/ws_rollbackAll");

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
                            , content: '<div style="padding: 20px 100px;">' + "你没有发布的权限！" + '</div>'
                            , btn: '关闭'
                            , btnAlign: 'c' //按钮居中
                            , area: '500px;'
                            , shade: 0.5 //不显示遮罩
                            , yes: function () {
                                layer.closeAll();
                            }
                        });
                        $('#proDeployText').addClass('fade');
                        $('.proDeployProgress').addClass('fade');
                        $('#proConsoleOpt').addClass('fade');
                    } else {
                        var html = "";
                        var sumPoints = received_msg[0];
                        var realPoints = 0;
                        for (var i = 1; i < received_msg.length; i++) {
                            console.log(received_msg[i]);
                            if (received_msg[i].length === 10) {
                                realPoints++;
                                $('#proDeployText').text("回滚进行中，共" + sumPoints + "个，完成第" + realPoints + "个");
                                var widthTemp = (realPoints / sumPoints) * 100;
                                $('#proBuildProgress').width(widthTemp + '%').text(widthTemp + '%');
                                html += "<a href='http://" + window.location.host + "/single_console_opt/"
                                    + received_msg[i] + "' target='_blank'>查看控制台信息</a>"
                            } else if (received_msg[i] === 'no_reversion') {
                                realPoints += received_msg[i + 1];
                                $('#proDeployText').text("回滚进行中，共" + sumPoints + "个，完成第" + realPoints + "个");
                                var widthTemp2 = (realPoints / sumPoints) * 100;
                                $('#proBuildProgress').width(widthTemp2 + '%').text(widthTemp2 + '%');
                            } else if (received_msg[i] === 'deploy_success') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + "所有项目回滚成功！" + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                                $('.startDeploy').show();
                            } else if (received_msg[i] === 'deploy_failed') {
                                layer.open({
                                    type: 1
                                    , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                                    , title: '发布结果'
                                    , id: 'layerDemo' + type//防止重复弹出
                                    , content: '<div style="padding: 20px 100px;">' + received_msg[i - 2] + '</div>'
                                    , btn: '关闭'
                                    , btnAlign: 'c' //按钮居中
                                    , area: '500px;'
                                    , shade: 0.5 //不显示遮罩
                                    , yes: function () {
                                        layer.closeAll();
                                    }
                                });
                                $('#proBuildProgress').removeClass("bg-success").addClass("bg-danger");
                                $('.restartDeploy').show();
                                $('.continueDeploy').show();
                                $('.rollbackOne').show();
                                $('.rollbackAll').show();
                            }
                            else {
                                html += "<pre>" + received_msg[i] + "</pre>"
                            }
                        }
                        $(`.proBuildResult`).show().html(html);
                        if (realPoints === sumPoints) {
                            $('#proDeployText').text("回滚完成");
                            $('.restartDeploy').removeClass('fade');
                            $('.continueDeploy').removeClass('fade');
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
                    layer.open({
                        type: 1
                        , title: '结果'
                        , content: '<div style="padding: 20px 100px;">' + data.res + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                    if (data.result === 1) {
                        $('#createUatBranchText').html("分支创建完成");
                        $(`#uatBranch`).html(data.uatBranch);
                    } else {
                        $('#createUatBranchText').html("分支创建失败");
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
    var $ = layui.jquery, layer = layui.layer;
    $("body").on("click", ".uatBuild", uatBuild);

    function uatBuild() {
        $('.uatBuild').hide();
        $('#uatConsoleOpt').removeClass('fade');
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
                // ws.send(planId);
                console.log("数据已发送...");
            };

            ws.onmessage = function (evt) {
                var received_msg = JSON.parse(evt.data);
                var html = "";
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
                    $('#uatConsoleOpt').hide();
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
                } else {
                    for (var i = 0; i < received_msg.length; i++) {
                        console.log(received_msg[i]);
                        if (received_msg[i] === 'success') {
                            html += "<pre>" + received_msg[i + 1] + "</pre>";
                            html += "<a href='http://" + window.location.host + "/single_console_opt/"
                                + received_msg[i + 2] + "' target='_blank'>查看控制台信息</a>";
                        } else if (received_msg[i] === 'fail') {
                            html += "<pre>" + received_msg[i + 1] + "</pre>";
                            html += "<a href='http://" + window.location.host + "/single_console_opt/"
                                + received_msg[i + 2] + "' target='_blank'>查看控制台信息</a>";
                        } else if (received_msg[i] === 'deploy') {
                            html += "<pre>" + received_msg[i + 1] + "</pre>";
                        }
                    }
                }
                $(`.uatBuildResult`).html(html);
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
//任务验收通过
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", ".checkSuccess", function () {
        var step = $(this).parent().parent().attr('id');
        var remark = $(this).siblings("#remark").val();
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
            var postData = {};
            postData['remark'] = remark;
            postData['sequenceId'] = sequenceId;
            $('.checkSuccess').hide();

            $.ajax({
                url: '/ajax_checkSuccess',
                type: 'POST',
                data: postData,

                success: function (data) {
                    if (data.role === 0) {
                        layer.open({
                            type: 1
                            , title: '警告'
                            , content: '<div style="padding: 20px 100px;">' + "你没有验收任务的权限" + '</div>'
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
                        $(`#${step} #p1`).removeClass("fade").html(data.remark);
                        $(`#${step} #nextBtn`).show();
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
                        console.log(sumPoints);
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