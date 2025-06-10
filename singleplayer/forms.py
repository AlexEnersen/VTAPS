from django import forms
from django.forms import ModelForm

from .models import IrrigationEntries, FertilizerEntries1, FertilizerEntries2, SingleplayerProfile, FertilizerInit

class SingleplayerProfileForm(ModelForm):
    class Meta:
        model = SingleplayerProfile
        fields = ['hybrid', 'seeding_rate', 'weather_type']

class IrrigationEntriesForm(ModelForm):
    class Meta:
        model = IrrigationEntries
        fields = '__all__'

class FertilizerEntriesForm1(ModelForm):
    class Meta:
        model = FertilizerEntries1
        fields = '__all__'

class FertilizerEntriesForm2(ModelForm):
    class Meta:
        model = FertilizerEntries2
        fields = '__all__'

class FertilizerInitForm(ModelForm):
    class Meta:
        model = FertilizerInit
        fields = '__all__'