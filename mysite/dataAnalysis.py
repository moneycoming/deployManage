from mysite import models


class dataAnalysis:
    def __init__(self, production):
        self.production = production

    def totalCounts(self):
        production = self.production
        plans = models.deployPlan.objects.filter(production=production)
        counts = len(plans)

        return counts

    def monthCounts(self, month):
        production = self.production
        plans = models.deployPlan.objects.filter(production=production)
        monthCounts = 0
        for i in range(len(plans)):
            if month == plans[i].createDate.month:
                monthCounts += 1

        return monthCounts
