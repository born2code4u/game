from django import forms

class NameForm(forms.Form):
    your_name = forms.CharField(label='Your name', max_length=100)

class OrderForm(forms.Form):
    the_age = forms.IntegerField(label='age')
