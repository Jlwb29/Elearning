from django import forms
from .models import Status

class StatusForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ["text"]
        widgets = {
            "text": forms.TextInput(attrs={
                "placeholder": "Post a status…",
                "maxlength": 280
            })
        }
