from django.core.mail import EmailMultiAlternatives  # 导入邮件模块
from django.template import loader


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
