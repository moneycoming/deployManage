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
            if (data[0] === 'uat') {
                $(`.uatBuildResult`).html(html);
            } else {
                $(`.proBuildResult`).html(html);
            }

        },
        error: function () {
            console.log('error');
        }
    })
}

//任务执行
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    var type = $(this).data('type');
    $("body").on("click", ".startDeploy", startDeploy);

    function startDeploy() {
        var taskId = getQueryVariable("tid");
        $('#proDeployText').text("发布进行中，请等待...");
        $('.proDeployProgress').removeClass('fade');
        $('#proBuildProgress').width(5 + '%').text('5%');
        $('.startDeploy').addClass('fade');
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
                            html += "<a href='http://127.0.0.1:8000/single_console_opt/"
                                + received_msg[i] + "' target='_blank'>查看控制台信息</a>"
                        } else if (received_msg[i] === 'deploy_failed') {
                            $('.restartDeploy').removeClass('fade');
                            $('.continueDeploy').removeClass('fade');
                            $('.rollbackOne').removeClass('fade');
                            $('.rollbackAll').removeClass('fade');
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
                        }
                        else {
                            html += "<pre>" + received_msg[i] + "</pre>"
                        }
                    }
                    $(`.proBuildResult`).html(html);
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
});
//重新发布
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    var type = $(this).data('type');
    $("body").on("click", ".restartDeploy", restartDeploy);

    function restartDeploy() {
        var taskId = getQueryVariable("tid");
        $('#proDeployText').text("发布进行中，请等待...");
        $('.proDeployProgress').removeClass('fade');
        $('#proBuildProgress').width('5%').text('5%');
        $('.restartDeploy').addClass('fade');
        $('.continueDeploy').addClass('fade');
        $('#proConsoleOpt').removeClass('fade');
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
                            html += "<a href='http://127.0.0.1:8000/single_console_opt/"
                                + received_msg[i] + "' target='_blank'>查看控制台信息</a>"
                        } else if (received_msg[i] === 'deploy_failed') {
                            $('.restartDeploy').removeClass('fade');
                            $('.continueDeploy').removeClass('fade');
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
                        }
                        else {
                            html += "<pre>" + received_msg[i] + "</pre>"
                        }
                    }
                    $(`.proBuildResult`).html(html);
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
});
//跳过继续下一个发布
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    var type = $(this).data('type');
    $("body").on("click", ".continueDeploy", continueDeploy);

    function continueDeploy() {
        var taskId = getQueryVariable("tid");
        $('#proDeployText').text("发布进行中，请等待...");
        $('.proDeployProgress').removeClass('fade');
        $('#proBuildProgress').width('5%').text('5%');
        $('.restartDeploy').addClass('fade');
        $('.continueDeploy').addClass('fade');
        $('#proConsoleOpt').removeClass('fade');
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
                    $('#proDeployText').addClass('fade');
                    $('.proDeployProgress').addClass('fade');
                    $('#proConsoleOpt').addClass('fade');
                    $('.proBuildResult').addClass('fade');
                    $('.restartDeploy').removeClass('fade');
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
                            html += "<a href='http://127.0.0.1:8000/single_console_opt/"
                                + received_msg[i] + "' target='_blank'>查看控制台信息</a>"
                        } else if (received_msg[i] === 'deploy_failed') {
                            $('.restartDeploy').removeClass('fade');
                            $('.continueDeploy').removeClass('fade');
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
                        }
                        else {
                            html += "<pre>" + received_msg[i] + "</pre>"
                        }
                    }
                    $(`.proBuildResult`).html(html);
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
});
//回滚单个节点
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    var type = $(this).data('type');
    $("body").on("click", ".rollbackOne", rollbackOne);

    function rollbackOne() {
        var taskId = getQueryVariable("tid");
        $('#proDeployText').text("回滚进行中，请等待...");
        $('.proDeployProgress').removeClass('fade');
        $('#proBuildProgress').width(5 + '%').text('5%');
        $('.restartDeploy').addClass('fade');
        $('.continueDeploy').addClass('fade');
        $('.rollbackOne').addClass('fade');
        $('.rollbackAll').addClass('fade');
        $('#proConsoleOpt').removeClass('fade');
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
                            html += "<a href='http://127.0.0.1:8000/single_console_opt/"
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
                            $('.restartDeploy').removeClass('fade');
                            $('.continueDeploy').removeClass('fade');
                            $('.rollbackOne').removeClass('fade');
                            $('.rollbackAll').removeClass('fade');
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
                    $(`.proBuildResult`).html(html);
                    if (realPoints === sumPoints) {
                        $('#proDeployText').text("回滚完成");
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
//回滚所有节点
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    var type = $(this).data('type');
    $("body").on("click", ".rollbackAll", rollbackAll);

    function rollbackAll() {
        var taskId = getQueryVariable("tid");
        $('#proDeployText').text("回滚进行中，请等待...");
        $('.proDeployProgress').removeClass('fade');
        $('#proBuildProgress').width(5 + '%').text('5%');
        $('.restartDeploy').addClass('fade');
        $('.continueDeploy').addClass('fade');
        $('.rollbackOne').addClass('fade');
        $('.rollbackAll').addClass('fade');
        $('#proConsoleOpt').removeClass('fade');
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
                        if (received_msg[i].length === 10) {
                            realPoints++;
                            $('#proDeployText').text("回滚进行中，共" + sumPoints + "个，完成第" + realPoints + "个");
                            var widthTemp = (realPoints / sumPoints) * 100;
                            $('#proBuildProgress').width(widthTemp + '%').text(widthTemp + '%');
                            html += "<a href='http://127.0.0.1:8000/single_console_opt/"
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
                                , content: '<div style="padding: 20px 100px;">' + "所有节点都已回滚！" + '</div>'
                                , btn: '关闭'
                                , btnAlign: 'c' //按钮居中
                                , area: '500px;'
                                , shade: 0.5 //不显示遮罩
                                , yes: function () {
                                    layer.closeAll();
                                }
                            });
                            $('.restartDeploy').removeClass('fade');
                            $('.continueDeploy').removeClass('fade');
                        }
                        else {
                            html += "<pre>" + received_msg[i] + "</pre>"
                        }
                    }
                    $(`.proBuildResult`).html(html);
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
                if (arg[1].length > 0) {
                    $('#createUatBranchText').html("分支创建完成");
                    $(`#uatBranch`).html(arg[1]);
                }
            },
            error: function () {
                console.log("error");
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
                        , content: '<div style="padding: 20px 100px;">' + "你没有合并分支的权限！" + '</div>'
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
                } else {
                    for (var i = 0; i < received_msg.length; i++) {
                        console.log(received_msg[i]);
                        if (received_msg[i] === 'success') {
                            html += "<pre>" + received_msg[i + 1] + "</pre>";
                            html += "<a href='http://127.0.0.1:8000/single_console_opt/"
                                + received_msg[i + 2] + "' target='_blank'>查看控制台信息</a>";
                        } else if (received_msg[i] === 'fail') {
                            html += "<pre>" + received_msg[i + 1] + "</pre>";
                            html += "<a href='http://127.0.0.1:8000/single_console_opt/"
                                + received_msg[i + 2] + "' target='_blank'>查看控制台信息</a>";
                        } else if (received_msg[i] === 'deploy'){
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
        var taskId = getQueryVariable("tid");
        var str = $(this).text();
        $(this).text(str);
        var postData = {};
        var sequenceId = $(this).attr("id");
        var remark = $(this).parent().children("#remark").val();
        postData['id'] = sequenceId;
        postData['implemented'] = 1;
        postData['remark'] = remark;
        postData['taskId'] = taskId;

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
//任务验收通过
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;

    $("body").on("click", ".checkSuccess", function () {
        var step = $(this).parent().attr('id');
        var postData = {};
        var taskId = getQueryVariable("tid");
        var remark = $(this).siblings("#remark").val();
        postData['taskId'] = taskId;
        postData['remark'] = remark;
        $('.checkSuccess').hide();
        $('.checkFail').hide();

        $.ajax({
            url: '/ajax_checkSuccess',
            type: 'POST',
            data: postData,

            success: function (arg) {
                if (arg === "no_role") {
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
                    layer.open({
                        type: 1
                        , title: '合并结果'
                        , content: '<div style="padding: 20px 100px;">' + "验收通过！" + '</div>'
                        , btn: '关闭'
                        , btnAlign: 'c' //按钮居中
                        , area: '500px;'
                        , shade: 0.5 //不显示遮罩
                        , yes: function () {
                            layer.closeAll();
                        }
                    });
                    $(`#${step} .checkSuccess`).hide();
                    $(`#${step} #remark`).hide();
                    $(`#${step} #p1`).removeClass("fade").html(arg);
                }
            },
            error: function () {
                console.log("error");
            }
        })
    });
});
//合并代码
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery, layer = layui.layer;
    var type = $(this).data('type');
    $("body").on("click", ".startCodeMerge", startCodeMerge);

    function startCodeMerge() {
        var taskId = getQueryVariable("tid");
        $('#codeMergeText').text("代码合并进行中，请等待...");
        $('.codeMergeProgress').removeClass('fade');
        $('#codeMerge').width(5 + '%').text('5%');
        $('#codeMergeOpt').removeClass('fade');
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
                        if (received_msg[i] === 'ok') {
                            realPoints++;
                            $('#codeMergeText').text("发布进行中，共" + sumPoints + "个，完成第" + realPoints + "个");
                            var widthTemp = (realPoints / sumPoints) * 100;
                            $('#codeMerge').width(widthTemp + '%').text(widthTemp + '%');
                            html += "<br>" + received_msg[i + 1]
                        } else if (received_msg[i] === 'conflict') {
                            realPoints++;
                            $('#codeMergeText').text("发布进行中，共" + sumPoints + "个，完成第" + realPoints + "个");
                            var widthTemp2 = (realPoints / sumPoints) * 100;
                            $('#codeMerge').width(widthTemp2 + '%').text(widthTemp2 + '%');
                            html += "<br>" + received_msg[i + 1]
                        }
                        else if (received_msg[i] === 'success') {
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
});
