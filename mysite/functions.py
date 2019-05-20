import time
from django.db import models


class TimeChange:
    def __init__(self, timeStamp):
        self.timeStamp = timeStamp

    def ChangeFormat(self):
        timeStamp = self.timeStamp
        timeArray = time.localtime(timeStamp)
        otherStyleTime = time.strftime("%Y--%m--%d %H:%M:%S", timeArray)
        # print(otherStyleTime)
        return otherStyleTime


class fileObj(models.Model):
    def __init__(self, fileKeyList, createDateList):
        self.fileKeyList = fileKeyList
        self.createDateList = createDateList
        self.index = len(fileKeyList)

    def __iter__(self):
        return self

    def __next__(self):
        if self.index == 0:
            raise StopIteration
        self.index -= 1
        return self.fileKeyList[self.index], self.createDateList[self.index]
