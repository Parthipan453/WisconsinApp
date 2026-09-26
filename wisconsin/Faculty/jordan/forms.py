from django import forms
from Research.models import StudentResearchPublication, PublicationAuthor


class StudentResearchPublicationForm(forms.ModelForm):
    class Meta:
        model = StudentResearchPublication
        fields = ['title', 'abstract', 'keywords', 'publication_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter publication title'}),
            'abstract': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter abstract'}),
            'keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter keywords (comma separated)'}),
            'publication_type': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError('Title must be at least 5 characters long.')
        return title
    
    def clean_abstract(self):
        abstract = self.cleaned_data.get('abstract')
        if len(abstract) < 20:
            raise forms.ValidationError('Abstract must be at least 20 characters long.')
        return abstract


class PublicationAuthorForm(forms.Form):
    team_member_id = forms.IntegerField(widget=forms.HiddenInput())
    author_role = forms.ChoiceField(choices=PublicationAuthor.AUTHOR_ROLE)
    author_order = forms.IntegerField(required=False)



# ========================== Research Submission ===============================

from django import forms
from Research.models import StudentResearchPublication, PublicationSubmission


class ResearchSubmissionForm(forms.ModelForm):
    """
    Form for creating/updating research submissions
    """
    journal_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter journal name'
        })
    )
    conference_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter conference name'
        })
    )
    publisher = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter publisher name'
        })
    )
    submission_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    manuscript_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter manuscript number'
        })
    )
    acceptance_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    publication_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    doi = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter DOI (e.g., 10.1234/abcd1234)'
        })
    )
    publication_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter publication URL'
        })
    )
    
    class Meta:
        model = StudentResearchPublication
        fields = ['title', 'abstract', 'keywords', 'publication_type']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter publication title'
            }),
            'abstract': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter abstract'
            }),
            'keywords': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter keywords (comma separated)'
            }),
            'publication_type': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title) < 5:
            raise forms.ValidationError('Title must be at least 5 characters long.')
        return title
    
    def clean_abstract(self):
        abstract = self.cleaned_data.get('abstract')
        if abstract and len(abstract) < 20:
            raise forms.ValidationError('Abstract must be at least 20 characters long.')
        return abstract
    
    def clean(self):
        cleaned_data = super().clean()
        publication_type = cleaned_data.get('publication_type')
        journal_name = cleaned_data.get('journal_name')
        conference_name = cleaned_data.get('conference_name')
        
        if publication_type == 'JOURNAL' and not journal_name:
            self.add_error('journal_name', 'Journal name is required for Journal publications.')
        elif publication_type == 'CONFERENCE' and not conference_name:
            self.add_error('conference_name', 'Conference name is required for Conference publications.')
        
        return cleaned_data


class SubmissionStatusForm(forms.Form):
    """
    Form for updating submission status
    """
    status = forms.ChoiceField(
        choices=StudentResearchPublication.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )