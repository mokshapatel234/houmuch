from django.contrib import admin
from .models import Owner, RoomType, PropertyType, RoomFeature, BathroomType, BedType, CommonAmenities, ExperienceSlot, Property
from django.contrib.auth.models import Group
from django.utils.html import format_html


# Register your models here.
admin.site.unregister(Group)


class UserAdmin(admin.ModelAdmin):
    admin.site.site_header = 'Hotel App'


class OwnerAdmin(admin.ModelAdmin):
    list_display = ['hotel_name', 'email', 'phone_number', 'government_id', 'is_verified',]
    search_fields = ['hotel_name',]
    list_per_page = 20


class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ['property_type', 'bid_time_duration',]
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


class PropertyAdmin(admin.ModelAdmin):
    list_display = ['get_image','parent_hotel_group', 'hotel_nick_name', 'manager_name', 'hotel_phone_number', 'hotel_website']

    @admin.display(description='Image')
    def get_image(self, obj):
        return format_html('<img src="{}" width=80px height=75px/>'.format(f'https://houmuch.s3.amazonaws.com/{obj.image}'))

admin.site.register(Owner, OwnerAdmin)
admin.site.register(PropertyType, PropertyTypeAdmin)
admin.site.register(RoomType, RoomTypeAdmin)
admin.site.register(RoomFeature, RoomFeatureAdmin)
admin.site.register(BathroomType, BathroomTypeAdmin)
admin.site.register(BedType, BedTypeAdmin)
admin.site.register(CommonAmenities, CommonAmenitiesAdmin)
admin.site.register(ExperienceSlot, ExperienceSlotAdmin)
admin.site.register(Property, PropertyAdmin)
