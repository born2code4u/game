from django import forms
from django.forms import inineformset_factoy
from .models import apiorders, Player, Constants
import django.forms as djforms

class apiordersForm(forms.ModelForm):
    ...

apiordersFormSet = inlineformset_factory(Player,apiorders,
                                         can_delete=False,extra=0,form=apiordersForm,
                                         formset=BaseInlineFormSet)
