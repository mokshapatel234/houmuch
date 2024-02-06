from django import forms
from .models import Property
from django.utils.safestring import mark_safe

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(PropertyForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.image:
            self.fields['image'].help_text = mark_safe(
                '<img src="{}" width=280px height=250px/>'.format(f'https://houmuch.s3.amazonaws.com/{self.instance.image}'))