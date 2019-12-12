import subprocess
# now = datetime.datetime.now()
# t = now.strftime('%Y%m%d%I%M')
# print(t)

token = "1159ae85fefbbc674c5493822c78b114b5"
url = "http://fabu:1159ae85fefbbc674c5493822c78b114b5@jenkinspro.bestjlb.cn/job/HD-institutionFinanceManage/212/stop"
subprocess.check_output(['curl', "-X", "POST", url])
