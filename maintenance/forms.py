from django import forms
from .models import MaintenanceRequest

class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['title', 'description', 'user_confirmation']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300',
                'placeholder': 'Enter a title for your maintenance request'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-300',
                'rows': 4,
                'placeholder': 'Describe the maintenance issue in detail'
            }),
            'user_confirmation': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-[#006340] focus:ring-[#006340] mt-1'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_confirmation'].required = True

class MaintenanceRequestManagerForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['status', 'manager_notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300'
            }),
            'manager_notes': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-300',
                'rows': 4,
                'placeholder': 'Add notes about this maintenance request'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager_notes'].help_text = "Edit this text to change what appears above the required checkbox" 