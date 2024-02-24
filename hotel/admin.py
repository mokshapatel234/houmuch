from django.contrib import admin
from .models import Owner, RoomType, Category, PropertyType, RoomFeature, BathroomType, BedType, CommonAmenities, \
    ExperienceSlot, Property, RoomInventory, RoomImage, PropertyImage
from django.contrib.auth.models import Group
from django.utils.html import format_html
from .forms import PropertyForm
from django import forms


# Register your models here.
admin.site.unregister(Group)


class UserAdmin(admin.ModelAdmin):
    admin.site.site_header = 'Hotel App'


class OwnerAdmin(admin.ModelAdmin):
    list_display = ['hotel_name', 'email', 'phone_number', 'gst', 'is_verified',]
    search_fields = ['hotel_name', 'phone_number']
    list_per_page = 20


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category', 'bid_time_duration']
    search_fields = ['category',]
    list_per_page = 20


class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ['property_type',]
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


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'image':
            kwargs['widget'] = forms.TextInput()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width=280px height=250px/>'.format(f'https://houmuch.s3.amazonaws.com/{obj.image}'))
        return "-"
    image_preview.short_description = "Image Preview"


class PropertyAdmin(admin.ModelAdmin):
    inlines = [PropertyImageInline,]
    form = PropertyForm
    list_display = ['hotel_nick_name', 'parent_hotel_group', 'manager_name', 'hotel_phone_number', 'hotel_website', 'get_owner_name',]
    list_per_page = 20

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='Owner Name')
    def get_owner_name(self, obj):
        return obj.owner.hotel_name


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'image':
            kwargs['widget'] = forms.TextInput()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width=280px height=250px/>'.format(f'https://houmuch.s3.amazonaws.com/{obj.image}'))
        return "-"
    image_preview.short_description = "Image Preview"


class RoomAdmin(admin.ModelAdmin):
    inlines = [RoomImageInline,]
    list_display = ['room_name', 'get_property_name', 'floor', 'room_view', 'default_price', 'adult_capacity', 'children_capacity',]
    search_fields = ['room_name', 'property__owner__hotel_name',]
    list_per_page = 20

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='Property Name')
    def get_property_name(self, obj):
        return obj.property.hotel_nick_name


admin.site.register(Owner, OwnerAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(PropertyType, PropertyTypeAdmin)
admin.site.register(RoomType, RoomTypeAdmin)
admin.site.register(RoomFeature, RoomFeatureAdmin)
admin.site.register(BathroomType, BathroomTypeAdmin)
admin.site.register(BedType, BedTypeAdmin)
admin.site.register(CommonAmenities, CommonAmenitiesAdmin)
admin.site.register(ExperienceSlot, ExperienceSlotAdmin)
admin.site.register(Property, PropertyAdmin)
admin.site.register(RoomInventory, RoomAdmin)
