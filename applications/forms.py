from django import forms
from datetime import datetime, timedelta
from django.utils.safestring import mark_safe
from django.forms import inlineformset_factory
from django.utils import timezone

from .models import Application, ApplicationAnswer, Question

class ApplicationDatesForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['first_name', 'last_name', 'email', 'date_join', 'date_leave', 'guests', 'member_type']
        widgets = {
            'date_join': forms.DateInput(attrs={'type': 'date', 'required': True, 'min': timezone.now().date().isoformat()}),
            'date_leave': forms.DateInput(attrs={'type': 'date', 'required': True, 'min': timezone.now().date().isoformat()}),
        }

    def clean_date_join(self):
        date_join = self.cleaned_data.get('date_join')
        if date_join and date_join < timezone.now().date():
            raise forms.ValidationError(mark_safe('<i style="color: #FF69B4;"> Arrival date cannot be in the past 🌸 </i>'))
        return date_join

    def clean_date_leave(self):
        date_leave = self.cleaned_data.get('date_leave')
        date_join = self.cleaned_data.get('date_join')
        
        if not date_leave:
            raise forms.ValidationError('Departure date is required.')
            
        if date_join and date_leave:
            if date_leave < timezone.now().date():
                raise forms.ValidationError(mark_safe('<i style="color: #FF69B4;"> Departure date cannot be in the past 🌸 </i>'))
                
        return date_leave

    def clean(self):
        cleaned_data = super().clean()
        date_join = cleaned_data.get('date_join')
        date_leave = cleaned_data.get('date_leave')

        if date_join and date_leave:
            if date_leave <= date_join:
                raise forms.ValidationError('Departure date must be after arrival date.')
            
            # Check if stay duration exceeds 93 days
            days_difference = (date_leave - date_join).days
            if days_difference > 93:
                raise forms.ValidationError(
                    mark_safe('<i style="color: #FF69B4;"> Initial bookings are limited to 93 days (3 months). You can extend your stay after arrival if space is available. 🌸 </i>')
                )

        return cleaned_data

class ApplicationAnswerForm(forms.ModelForm):
    class Meta:
        model = ApplicationAnswer
        fields = ['answer']
        widgets = {
            'answer': forms.Textarea(attrs={'rows': 4}),
        }

class ApplicationNameForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['first_name', 'last_name', 'email']  # Add any other fields you need from the Application model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_questions = Question.objects.filter(is_active=True).order_by('order')
        for question in active_questions:
            self.fields[f'question_{question.id}'] = forms.CharField(
                label=question.text,
                required=question.required,
                widget=forms.Textarea(attrs={'rows': 4})
            )

    def clean(self):
        cleaned_data = super().clean()
        if self.data.get('submit'):
            for field_name, value in cleaned_data.items():
                if field_name.startswith('question_'):
                    question_id = int(field_name.split('_')[1])
                    question = Question.objects.get(id=question_id)
                    if question.required and not value:
                        self.add_error(field_name, 'This field is required for submission.')
        return cleaned_data

    def save(self, commit=True):
        application = super().save(commit=commit)
        if commit:
            # Save answers for dynamic questions
            for field_name, value in self.cleaned_data.items():
                if field_name.startswith('question_'):
                    question_id = int(field_name.split('_')[1])
                    question = Question.objects.get(id=question_id)
                    ApplicationAnswer.objects.update_or_create(
                        application=application,
                        question=question,
                        defaults={'answer': value}
                    )
        return application

class ApplicationEditForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['first_name', 'last_name', 'email', 'date_join', 'date_leave', 
                 'guests', 'member_type']
        widgets = {
            'date_join': forms.DateInput(attrs={'type': 'date', 'required': True, 'min': timezone.now().date().isoformat()}),
            'date_leave': forms.DateInput(attrs={'type': 'date', 'required': True, 'min': timezone.now().date().isoformat()}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            active_questions = Question.objects.filter(is_active=True).order_by('order')
            for question in active_questions:
                answer = ApplicationAnswer.objects.filter(
                    application=self.instance,
                    question=question
                ).first()
                field_name = f'question_{question.id}'
                self.fields[field_name] = forms.CharField(
                    label=question.text,
                    required=False,  # Set to False initially
                    widget=forms.Textarea(attrs={'rows': 4}),
                    initial=answer.answer if answer else ''
                )

    def clean(self):
        cleaned_data = super().clean()
        date_join = cleaned_data.get('date_join')
        date_leave = cleaned_data.get('date_leave')

        if not date_join:
            raise forms.ValidationError('Arrival date is required')
        if not date_leave:
            raise forms.ValidationError('Departure date is required')

        if date_join and date_leave:
            if date_leave <= date_join:
                raise forms.ValidationError('Departure date must be after arrival date.')
            
            # Check if stay duration exceeds 93 days
            days_difference = (date_leave - date_join).days
            if days_difference > 93:
                raise forms.ValidationError(
                    mark_safe('<i style="color: #FF69B4;"> Initial bookings are limited to 93 days (3 months). You can extend your stay after arrival if space is available. 🌸 </i>')
                )

        # Only validate question fields if we're not checking availability and not continuing to questions
        if 'check_availability' not in self.data and self.data.get('action') != 'continue_to_questions':
            # Create a list of items to avoid dictionary size change during iteration
            field_items = list(cleaned_data.items())
            for field_name, value in field_items:
                if field_name.startswith('question_'):
                    question_id = int(field_name.split('_')[1])
                    question = Question.objects.get(id=question_id)
                    if question.required and not value:
                        self.add_error(field_name, 'This field is required.')

        return cleaned_data

    def save(self, commit=True):
        application = super().save(commit=commit)
        if commit:
            # Save answers for dynamic questions
            for field_name, value in self.cleaned_data.items():
                if field_name.startswith('question_'):
                    question_id = int(field_name.split('_')[1])
                    question = Question.objects.get(id=question_id)
                    ApplicationAnswer.objects.update_or_create(
                        application=application,
                        question=question,
                        defaults={'answer': value}
                    )
        return application
