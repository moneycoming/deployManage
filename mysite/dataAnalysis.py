from mysite import models


class dataAnalysis:
    def __init__(self, production):
        self.production = production

    def totalCounts(self):
        production = self.production
        tasks = models.TaskBar.objects.filter(production=production)
        counts = len(tasks)

        return counts

    def monthCounts(self, month):
        production = self.production
        tasks = models.TaskBar.objects.filter(production=production)
        monthCounts = 0
        for i in range(len(tasks)):
            if month == tasks[i].createDate.month:
                monthCounts += 1

        return monthCounts
