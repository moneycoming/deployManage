from mysite import models


class DataAnalysis:
    def __init__(self, production):
        self.production = production

    def totalCounts(self):
        production = self.production
        plans = models.plan.objects.filter(production=production)
        counts = len(plans)

        return counts

    def monthCounts(self, month):
        production = self.production
        plans = models.plan.objects.filter(production=production)
        monthCounts = 0
        for i in range(len(plans)):
            if month == plans[i].createDate.month:
                monthCounts += 1

        return monthCounts

    def monthKindCounts(self, month, kind):
        production = self.production
        deployPlans = models.plan.objects.filter(production=production)
        perKindPlans = deployPlans.filter(kind=kind)
        monthKindCounts = 0
        for i in range(len(perKindPlans)):
            if month == perKindPlans[i].createDate.month:
                monthKindCounts += 1

        return monthKindCounts
