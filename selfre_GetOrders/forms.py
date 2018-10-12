from . import models
from ._builtin import Page, WaitPage
from .models import Constants
from otree.api import Currency as c 
import random

import selfremarket.selfre_market
from .models import Constants, Orderapi, Player
from django import forms
from django.forms import modelformset_factory, formset_factory, BaseFormSet
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList

from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _, ngettext, ungettext

class ImportForm(forms.Form):
    underlyingDes = None
    yes=forms.BooleanField()

class BaseImportFormSet(BaseFormSet):
    def clean(self):
        print("msg custom self.clean()")
        # cleaned_data = super(BaseImportFormSet, self).clean()
        raise forms.ValidationError("Please BLBLJB choose one")
        # return cleaned_data
