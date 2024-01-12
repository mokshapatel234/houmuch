from django.contrib import admin
from .models import Customer
# Register your models here.

class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name','last_name','email','phone_number','government_id',]
    search_fields = ['first_name','last_name', ]
    list_per_page = 20

admin.site.register(Customer, CustomerAdmin)