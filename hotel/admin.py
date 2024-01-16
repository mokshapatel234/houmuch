from django.contrib import admin
from .models import Owner, RoomType, PropertyType, RoomFeature, BathroomType, BedType, CommonAmenities, ExperienceSlot
from django.contrib.auth.models import Group

# Register your models here.
admin.site.unregister(Group)

class UserAdmin(admin.ModelAdmin):
    admin.site.site_header = 'Hotel App'

class OwnerAdmin(admin.ModelAdmin):
    list_display = ['first_name','last_name','email','phone_number','government_id','is_verified',]
    search_fields = ['first_name','last_name',]
    list_per_page = 20

class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ['property_type','bid_time_duration',]
    search_fields = ['property_type',]
    list_per_page = 20

class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['room_type',]
    search_fields = ['room_type',]
    list_per_page = 20

class BedTypeAdmin(admin.ModelAdmin):
    list_display = ['bed_type',]
    search_fields = ['bed_type',]
    list_per_page = 20

class BathroomTypeAdmin(admin.ModelAdmin):
    list_display = ['bathroom_type',]
    search_fields = ['bathroom_type',]
    list_per_page = 20

class RoomFeatureAdmin(admin.ModelAdmin):
    list_display = ['room_feature',]
    search_fields = ['room_feature',]
    list_per_page = 20

class CommonAmenitiesAdmin(admin.ModelAdmin):
    list_display = ['common_ameninity',]
    search_fields = ['common_ameninity',]
    list_per_page = 20

class ExperienceSlotAdmin(admin.ModelAdmin):
    list_display = ['slot',]
    search_fields = ['slot',]
    list_per_page = 20

admin.site.register(Owner, OwnerAdmin)
admin.site.register(PropertyType, PropertyTypeAdmin)
admin.site.register(RoomType, RoomTypeAdmin)
admin.site.register(RoomFeature, RoomFeatureAdmin)
admin.site.register(BathroomType, BathroomTypeAdmin)
admin.site.register(BedType, BedTypeAdmin)
admin.site.register(CommonAmenities, CommonAmenitiesAdmin)
admin.site.register(ExperienceSlot, ExperienceSlotAdmin)