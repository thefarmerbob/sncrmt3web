from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta, date
from django.db import models
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.http import JsonResponse
from django.urls import reverse

from .forms import ApplicationDatesForm, ApplicationNameForm, ApplicationEditForm          
from chapters.models import Chapter, ChapterBooking
from .models import Application, ApplicationAnswer, ReintroductionAnswer, ReintroductionQuestionSettings, ShortStayWarning, PricingSettings
from questions.models import Question, ReintroductionQuestion

@login_required
def applications_list(request):
    applications = Application.objects.filter(
        created_by=request.user,
        is_active=True
    ).exclude(
        status='Withdrawn'
    ).order_by('-created_at')  # Show newest applications first

    # If there are no applications, redirect to new application page
    if not applications.exists():
        return redirect('applications')

    return render(request, 'applications/applications_list.html', {
        'applications': applications
    })

@login_required
def application_detail(request, pk): #shows application details
    application = Application.objects.filter(created_by = request.user).get(pk=pk)

    return render(request, 'applications/application_detail.html', {
        'application': application
    })

@login_required
def applications(request):
    # Only clear session data if we're not coming back from questions
    if request.method == 'GET' and not request.GET.get('from_questions'):
        if 'application_id' in request.session:
            del request.session['application_id']
        if 'current_question_index' in request.session:
            del request.session['current_question_index']
    
    # Check if we have an existing application in the session
    application_id = request.session.get('application_id')
    application = None
    if application_id:
        application = get_object_or_404(Application, id=application_id, created_by=request.user)

    # Get the short stay warning message and pricing settings
    short_stay_message = ShortStayWarning.get_active()
    pricing_settings = PricingSettings.get_settings().get_formatted_texts()

    # Check for pre-filled data from availability matrix
    prefill_chapter_id = request.GET.get('chapter')
    prefill_date = request.GET.get('date')
    
    # Create initial form data
    initial_data = {}
    if prefill_date:
        try:
            parsed_date = datetime.strptime(prefill_date, '%Y-%m-%d').date()
            initial_data['date_join'] = parsed_date
            # Set a default checkout date (e.g., 30 days later)
            initial_data['date_leave'] = parsed_date + timedelta(days=30)
        except ValueError:
            pass  # Ignore invalid date format

    if request.method == 'POST':
        # If we have an existing application, update it instead of creating a new one
        if application:
            form = ApplicationDatesForm(request.POST, instance=application)
        else:
            form = ApplicationDatesForm(request.POST)

        if form.is_valid():
            date_join = form.cleaned_data['date_join']
            date_leave = form.cleaned_data['date_leave']
            
            # Calculate stay duration
            days_difference = (date_leave - date_join).days
            
            # If checking availability and stay is over 93 days, show message without chapters
            if 'check_availability' in request.POST and days_difference > 93:
                messages.warning(request, mark_safe('<i style="color: #FF69B4;">Please adjust your dates to 93 days or less to view available chapters. You can extend your stay after arrival if space is available. 🌸</i>'))
                return render(request, 'applications/new_application.html', {
                    'form': form,
                    'application': application,
                    'dates_selected': False,  # Don't show chapters
                    'short_stay_message': short_stay_message,
                    'pricing_settings': pricing_settings,
                    'prefill_chapter_id': prefill_chapter_id
                })

            # Get all chapters with availability status
            chapters_with_availability = get_available_chapters(date_join, date_leave)
            nights = (date_leave - date_join).days

            # If just checking availability
            if 'check_availability' in request.POST:
                # Calculate costs for all chapters and include images
                chapters_info = []
                for chapter_data in chapters_with_availability:
                    chapter = chapter_data['chapter']
                    # Create a temporary application object to calculate cost
                    temp_application = Application(
                        chapter=chapter,
                        date_join=date_join,
                        date_leave=date_leave,
                        member_type=form.cleaned_data['member_type'],
                        guests=form.cleaned_data['guests']
                    )
                    total_cost = temp_application.calculate_cost()
                    # Calculate per guest cost if there are 2 guests
                    per_guest_cost = round(total_cost / 2, 2) if form.cleaned_data['guests'] == '2' else None
                    
                    # Get pricing breakdown for this chapter
                    pricing_breakdown = temp_application.get_pricing_breakdown()
                    
                    # Check if short-term pricing is being used
                    is_short_term = (chapter.use_short_term_pricing and 
                                    nights <= chapter.short_term_threshold_days and 
                                    chapter.short_term_price_per_night > 0)
                    
                    chapters_info.append({
                        'chapter': chapter,
                        'is_available': chapter_data['is_available'],
                        'nightly_rate': chapter.get_display_rate_per_night(nights),
                        'total_cost': total_cost,
                        'per_guest_cost': per_guest_cost,
                        'nights': nights,
                        'images': chapter.images.all(),
                        'pricing_breakdown': pricing_breakdown,
                        'is_short_term': is_short_term
                    })

                context = {
                    'form': form,
                    'chapters_info': chapters_info,
                    'dates_selected': True,
                    'application': application,
                    'short_stay_message': short_stay_message,
                    'pricing_settings': pricing_settings,
                    'prefill_chapter_id': prefill_chapter_id  # Pass to template for auto-selection
                }
                return render(request, 'applications/new_application.html', context)
            
            # If continuing to next step
            else:
                # Create or update application
                if application:
                    # Update the application with the new form data
                    application = form.save()
                else:
                    application = form.save(commit=False)
                    application.created_by = request.user
                
                # Get selected chapter
                chapter_id = request.POST.get('chapter')
                if chapter_id:
                    # If we're updating an existing application, preserve its answers
                    existing_answers = None
                    if application.id:
                        existing_answers = list(ApplicationAnswer.objects.filter(application=application))
                    
                    # Reset the current question index when changing chapters
                    request.session['current_question_index'] = 0
                    
                    application.chapter_id = chapter_id
                    application.date_join = date_join
                    application.date_leave = date_leave
                    application.save()
                    
                    # If we had existing answers and changed chapters, reassign them to the updated application
                    if existing_answers:
                        for answer in existing_answers:
                            answer.application = application
                            answer.save()
                    
                    # Store application ID in session
                    request.session['application_id'] = application.id
                    
                    # Check if this is a returning member and redirect to reintroduction question
                    if application.member_type == 'returning member':
                        return redirect('reintroduction_question')
                    else:
                        # Redirect to step 2 for new members
                        return redirect('application_step2')
                else:
                    # If no chapter was selected, show the chapters again
                    chapters_info = []
                    for chapter_data in chapters_with_availability:
                        chapter = chapter_data['chapter']
                        # Create a temporary application object to calculate cost
                        temp_application = Application(
                            chapter=chapter,
                            date_join=date_join,
                            date_leave=date_leave,
                            member_type=form.cleaned_data['member_type'],
                            guests=form.cleaned_data['guests']
                        )
                        total_cost = temp_application.calculate_cost()
                        # Calculate per guest cost if there are 2 guests
                        per_guest_cost = round(total_cost / 2, 2) if form.cleaned_data['guests'] == '2' else None
                        
                        # Get pricing breakdown for this chapter
                        pricing_breakdown = temp_application.get_pricing_breakdown()
                        
                        # Check if short-term pricing is being used
                        is_short_term = (chapter.use_short_term_pricing and 
                                        nights <= chapter.short_term_threshold_days and 
                                        chapter.short_term_price_per_night > 0)
                        
                        chapters_info.append({
                            'chapter': chapter,
                            'is_available': chapter_data['is_available'],
                            'nightly_rate': chapter.get_display_rate_per_night(nights),
                            'total_cost': total_cost,
                            'per_guest_cost': per_guest_cost,
                            'nights': nights,
                            'images': chapter.images.all(),
                            'pricing_breakdown': pricing_breakdown,
                            'is_short_term': is_short_term
                        })
                    
                    context = {
                        'form': form,
                        'chapters_info': chapters_info,
                        'dates_selected': True,
                        'application': application,
                        'short_stay_message': short_stay_message,
                        'pricing_settings': pricing_settings,
                        'prefill_chapter_id': prefill_chapter_id  # Pass to template for auto-selection
                    }
                    return render(request, 'applications/new_application.html', context)
    else:
        # GET request - show the form
        if application:
            form = ApplicationDatesForm(instance=application, initial=initial_data)
        else:
            form = ApplicationDatesForm(initial=initial_data)

    context = {
        'form': form,
        'application': application,
        'short_stay_message': short_stay_message,
        'pricing_settings': pricing_settings,
        'prefill_chapter_id': prefill_chapter_id,
        'from_questions': request.GET.get('from_questions')  # Pass this to template
    }
    return render(request, 'applications/new_application.html', context)

@login_required
def available_chapters(request):
    application_data = request.session.get('application_data')
    if not application_data:
        return redirect('applications')  # Go back to step 1 if no data

    date_join = datetime.fromisoformat(application_data['date_join'])
    date_leave = datetime.fromisoformat(application_data['date_leave'])

    # Get all chapters
    all_chapters = Chapter.objects.all()
    available_chapters = []

    for chapter in all_chapters:
        # Check if chapter has any conflicting bookings
        conflicting_bookings = ChapterBooking.objects.filter(
            chapter=chapter
        ).filter(
            models.Q(start_date__lte=date_leave) & 
            models.Q(end_date__gte=date_join)
        ).exists()

        if not conflicting_bookings:
            available_chapters.append(chapter)

    if request.method == 'POST':
        selected_chapter = request.POST.get('chapter')
        if selected_chapter:
            # Create and save the initial application with all fields
            application = Application(
                created_by=request.user,
                first_name=application_data['first_name'],
                last_name=application_data['last_name'],
                email=application_data['email'],
                date_join=date_join,
                date_leave=date_leave,
                guests=application_data['guests'],
                member_type=application_data['member_type']
            )
            
            # Validate the application before saving
            try:
                application.full_clean()
                application.save()
            except ValidationError as e:
                messages.error(request, f"Invalid application data: {e}")
                return redirect('applications')
            
            # Store the application ID in session for future steps
            request.session['application_id'] = application.id
            request.session['application_data']['chapter_id'] = selected_chapter
            
            # Check if this is a returning member and redirect to reintroduction question
            if application.member_type == 'returning member':
                return redirect('reintroduction_question')
            else:
                return redirect('application_step2')

    return render(request, 'applications/available_chapters.html', {
        'chapters': available_chapters
    })

@login_required
def application_step2(request):
    # Get the application from session
    application_id = request.session.get('application_id')
    if not application_id:
        return redirect('applications')
    
    application = get_object_or_404(Application, id=application_id, created_by=request.user)
    
    # Get all active questions ordered by their order field
    questions = Question.objects.filter(is_active=True).order_by('order')
    
    # Get current question index from session or default to 0
    current_question_index = request.session.get('current_question_index', 0)
    
    # If we've answered all questions, clear session and redirect to success
    if current_question_index >= questions.count():
        if 'current_question_index' in request.session:
            del request.session['current_question_index']
        if 'application_id' in request.session:
            del request.session['application_id']
        if 'edit_questions' in request.session:
            del request.session['edit_questions']
        application.status = 'Submitted'
        application.save()
        return redirect('application_success')
    
    current_question = questions[current_question_index]
    
    # Get the answer for this question if it exists for this specific application
    try:
        answer = ApplicationAnswer.objects.get(
            application=application,
            question=current_question
        )
    except ApplicationAnswer.DoesNotExist:
        # For new applications, create a blank answer
        answer = ApplicationAnswer.objects.create(
            application=application,
            question=current_question,
            answer=''
        )

    save_success = False
    if request.method == 'POST':
        action = request.POST.get('action', 'next')
        
        # Handle back to chapter selection
        if action == 'back_to_chapter':
            # Save the current answer
            answer_text = request.POST.get('answer')
            if answer_text:
                answer.answer = answer_text
                answer.save()
            
            # Only clear edit_questions flag, preserve current_question_index
            if 'edit_questions' in request.session:
                del request.session['edit_questions']
            applications_url = reverse('applications') + '?from_questions=true'
            return redirect(applications_url)
        
        # Save the current answer regardless of direction
        answer_text = request.POST.get('answer')
        if answer_text is not None:  # Save even if empty string
            answer.answer = answer_text
            answer.save()
        
        if action == 'previous':
            # Move to previous question
            request.session['current_question_index'] = max(0, current_question_index - 1)
            return redirect('application_step2')
        elif action == 'save':
            # Stay on the same question and show a success message
            save_success = True
        else:
            # Move to next question
            request.session['current_question_index'] = current_question_index + 1
            return redirect('application_step2')

    total_questions = questions.count()
    progress = int((current_question_index / total_questions) * 100)

    return render(request, 'applications/question_form.html', {
        'application': application,
        'question': current_question,
        'answer': answer,
        'progress': progress,
        'current_step': current_question_index + 1,
        'total_steps': total_questions,
        'save_success': save_success
    })

@login_required
def application_success(request):
    return render(request, 'applications/application_success.html')

def get_available_chapters(date_join, date_leave):
    chapters = Chapter.objects.all()
    chapters_with_availability = []
    
    for chapter in chapters:
        # Check if there are any overlapping bookings
        overlapping_bookings = ChapterBooking.objects.filter(
            chapter=chapter,
            end_date__gt=date_join,
            start_date__lt=date_leave
        ).exists()
        
        chapters_with_availability.append({
            'chapter': chapter,
            'is_available': not overlapping_bookings
        })
    
    return chapters_with_availability

@login_required
def edit_application(request, pk):
    print("\n=== Starting edit_application view ===")
    print(f"Request method: {request.method}")
    print(f"POST data: {request.POST}")
    print(f"Session data before: {dict(request.session)}")
    
    application = get_object_or_404(Application, pk=pk, created_by=request.user)
    print(f"Found application: {application.pk}")
    print(f"Current application status: {application.status}")
    print(f"Current chapter: {application.chapter_id if application.chapter_id else 'None'}")
    
    if not application.is_editable:
        messages.error(request, "This application has already been submitted and cannot be edited.")
        return redirect('application_detail', pk=application.pk)
    
    # Store application ID in session to maintain connection between modes
    request.session['application_id'] = application.pk
    print(f"Stored application_id in session: {application.pk}")
    
    # Get the short stay warning message and pricing settings
    short_stay_message = ShortStayWarning.get_active()
    pricing_settings = PricingSettings.get_settings().get_formatted_texts()
    
    # Check if we're in question editing mode
    edit_questions = request.session.get('edit_questions', False)
    print(f"Edit questions mode: {edit_questions}")
    
    if edit_questions:
        print("\n=== Processing question editing mode ===")
        # Add support for reintroduction questions
        if application.member_type == 'returning member' and application.wants_reintroduction:
            reintro_questions = list(ReintroductionQuestion.objects.filter(is_active=True).order_by('order'))
            reintro_answers = {a.question_id: a for a in ReintroductionAnswer.objects.filter(application=application) if a.answer}
            last_answered_index = 0
            for idx, q in enumerate(reintro_questions):
                if q.id in reintro_answers:
                    last_answered_index = idx
            request.session['current_reintroduction_question_index'] = last_answered_index
            return redirect('reintroduction_form')
        elif application.member_type == 'returning member':
            # For returning members who don't want reintroduction, go back to reintroduction question
            return redirect('reintroduction_question')
        else:
            # Regular questions logic for new members
            questions = Question.objects.filter(is_active=True).order_by('order')
            answers = ApplicationAnswer.objects.filter(application=application)
            answered_question_ids = set(a.question_id for a in answers)
            first_unanswered_index = 0
            for idx, q in enumerate(questions):
                if q.id not in answered_question_ids or not answers.filter(question=q, answer__isnull=False).exists():
                    first_unanswered_index = idx
                    break
            else:
                first_unanswered_index = questions.count() - 1 if questions.exists() else 0
            request.session['current_question_index'] = first_unanswered_index
            return redirect('application_step2')
    
    # Handle the chapter selection and basic info editing
    if request.method == 'POST':
        print("\n=== Processing POST request for chapter selection ===")
        print(f"POST data: {request.POST}")
        form = ApplicationEditForm(request.POST, instance=application)
        
        if form.is_valid():
            print("Form is valid")
            date_join = form.cleaned_data['date_join']
            date_leave = form.cleaned_data['date_leave']
            print(f"Dates: {date_join} to {date_leave}")

            # Save the form data but don't commit yet
            application = form.save(commit=False)
            
            # If just checking availability
            if 'check_availability' in request.POST:
                print("Checking chapter availability")
                # Save any answers that were provided
                for field_name, value in form.cleaned_data.items():
                    if field_name.startswith('question_'):
                        question_id = int(field_name.split('_')[1])
                        question = Question.objects.get(id=question_id)
                        if value:  # Only save if an answer was provided
                            ApplicationAnswer.objects.update_or_create(
                                application=application,
                                question=question,
                                defaults={'answer': value}
                            )
                
                # Save the application with updated dates
                application.date_join = date_join
                application.date_leave = date_leave
                application.save()
                print(f"Saved application with dates: {date_join} to {date_leave}")
                
                chapters_with_availability = get_available_chapters(date_join, date_leave)
                nights = (date_leave - date_join).days
                
                chapters_info = []
                for chapter_data in chapters_with_availability:
                    chapter = chapter_data['chapter']
                    print(f"Processing chapter: {chapter.name} (Available: {chapter_data['is_available']})")
                    temp_application = Application(
                        chapter=chapter,
                        date_join=date_join,
                        date_leave=date_leave,
                        member_type=form.cleaned_data['member_type'],
                        guests=form.cleaned_data['guests']
                    )
                    total_cost = temp_application.calculate_cost()
                    per_guest_cost = round(total_cost / 2, 2) if form.cleaned_data['guests'] == '2' else None
                    
                    # Get pricing breakdown for this chapter
                    pricing_breakdown = temp_application.get_pricing_breakdown()
                    
                    # Check if short-term pricing is being used
                    is_short_term = (chapter.use_short_term_pricing and 
                                    nights <= chapter.short_term_threshold_days and 
                                    chapter.short_term_price_per_night > 0)
                    
                    chapters_info.append({
                        'chapter': chapter,
                        'is_available': chapter_data['is_available'],
                        'nightly_rate': chapter.get_display_rate_per_night(nights),
                        'total_cost': total_cost,
                        'per_guest_cost': per_guest_cost,
                        'nights': nights,
                        'images': chapter.images.all(),
                        'pricing_breakdown': pricing_breakdown,
                        'is_short_term': is_short_term
                    })

                print(f"Rendering chapter selection with {len(chapters_info)} chapters")
                return render(request, 'applications/new_application.html', {
                    'form': form,
                    'application': application,
                    'chapters_info': chapters_info,
                    'dates_selected': True,
                    'short_stay_message': short_stay_message,
                    'pricing_settings': pricing_settings,
                    'is_edit': True
                })
            
            # If continuing to questions
            elif request.POST.get('action') == 'continue_to_questions':
                print("\n=== Continuing to questions ===")
                # Save any answers that were provided
                for field_name, value in form.cleaned_data.items():
                    if field_name.startswith('question_'):
                        question_id = int(field_name.split('_')[1])
                        question = Question.objects.get(id=question_id)
                        if value:  # Only save if an answer was provided
                            ApplicationAnswer.objects.update_or_create(
                                application=application,
                                question=question,
                                defaults={'answer': value}
                            )
                
                # Get selected chapter
                chapter_id = request.POST.get('chapter')
                print(f"Selected chapter ID: {chapter_id}")
                
                if chapter_id:
                    application.chapter_id = chapter_id
                
                # Save the application with all updates including dates
                application.date_join = date_join
                application.date_leave = date_leave
                application.save()
                print(f"Saved application with dates: {date_join} to {date_leave}")
                
                # Set up session for question editing
                request.session['edit_questions'] = True
                request.session['current_question_index'] = 0
                request.session['application_id'] = application.pk
                print("Session updated for questions:")
                print(f"edit_questions: {request.session.get('edit_questions')}")
                print(f"current_question_index: {request.session.get('current_question_index')}")
                print(f"application_id: {request.session.get('application_id')}")
                
                # Check if this is a returning member and redirect to reintroduction question
                if application.member_type == 'returning member':
                    return redirect('reintroduction_question')
                else:
                    # Redirect to application_step2
                    print("Redirecting to application_step2")
                    return redirect('application_step2')
        else:
            print(f"Form validation failed: {form.errors}")
            return render(request, 'applications/new_application.html', {
                'form': form,
                'application': application,
                'chapters_info': [],
                'dates_selected': False,
                'short_stay_message': short_stay_message,
                'pricing_settings': pricing_settings,
                'is_edit': True
            })
    else:
        print("\n=== Initial GET request ===")
        # Clear any existing question editing session data
        if 'edit_questions' in request.session:
            del request.session['edit_questions']
        if 'current_question_index' in request.session:
            del request.session['current_question_index']
        print("Cleared existing question editing session data")
        
        form = ApplicationEditForm(instance=application)
    
    print("Rendering initial edit form")
    print(f"Final session state: {dict(request.session)}")
    return render(request, 'applications/new_application.html', {
        'form': form,
        'application': application,
        'chapters_info': [],
        'dates_selected': False,
        'short_stay_message': short_stay_message,
        'pricing_settings': pricing_settings,
        'is_edit': True
    })

@login_required
def withdraw_application(request, pk):
    application = get_object_or_404(Application, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        application.withdraw()
        return redirect('applications_list')
        
    return render(request, 'applications/withdraw_confirmation.html', {
        'application': application
    })

@login_required
def reintroduction_question(request):
    """Ask returning members if they want to reintroduce themselves."""
    application_id = request.session.get('application_id')
    if not application_id:
        return redirect('applications')
    
    application = get_object_or_404(Application, id=application_id, created_by=request.user)
    
    # Only returning members should see this page
    if application.member_type != 'returning member':
        return redirect('application_step2')
    
    # Get the admin-configurable settings
    settings = ReintroductionQuestionSettings.get_active()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Handle back to chapter selection
        if action == 'back_to_chapter':
            # Reset wants_reintroduction so they can choose again
            application.wants_reintroduction = None
            application.save()
            return redirect('application_edit', pk=application.pk)
        
        wants_reintroduction = request.POST.get('wants_reintroduction')
        
        if wants_reintroduction == 'yes':
            application.wants_reintroduction = True
            application.save()
            return redirect('reintroduction_form')
        elif wants_reintroduction == 'no':
            application.wants_reintroduction = False
            application.status = 'Submitted'
            application.save()
            # Clear session data and submit directly
            if 'application_id' in request.session:
                del request.session['application_id']
            return redirect('application_success')
    
    return render(request, 'applications/reintroduction_question.html', {
        'application': application,
        'settings': settings
    })

@login_required
def reintroduction_form(request):
    """Handle the reintroduction form for returning members."""
    application_id = request.session.get('application_id')
    if not application_id:
        return redirect('applications')
    
    application = get_object_or_404(Application, id=application_id, created_by=request.user)
    
    # Only returning members who want reintroduction should see this page
    if application.member_type != 'returning member' or not application.wants_reintroduction:
        return redirect('application_step2')
    
    # Get all active reintroduction questions ordered by their order field
    questions = ReintroductionQuestion.objects.filter(is_active=True).order_by('order')
    
    # If there are no reintroduction questions, submit directly
    if not questions.exists():
        if 'current_reintroduction_question_index' in request.session:
            del request.session['current_reintroduction_question_index']
        if 'application_id' in request.session:
            del request.session['application_id']
        application.reintroduction_completed = True
        application.status = 'Submitted'
        application.save()
        return redirect('application_success')
    
    # Get current question index from session or default to 0
    current_question_index = request.session.get('current_reintroduction_question_index', 0)
    
    # If we've answered all reintroduction questions, mark as completed and submit the application
    if current_question_index >= questions.count():
        if 'current_reintroduction_question_index' in request.session:
            del request.session['current_reintroduction_question_index']
        if 'application_id' in request.session:
            del request.session['application_id']
        application.reintroduction_completed = True
        application.status = 'Submitted'
        application.save()
        return redirect('application_success')
    
    current_question = questions[current_question_index]
    
    # Get the answer for this question if it exists for this specific application
    try:
        answer = ReintroductionAnswer.objects.get(
            application=application,
            question=current_question
        )
    except ReintroductionAnswer.DoesNotExist:
        # For new applications, create a blank answer
        answer = ReintroductionAnswer.objects.create(
            application=application,
            question=current_question,
            answer=''
        )

    total_questions = questions.count()
    progress = int((current_question_index / total_questions) * 100) if total_questions else 0

    save_success = False
    if request.method == 'POST':
        action = request.POST.get('action', 'next')

        if action == 'save':
            answer_text = request.POST.get('answer')
            if answer_text is not None:
                answer.answer = answer_text
                answer.save()
            save_success = True
            return render(request, 'applications/reintroduction_form.html', {
                'application': application,
                'question': current_question,
                'answer': answer,
                'progress': progress,
                'current_step': current_question_index + 1,
                'total_steps': total_questions,
                'save_success': save_success
            })

        # Handle back to reintroduction question (Yes/No choice)
        if action == 'back_to_reintroduction_question':
            # Save the current answer only if provided (don't require it)
            answer_text = request.POST.get('answer')
            if answer_text:
                answer.answer = answer_text
                answer.save()
            
            # Clear reintroduction session data
            if 'current_reintroduction_question_index' in request.session:
                del request.session['current_reintroduction_question_index']
            return redirect('reintroduction_question')
        
        # Handle back to chapter selection
        if action == 'back_to_chapter':
            # Save the current answer only if provided (don't require it)
            answer_text = request.POST.get('answer')
            if answer_text:
                answer.answer = answer_text
                answer.save()
            
            # Clear reintroduction session data
            if 'current_reintroduction_question_index' in request.session:
                del request.session['current_reintroduction_question_index']
            # Reset wants_reintroduction so they can choose again
            application.wants_reintroduction = None
            application.save()
            return redirect('application_edit', pk=application.pk)
        
        if action == 'previous':
            # Save the current answer only if provided (don't require it for going back)
            answer_text = request.POST.get('answer')
            if answer_text:
                answer.answer = answer_text
                answer.save()
            
            # Move to previous question
            request.session['current_reintroduction_question_index'] = max(0, current_question_index - 1)
        else:
            # Save the current answer for next/submit actions
            answer_text = request.POST.get('answer')
            if answer_text:
                answer.answer = answer_text
                answer.save()
            
            # Move to next question
            request.session['current_reintroduction_question_index'] = current_question_index + 1
        
        if action != 'save':
            return redirect('reintroduction_form')

    return render(request, 'applications/reintroduction_form.html', {
        'application': application,
        'question': current_question,
        'answer': answer,
        'progress': progress,
        'current_step': current_question_index + 1,
        'total_steps': total_questions,
        'save_success': save_success
    })

@login_required
def availability_matrix(request):
    """
    Display a matrix showing chapter availability across dates.
    Dates are shown as columns, chapters as rows.
    """
    # Get date range - default to next 30 days
    start_date = request.GET.get('start_date')
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = date.today()
    
    # Default to showing 30 days
    days_to_show = int(request.GET.get('days', 30))
    end_date = start_date + timedelta(days=days_to_show - 1)
    
    # Generate date range
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        current_date += timedelta(days=1)
    
    # Get all chapters
    chapters = Chapter.objects.all()
    
    # Build availability matrix
    matrix_data = []
    for chapter in chapters:
        row_data = {
            'chapter': chapter,
            'dates': []
        }
        
        for single_date in date_range:
            # Check if chapter is booked on this date
            is_booked = ChapterBooking.objects.filter(
                chapter=chapter,
                start_date__lte=single_date,
                end_date__gt=single_date
            ).exists()
            
            row_data['dates'].append({
                'date': single_date,
                'is_available': not is_booked,
                'is_booked': is_booked
            })
        
        matrix_data.append(row_data)
    
    # Navigation dates
    prev_start = start_date - timedelta(days=days_to_show)
    next_start = start_date + timedelta(days=days_to_show)
    
    context = {
        'matrix_data': matrix_data,
        'date_range': date_range,
        'start_date': start_date,
        'end_date': end_date,
        'days_to_show': days_to_show,
        'prev_start': prev_start,
        'next_start': next_start,
    }
    
    return render(request, 'applications/availability_matrix.html', context)