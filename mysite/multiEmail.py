from django.core.mail import EmailMultiAlternatives  # 导入邮件模块
from django.template import loader


# 预发申请邮件
def email_createPlan(project_plans, mail_from, mail_to, mail_cc):
    title = "【预发申请】：%s" % project_plans[0].plan.name
    context = {
        'plan': project_plans[0].plan,
        'project_plans': project_plans,
        'url': 'http://127.0.0.1:8000/planDetail?pid=%s' % project_plans[0].plan.id
    }

    template = loader.get_template("email_createPlan.html")
    html_content = template.render(context)
    msg = EmailMultiAlternatives(title, html_content, mail_from, mail_to, mail_cc, headers={"Cc": ",".join(mail_cc)})
    msg.attach_alternative(html_content, "text/html")
    msg.send()


# 预发验收邮件
def email_uatCheck(plan, mail_from, mail_to, mail_cc):
    title = "【预发验收】：%s" % plan.name
    context = {
        'plan': plan,
        'url': 'http://127.0.0.1:8000/uatDetail?pid=%s' % plan.id
    }

    template = loader.get_template("email_uatCheck.html")
    html_content = template.render(context)
    msg = EmailMultiAlternatives(title, html_content, mail_from, mail_to, mail_cc, headers={"Cc": ",".join(mail_cc)})
    msg.attach_alternative(html_content, "text/html")
    msg.send()


# 上线申请邮件
def email_createTask(plan, sequences, mail_from, mail_to, mail_cc):
    title = "【上线申请】：%s" % plan.name
    context = {
        'plan': plan,
        'sequences': sequences,
        'url': 'http://127.0.0.1:8000/planDetail?pid=%s' % plan.id
    }

    template = loader.get_template("email_createTask.html")
    html_content = template.render(context)
    msg = EmailMultiAlternatives(title, html_content, mail_from, mail_to, mail_cc, headers={"Cc": ",".join(mail_cc)})
    msg.attach_alternative(html_content, "text/html")
    msg.send()


# 线上验收邮件
def email_proCheck(task, mail_from, mail_to, mail_cc):
    title = "【上线验收】：%s" % task.plan.name
    context = {
        'task': task,
        'plan': task.plan,
        'url': 'http://127.0.0.1:8000/taskDetail?tid=%s' % task.id
    }

    template = loader.get_template("email_proCheck.html")
    html_content = template.render(context)
    msg = EmailMultiAlternatives(title, html_content, mail_from, mail_to, mail_cc, headers={"Cc": ",".join(mail_cc)})
    msg.attach_alternative(html_content, "text/html")
    msg.send()
