from django import forms
from .models import GradeScale


class GradeScaleForm(forms.ModelForm):
    class Meta:
        model = GradeScale
        fields = "__all__"