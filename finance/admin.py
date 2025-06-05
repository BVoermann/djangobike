from django.contrib import admin
from .models import Credit, Transaction, MonthlyReport

admin.site.register(Credit)
admin.site.register(Transaction)
admin.site.register(MonthlyReport)
