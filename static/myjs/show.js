// 面板
layui.use('element', function () {
    var $ = layui.jquery
        , element = layui.element; //Tab的切换功能，切换事件监听等，需要依赖element模块

    //触发事件
    var active = {
        tabAdd: function () {
            //新增一个Tab项
            element.tabAdd('demo', {
                title: '新选项' + (Math.random() * 1000 | 0) //用于演示
                , content: '内容' + (Math.random() * 1000 | 0)
                , id: new Date().getTime() //实际使用一般是规定好的id，这里以时间戳模拟下
            })
        }
        , tabDelete: function (othis) {
            //删除指定Tab项
            element.tabDelete('demo', '44'); //删除：“商品管理”


            othis.addClass('layui-btn-disabled');
        }
        , tabChange: function () {
            //切换到指定Tab项
            element.tabChange('demo', '22'); //切换到：用户管理
        }
    };

    $('.site-demo-active').on('click', function () {
        var othis = $(this), type = othis.data('type');
        active[type] ? active[type].call(this, othis) : '';
    });

    //Hash地址的定位
    var layid = location.hash.replace(/^#test=/, '');
    element.tabChange('test', layid);

    element.on('tab(test)', function (elem) {
        location.hash = 'test=' + $(this).attr('lay-id');
    });
});

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

//任务执行
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery
        , element = layui.element, layer = layui.layer;

    //触发事件
    var active = {
        loading: function (othis) {
            var DISABLED = 'layui-btn-disabled';
            if (othis.hasClass(DISABLED)) return;
            //模拟loading
            var n = 0, timer = setInterval(function () {
                n = n + Math.random() * 10 | 0;
                if (n > 95) {
                    n = 95;
                    clearInterval(timer);
                    othis.removeClass(DISABLED);
                }
                element.progress('runtask', n + '%');
            }, 300 + Math.random() * 1000);

            // 没完成前设置为50%
            // element.progress('runtask', '40%');

            othis.addClass(DISABLED);
        }
    };

    $("body").on("click", ".runTask", function () {
        var othis = $(this), type = $(this).data('type');
        active[type] ? active[type].call(this, othis) : '';
        var task = {};
        var id = getQueryVariable("tid")
        // console.log(id);
        task['id'] = id;

        $.ajax({
            url: '/ajax_RunBuild',
            type: 'POST',
            data: task,

            success: function (arg) {
                // var flag = arg
                if (arg === "done") {
                    element.progress('runtask', '100%');
                    // console.log(arg);
                }
                else {
                    element.progress('runtask', '0%');
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '发布异常'
                        , id: 'layerDemo' + type //防止重复弹出
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
//任务回滚
layui.use(['element', 'layer'], function () {
    var $ = layui.jquery
        , element = layui.element, layer = layui.layer;

    //触发事件
    var active = {
        loading: function (othis) {
            var DISABLED = 'layui-btn-disabled';
            if (othis.hasClass(DISABLED)) return;
            //模拟loading
            var n = 0, timer = setInterval(function () {
                n = n + Math.random() * 10 | 0;
                if (n > 95) {
                    n = 95;
                    clearInterval(timer);
                    othis.removeClass(DISABLED);
                }
                element.progress('rollback', n + '%');
            }, 300 + Math.random() * 1000);
            // 没完成前设置为50%
            // element.progress('rollback', '50%');

            othis.addClass(DISABLED);
        }
    };

    $("body").on("click", ".rollback", function () {
        var othis = $(this), type = $(this).data('type');
        active[type] ? active[type].call(this, othis) : '';
        var task = {};
        var id = getQueryVariable("tid")
        // console.log(id);
        task['id'] = id;

        $.ajax({
            url: '/ajax_RollBack',
            type: 'POST',
            data: task,

            success: function (arg) {
                // console.log(arg);
                // xx = typeof arg;
                // console.log(xx);
                if (arg === "done") {
                    element.progress('rollback', '100%');
                    // console.log(arg);
                }
                else {
                    element.progress('rollback', '0%');
                    layer.open({
                        type: 1
                        , offset: type //具体配置参考：http://www.layui.com/doc/modules/layer.html#offset
                        , title: '回滚异常'
                        , id: 'layerDemo' + type //防止重复弹出
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
