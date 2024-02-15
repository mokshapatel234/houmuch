from django import forms
from .models import Property
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
