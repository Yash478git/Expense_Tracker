from django.contrib import admin
from .models import Category, Transaction, Budget, Report, UserProfile


admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(Budget)
admin.site.register(Report)
admin.site.register(UserProfile)