from django import forms
from .models import Property, SubscriptionPlan, BookingHistory
from django.contrib.gis import forms as gis_forms


class PropertyForm(forms.ModelForm):
    location = gis_forms.PointField(widget=gis_forms.OSMWidget(attrs={
        'map_width': 800,
        'map_height': 500
    }))

    class Meta:
        model = Property
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(PropertyForm, self).__init__(*args, **kwargs)
        if 'location' in self.fields:
            self.fields['location'].disabled = True


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(SubscriptionPlanForm, self).__init__(*args, **kwargs)
        if 'razorpay_plan_id' in self.fields:
            self.fields['razorpay_plan_id'].disabled = True


class BookingHistoryForm(forms.ModelForm):
    class Meta:
        model = BookingHistory
        fields = ['property', 'rooms', 'amount', 'check_in_date', 'check_out_date', 'book_status', 'payment_id', 'is_cancel', 'cancel_date', 'cancel_reason', 'cancel_by_owner']
