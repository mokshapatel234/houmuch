from django import forms
from .models import Property
from django.utils.safestring import mark_safe
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
        if self.instance and self.instance.image:
            self.fields['image'].help_text = mark_safe(
                '<img src="{}" width=280px height=250px/>'.format(f'https://houmuch.s3.amazonaws.com/{self.instance.image}'))
        if 'location' in self.fields:
            self.fields['location'].disabled = True
