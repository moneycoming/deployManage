from django.test import TestCase
import time
import datetime

now = datetime.datetime.now()
t = now.strftime('%Y%m%d%I%M')
print(t)

