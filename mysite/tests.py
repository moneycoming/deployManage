import subprocess
import jenkins
import time
# now = datetime.datetime.now()
# t = now.strftime('%Y%m%d%I%M')
# print(t)
user = "fabu"
token = "1159ae85fefbbc674c5493822c78b114b5"
url = "http://jenkinspro.bestjlb.cn/"
jenkinsJob = "UAT-institutionFinanceManage-COPY"
# subprocess.check_output(['curl', "-X", "POST", url])
server = jenkins.Jenkins(url, username=user, password=token)
server.build_job(jenkinsJob, {'BRANCH': 'master'})
time.sleep(15)
consoleOpt = server.get_build_console_output(jenkinsJob, 82)
isSuccess = consoleOpt.find("Finished: SUCCESS")
while isSuccess == -1:
    time.sleep(2)
    consoleOpt = server.get_build_console_output(jenkinsJob, 82)
    print(consoleOpt)
