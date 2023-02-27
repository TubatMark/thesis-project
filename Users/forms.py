from django import forms
from .models import *
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.forms import UserChangeForm


class RepositoryForm(forms.ModelForm):
    proponents = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Enter names separated by commas'}))

    class Meta:
        model = RepositoryFiles
        fields = ["title", "proponents", "adviser", "school_year", "pdf_file", "abstract"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-group"}),
            "adviser": forms.TextInput(attrs={"class": "form-group"}),
            "school_year": forms.TextInput(attrs={"class": "form-group"}),
            "pdf_file": forms.FileInput(attrs={"class": "form-group"}),
            "abstract": forms.Textarea(attrs={"class": "form-group"}),
        }
        
    def save(self, commit=True):
        repository_file = super().save(commit=False)
        proponent_names = [name.strip() for name in self.cleaned_data['proponents'].split(',') if name.strip()]
        proponents = [Proponent.objects.get_or_create(name=name)[0] for name in proponent_names]
        repository_file.save()
        repository_file.proponents.set(proponents)
        return repository_file

class ProfilePictureForm(forms.Form):
    profile_picture = forms.ImageField()

class StudentForm(forms.Form):
    # upload excel file for all enrolled students
    file = forms.FileField()
    
class EditStudentForm(forms.ModelForm):
    class Meta:
        model = StudentUsers
        fields = "__all__"

class EditRegisteredStudentForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username','email','name','student_id']


class UploadDocumentsForm(forms.ModelForm):
    class Meta:
        model = UploadDocuments
        fields = ["student_title", "student_proponents", "adviser", "school_year", "student_pdf_file", "abstract"]
        widgets = {
            "student_title": forms.TextInput(attrs={"class": "form-group"}),
            "student_proponents": forms.TextInput(attrs={"class": "form-group"}),
            "adviser": forms.TextInput(attrs={"class": "form-group"}),
            "school_year": forms.TextInput(attrs={"class": "form-group"}),
            "student_pdf_file": forms.FileInput(attrs={"class": "form-group"}),
            "abstract": forms.Textarea(attrs={"class": "form-group"}),
        }
        
class DocumentComparisonForm(forms.ModelForm):
    class Meta:
        model = DocumentComparison
        fields = ['doc1_title', 'doc1_proponents', 'doc1_pdf_file', 'doc2_title', 'doc2_proponents', 'doc2_pdf_file']
        widgets = {
            "doc1_title": forms.TextInput(attrs={"class": "form-group"}),
            "doc1_proponents": forms.TextInput(attrs={"class": "form-group"}),
            "doc1_pdf_file": forms.FileInput(attrs={"class": "form-group"}),
            "doc2_title": forms.TextInput(attrs={"class": "form-group"}),
            "doc2_proponents": forms.TextInput(attrs={"class": "form-group"}),
            "doc2_pdf_file": forms.FileInput(attrs={"class": "form-group"}),
        }



class StudentRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-group"}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-group"}))

    class Meta:
        model = Student
        fields = ['password', 'confirm_password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

class PanelUsersForm(forms.ModelForm):
 
    class Meta:
        model = PanelUsers
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "password": forms.PasswordInput(attrs={"class": "form-control"}),
        }
        
class EditRegisteredPanelForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username','email','first_name','last_name']

class AdminUsersForm(forms.ModelForm):
 
    class Meta:
        model = AdminUsers
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "password": forms.PasswordInput(attrs={"class": "form-control"}),
        }

class SimilarityThresholdForm(forms.ModelForm):
    
    class Meta:
        model = SimilarityThreshold
        fields = ['threshold']
        widgets = {
            "threshold": forms.TextInput(attrs={"class": "form-control"}),
        }