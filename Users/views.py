from sklearn.feature_extraction.text import TfidfVectorizer
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.contrib import messages
from .forms import *
from django.contrib.auth.models import AbstractUser
from .models import *
import pandas as pd
from .functions import *
import logging
from django.conf import settings
import numpy as np
import PyPDF2
import os
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.static import serve
from .decorators import *
from datetime import datetime

#FOR EMAIL VERIFICATION
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage

from .tokens import account_activation_token

logger = logging.getLogger(__name__)

#EMAIL ACTIVATION
def activateEmail(request, user, to_email):
    mail_subject = 'Activate your user account.'
    message = render_to_string('template_activation_account.html', {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(request, f'Dear {user}, thank you for registering! To complete the registration process, please check your email at {to_email} and click on the activation link to confirm your account. If you cannot find the email in your inbox, please check your spam folder as well. Thank you!')

        # messages.success(request, f'Dear <b> {user} </b>, please go to you email <b> {to_email} </b> inbox and click on \
        #     received activation link to confirm and complete the registration. <b>Note:</b> Check your spam folder.')
    else:
        messages.error(request, f'Problem sending confirmation email to {to_email}, check if you typed it correctly.')

def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        
        messages.success(request, 'Thank you for your email confirmation. Now you can login your account.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid!')
        return redirect('login')

# ACCOUNT LOGIN
@unauthenticate_user
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.groups.filter(name='Admin').exists():
                return redirect('admin_dashboard')
            elif user.groups.filter(name='Panel').exists():
                return redirect('panel_dashboard')
            elif user.groups.filter(name='Student').exists():
                print('Redirecting to student dashboard...')  # Debugging line
                return redirect('student_dashboard')
        else:
            return render(request, 'login/login.html', {'error_message': 'Invalid login credentials'})
    else:
        print('Rendering login form...')  # Debugging line
        return render(request, 'login/login.html')

# ACCOUNT LOGOUT


def logout_view(request):
    logout(request)
    return redirect('login')

# ADMIN DASHBOARD


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def admin_dashboard(request):
    # students
    students = StudentUsers.objects.all()
    total_students_enrolled = students.count()

    reg_students = User.objects.filter(group='Student')
    total_reg_students = reg_students.count()

    reg_panel = User.objects.filter(group='Panel')
    total_reg_panel = reg_panel.count()

    reg_admin = User.objects.filter(group='Admin')
    total_reg_admin = reg_admin.count()

    # repository
    repository = RepositoryFiles.objects.all()
    total_repository = repository.count()

    # uploaded docs
    docs = UploadDocuments.objects.all()
    total_docs = docs.count()

    status_rejected = UploadDocuments.objects.filter(status='REJECTED')
    total_rejected = status_rejected.count()
    status_approved = UploadDocuments.objects.filter(status='APPROVED')
    total_approved = status_approved.count()

    context = {
        "repository": repository,
        "total_repository": total_repository,
        "students": students,
        "total_students_enrolled": total_students_enrolled,
        "docs": docs,
        "total_docs": total_docs,
        "status_rejected": status_rejected,
        "total_rejected": total_rejected,
        "status_approved": status_approved,
        "total_approved": total_approved,
        "reg_students": reg_students,
        "total_reg_students": total_reg_students,
        "reg_admin": reg_admin,
        "total_reg_admin": total_reg_admin,
        "reg_panel": reg_panel,
        "total_reg_panel": total_reg_panel,
    }
    return render(request, "accounts/admin/admin_dashboard/data_visualization/charts.html", context)

# ADMIN REGISTER


@unauthenticate_user
def admin_register(request):
    if request.method == 'POST':
        form = AdminUsersForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                context = {'form': form, 'error': 'Email already exists.'}
                return render(request, 'accounts/admin/admin_registration/admin_register.html', context)
            except User.DoesNotExist:
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                username = form.cleaned_data['username']

                user = User.objects.create_user(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    password=password,
                    email=email,
                    group='Admin'
                )
                user.is_active = False
                user.save()
                group, created = Group.objects.get_or_create(name='Admin')
                group.user_set.add(user)

                admin = Admin(user=user)
                admin.save()
                activateEmail(request, user, form.cleaned_data.get('email'))
                return redirect('admin_register')
    else:
        form = AdminUsersForm()
    return render(request, 'accounts/admin/admin_registration/admin_register.html', {'form': form})

# ADMIN ADD FILES FOR REPOSITORY


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def AddRepositoryFiles(request):
    if request.method == "POST":
        form = RepositoryForm(request.POST, request.FILES)
        if form.is_valid():
            repository_file = form.save(commit=False)  # save the form and get the instance
            repository_file.user = request.user  # add the user to the instance
            repository_file.save()
            pdf_file = request.FILES['pdf_file']
            try:
                # pass the repository_file object to the function
                extract_pdf_text(pdf_file, repository_file)
                logger.info(
                    f"Successfully extracted text from PDF file {pdf_file} and saved it to a .txt file")
                return redirect("TableRepository")
            except Exception as e:
                logger.error(f"Error extracting text from PDF file: {e}")
                pass
    else:
        form = RepositoryForm()
    return render(request, "accounts/admin/admin_dashboard/repository/add_files_repository.html", {"form": form})



# ADMIN EDIT FILES FOR REPOSITORY


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def EditRepositoryFiles(request, id):
    repository = RepositoryFiles.objects.get(id=id)

    if request.method == "POST":
        # Update the task with the new data
        form = RepositoryForm(request.POST, instance=repository)
        if form.is_valid():
            task = form.save(commit=False)
            task.save()
            return redirect("TableRepository")
    else:
        form = RepositoryForm(instance=task)
    return render(request, "accounts/admin/admin_dashboard/repository/edit_files_repository.html", {"form": form})

# ADMIN DELETE FILES IN REPOSITORY


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def DeleteRepositoryFiles(request, id):
    repository = RepositoryFiles.objects.get(id=id)
    repository.delete()
    return redirect("TableRepository")

# ADMIN STATUS TABLE


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def admin_status_approved(request):
    repository = RepositoryFiles.objects.all()
    total_repository = repository.count()
    students = StudentUsers.objects.all()
    total_students_enrolled = students.count()
    docs = UploadDocuments.objects.all()
    total_docs = docs.count()
    status_approved = UploadDocuments.objects.filter(status='APPROVED')
    total_approved = status_approved.count()
    status_rejected = UploadDocuments.objects.filter(status='REJECTED')
    total_rejected = status_rejected.count()

    context = {
        "total_repository": total_repository,
        "repository": repository,
        "students": students,
        "total_students_enrolled": total_students_enrolled,
        "docs": docs,
        "total_docs": total_docs,
        "status_approved": status_approved,
        "total_approved": total_approved,
        "status_rejected": status_rejected,
        "total_rejected": total_rejected
    }

    return render(request, 'accounts/admin/admin_dashboard/tables/table_status/table_approved.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def admin_status_rejected(request):
    repository = RepositoryFiles.objects.all()
    total_repository = repository.count()
    students = StudentUsers.objects.all()
    total_students_enrolled = students.count()
    docs = UploadDocuments.objects.all()
    total_docs = docs.count()
    status_rejected = UploadDocuments.objects.filter(status='REJECTED')
    total_rejected = status_rejected.count()
    status_approved = UploadDocuments.objects.filter(status='APPROVED')
    total_approved = status_approved.count()

    context = {
        "total_repository": total_repository,
        "repository": repository,
        "students": students,
        "total_students_enrolled": total_students_enrolled,
        "docs": docs,
        "total_docs": total_docs,
        "status_rejected": status_rejected,
        "total_rejected": total_rejected,
        "status_approved": status_approved,
        "total_approved": total_approved,
    }

    return render(request, 'accounts/admin/admin_dashboard/tables/table_status/table_rejected.html', context)

# ADMIN TABLE FOR REPOSITORY


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def TableRepository(request):
    repository = RepositoryFiles.objects.filter(description='repository')
    

    context = {
        "repository": repository,
    }

    return render(request, "accounts/admin/admin_dashboard/tables/table_repository/table_repository.html", context)

# ADMIN TABLE FOR REGISTERED STUDENTS


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def TableRegisteredStudents(request):
    try:
        student_group = Group.objects.get(name='Student')
    except Group.DoesNotExist:
        student_group = None

    if student_group is not None:
        registered_student = User.objects.filter(groups=student_group)
        user_docs = UploadDocuments.objects.filter(user__in=registered_student.values_list('id', flat=True))
        context = {
            "registered_student": registered_student,
            "user_docs": user_docs,
        }
    else:
        context = {}

    return render(request, "accounts/admin/admin_dashboard/tables/table_users/table_registered_students.html", context)


# ADMIN TABLE FOR REGISTERED PANELS
@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def TableRegisteredPanels(request):
    try:
        panel_group = Group.objects.get(name='Panel')
    except Group.DoesNotExist:
        panel_group = None

    if panel_group is not None:
        registered_panel = User.objects.filter(groups=panel_group)
        docs_updated_by = UploadDocuments.objects.filter(status_updated_by__in=registered_panel.values_list('id', flat=True))
        context = {
            "registered_panel": registered_panel,
            "docs_updated_by": docs_updated_by,
        }
    else:
        context = {}

    return render(request, "accounts/admin/admin_dashboard/tables/table_users/table_registered_panels.html", context)

# ADMIN TABLE FOR ENROLLED STUDENTS


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def TableEnrolledUsers(request):
    repository = RepositoryFiles.objects.all()
    students = StudentUsers.objects.all()
    total_students_enrolled = students.count()
    total_repository = repository.count()

    # documents
    docs = UploadDocuments.objects.all()
    total_docs = docs.count()

    status_rejected = UploadDocuments.objects.filter(status='REJECTED')
    total_rejected = status_rejected.count()
    status_approved = UploadDocuments.objects.filter(status='APPROVED')
    total_approved = status_approved.count()

    context = {
        "total_repository": total_repository,
        "repository": repository,
        "students": students,
        "total_students_enrolled": total_students_enrolled,
        "docs": docs,
        "total_docs": total_docs,
        "status_rejected": status_rejected,
        "total_rejected": total_rejected,
        "status_approved": status_approved,
        "total_approved": total_approved,
    }
    return render(request, "accounts/admin/admin_dashboard/tables/table_users/table_users.html", context)

# ADMIN TABLE FOR DOCUMENTS SIMILARITY - TITLES


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def TableTitle(request):
    repository = RepositoryFiles.objects.all()
    total_repository = repository.count()
    docs = UploadDocuments.objects.all()
    total_docs = docs.count()
    title_defense_documents = UploadDocuments.objects.filter(document_type='TITLE DEFENSE DOCUMENT')
    total_title_defense_documents = title_defense_documents.count()

    status_rejected = UploadDocuments.objects.filter(status='REJECTED')
    total_rejected = status_rejected.count()
    status_approved = UploadDocuments.objects.filter(status='APPROVED')
    total_approved = status_approved.count()

    context = {
        "total_repository": total_repository,
        "repository": repository,
        "docs": docs,
        "total_docs": total_docs,
        "total_title_defense_documents": total_title_defense_documents,
        "title_defense_documents": title_defense_documents,
        "status_rejected": status_rejected,
        "total_rejected": total_rejected,
        "status_approved": status_approved,
        "total_approved": total_approved,
    }
    return render(request, "accounts/admin/admin_dashboard/tables/table_docs/table_title.html", context)

# ADMIN TABLE FOR DOCUMENTS SIMILARITY - PROPOSALS


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def TableProposal(request):
    repository = RepositoryFiles.objects.all()
    total_repository = repository.count()
    docs = UploadDocuments.objects.all()
    total_docs = docs.count()
    proposal_defense_documents = UploadDocuments.objects.filter(document_type='PROPOSAL DEFENSE DOCUMENT')
    total_proposal_defense_documents = proposal_defense_documents.count()

    status_rejected = UploadDocuments.objects.filter(status='REJECTED')
    total_rejected = status_rejected.count()
    status_approved = UploadDocuments.objects.filter(status='APPROVED')
    total_approved = status_approved.count()

    context = {
        "total_repository": total_repository,
        "repository": repository,
        "docs": docs,
        "total_docs": total_docs,
        "total_proposal_defense_documents": total_proposal_defense_documents,
        "proposal_defense_documents": proposal_defense_documents,
        "status_rejected": status_rejected,
        "total_rejected": total_rejected,
        "status_approved": status_approved,
        "total_approved": total_approved,
    }
    return render(request, "accounts/admin/admin_dashboard/tables/table_docs/table_proposal.html", context)

# ADMIN TABLE FOR DOCUMENTS SIMILARITY - FINALS


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def TableFinal(request):
    repository = RepositoryFiles.objects.all()
    total_repository = repository.count()
    docs = UploadDocuments.objects.all()
    total_docs = docs.count()
    final_defense_documents = UploadDocuments.objects.filter(document_type='FINAL DEFENSE DOCUMENT')
    total_final_defense_documents = final_defense_documents.count()

    status_rejected = UploadDocuments.objects.filter(status='REJECTED')
    total_rejected = status_rejected.count()
    status_approved = UploadDocuments.objects.filter(status='APPROVED')
    total_approved = status_approved.count()

    context = {
        "total_repository": total_repository,
        "repository": repository,
        "docs": docs,
        "total_docs": total_docs,
        "total_final_defense_documents": total_final_defense_documents,
        "final_defense_documents": final_defense_documents,
        "status_rejected": status_rejected,
        "total_rejected": total_rejected,
        "status_approved": status_approved,
        "total_approved": total_approved,
    }
    return render(request, "accounts/admin/admin_dashboard/tables/table_docs/table_final.html", context)

# ADMIN UPLOAD FILE FOR ENROLLED STUDENTS


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def EnrolledStudentsExcel(request):
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["file"]
            # Handle the uploaded file
            csv_enrolled_students(file)
            return redirect("TableEnrolledUsers")
    else:
        form = StudentForm()
    return render(request, "accotuns/admin/admin_dashboard/tables/table_users/table_users.html", {"form": form})

# ADMIN EDIT ENROLLED STUDENTS DETAILS


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def EditStudentsDetails(request, id):
    students = StudentUsers.objects.get(id=id)

    if request.method == "POST":
        # Update the task with the new data
        form = EditStudentForm(request.POST, instance=students)
        if form.is_valid():
            form.save()
            return redirect("TableEnrolledUsers")
    else:
        form = EditStudentForm(instance=students)
    return render(request, "accounts/admin/admin_dashboard/enrolled_students/edit_enrolled_students.html", {"form": form})

# ADMIN VIEW ENROLLED STUDENTS DETAILS


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def ViewStudentDetails(request):
    students = StudentUsers.objects.all()
    context = {"students": students}
    return render(request, "accounts/admin/admin_dashboard/enrolled_students/view_enrolled_students.html", context)

# ADMIN DELETE ENROLLED STUDENTS DETAILS


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def DeleteEnrolledStudent(request, id):
    students = StudentUsers.objects.get(id=id)
    students.delete()
    return redirect("TableEnrolledUsers")

# ADMIN EDIT REGISTERED STUDENTS


def is_admin_or_student(user):
    return user.groups.filter(name__in=['Admin', 'Student']).exists()


@login_required
@user_passes_test(is_admin_or_student)
def EditRegisteredStudent(request, id):
    User = get_user_model()
    student = get_object_or_404(User, id=id)
    if request.method == 'POST':
        form = EditRegisteredStudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('TableRegisteredStudents')
        else:
            print(form.errors)
    else:
        form = EditRegisteredStudentForm(instance=student)
    return render(request, 'accounts/admin/admin_dashboard/registered_students/edit_registered_students.html', {'form': form})

# ADMIN DELETE REGISTERED STUDENTS DETAILS


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def DeleteRegisteredStudent(request, id):
    students = User.objects.get(id=id)
    students.delete()
    return redirect("TableRegisteredStudents")

# ADMIN ACCOUNT DETAILS


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def admin_details(request):
     #PROFILE PICTURE REQUEST METHOD
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES)
        if form.is_valid():
            admin_profiles = Admin.objects.get(user=request.user)
            admin_profiles.profile_picture = form.cleaned_data['profile_picture']
            admin_profiles.save()
            return redirect('admin_details')
    else:
        form = ProfilePictureForm()
        
    #SIMILARITY THRESHOLD REQUEST METHOD
    if request.method == 'POST':
        form = SimilarityThresholdForm(request.POST)
        if form.is_valid():
            similarity_threshold, created = SimilarityThreshold.objects.get_or_create(user=request.user)
            if not created:
                similarity_threshold.threshold = form.cleaned_data['threshold']
                similarity_threshold.save()
    else:
        form = SimilarityThresholdForm()
        
    admins = Admin.objects.filter(user=request.user)
    
    thresholds = SimilarityThreshold.objects.all().last()
    userrepo = RepositoryFiles.objects.filter(user=request.user)

    context = {
        "form": form,
        'admins': admins,
        "userrepo": userrepo,
        "thresholds": thresholds,
    }
    return render(request, 'accounts/admin/admin_dashboard/admin_details/settings.html', context)


def EditRegisteredPanel(request, id):
    if request.method == 'POST':
        panel_user = User.objects.get(id=id)
        form = EditRegisteredPanelForm(request.POST, instance=panel_user)
        if form.is_valid():
            form.save()
            return redirect('TableRegisteredPanels')
    else:
        panel_user = User.objects.get(id=id)
        form = PanelUsersForm(instance=panel_user)
    return render(request, 'accounts/admin/admin_dashboard/registered_panels/edit_registered_panels.html', {'form': form})


@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def DeleteRegisteredPanel(request, id):
    panels = User.objects.get(id=id)
    panels.delete()
    return redirect("TableRegisteredPanels")
#
#
#
# STUDENT DASHBOARD


@login_required(login_url='login')
@allowed_users(allowed_roles=['Student'])
def student_dashboard(request):
    repository = RepositoryFiles.objects.filter(description='repository')
    return render(
        request,
        "accounts/student/student_dashboard/student_repository/table_repository_student.html",
        {"repository": repository},
    )

# STUDENT SEARCH STUDENT ID


def search_student_id(request):
    if request.method == 'POST':
        student_id = request.POST.get('search')
        students = StudentUsers.objects.filter(Student_Id=student_id)
        if students:
            message = 'Searching is done, press the view result button'
        else:
            message = 'No results found'
        return render(request, 'accounts/student/student_registration/search_student_id.html', {'students': students, 'message': message})
    else:
        return render(request, 'accounts/student/student_registration/search_student_id.html')

# STUDENT REGISTER


def register_student(request):
    if request.method == 'POST':
        student_id = request.POST['student_id']
        email = request.POST['email']
        name = request.POST['student_name']
        username = request.POST['username']
        password = request.POST['password']
        
        # Check if the student already exists
        existing_user = User.objects.filter(student_id=student_id)
        if existing_user:
            # Raise a SweetAlert message
            context = {'error': 'The student is already registered', 'student_id': student_id}
            return render(request, 'accounts/student/student_registration/search_student_id.html', context)
        else:
            # Create a User instance
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                name=name,
                student_id=student_id,
                group='Student'
            )

            # Save the User instance
            user.save()

            # Create a Student instance
            student = Student(user=user, group='Student', student_id=student_id)

            # Save the Student instance
            student.save()

            # Add the student to the group
            group, created = Group.objects.get_or_create(name='Student')
            group.user_set.add(user)
            user.save()
            return redirect('login')
    else:
        form = StudentRegistrationForm()
    return render(request, 'accounts/student/student_registration/student_register.html', {'form': form})

# STUDENT UPLOAD DOCUMENT FOR SIMILARITY - TITLE
# Upload Title Defense


@login_required(login_url='login')
@allowed_users(allowed_roles=['Student'])
def upload_title_defense(request):
    nearest_neighbors = None
    if request.method == "POST":
        form = UploadDocumentsForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                title_user = form.save(commit=False)
                title_user.user = request.user
                title_user.document_type = "TITLE DEFENSE DOCUMENT"
                title_user.save()

                # extract the text from the student's PDF file
                student_title = form.cleaned_data['student_title']
                student_proponents = form.cleaned_data['student_proponents']
                student_pdf_file = form.cleaned_data["student_pdf_file"]
                adviser = form.cleaned_data["adviser"]
                school_year = form.cleaned_data["school_year"]

                
                vectorizer = TfidfVectorizer()
                all_docs = []
                for file in RepositoryFiles.objects.all().values('text_file', 'title','proponents','adviser','school_year'):
                    file_path = file['text_file']
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        all_docs.append(f.read())
                all_docs = [preprocess(text) for text in all_docs]
                vectorizer.fit(all_docs)
                k = 5
                user_id = request.user
                query_matrix = student_pdf_text(student_pdf_file, vectorizer)
                nearest_neighbors = vectorize(query_matrix, vectorizer, k, student_title, user_id)
                
                threshold = 0
                last_threshold = SimilarityThreshold.objects.all().last()
                if last_threshold:
                    threshold = last_threshold.threshold
                    
                for neighbor in nearest_neighbors:
                    # Retrieve the title, proponents, advisor and school_year fields from the RepositoryFiles model
                    repository_file = RepositoryFiles.objects.get(title=neighbor['title'])
                    neighbor['title'] = repository_file.title
                    neighbor['proponents'] = repository_file.proponents
                    neighbor['adviser'] = repository_file.adviser
                    neighbor['school_year'] = repository_file.school_year

                    # Save the data in the Documents model
                    document = Documents(
                        docs_title=neighbor['title'], 
                        title_similarity=neighbor['title_similarity'], 
                        content_similarity=neighbor['content_similarity'], 
                        uploaded_at=timezone.now(),
                        proponents=neighbor['proponents'],
                        adviser=neighbor['adviser'],
                        school_year=neighbor['school_year']
                    )
                    document.save()
                    title_user.most_similar_documents.add(document)
                    title_user.save()
                    
                    if neighbor['content_similarity'] > threshold:
                        title_user.threshold_result = "above threshold"
                        title_user.save()
                    else:
                        title_user.threshold_result = "below threshold"
                        title_user.save()
                
                if student_title and student_proponents and adviser and school_year and student_pdf_file :
                    repository_file = RepositoryFiles()
                    repository_file.title = student_title
                    repository_file.proponents = student_proponents
                    repository_file.adviser = adviser
                    repository_file.school_year = school_year
                    repository_file.student_pdf_file = student_pdf_file
                    repository_file.user = request.user
                    repository_file.description = "uploads"
                    extract_pdf_text(student_pdf_file, repository_file)
                    repository_file.save()
                else:
                    logger.info(f"Missing field values. Not able to save the RepositoryFiles.")
                
                context = {"form": form, "nearest_neighbors": nearest_neighbors, "student_title": student_title, "student_proponents": student_proponents}
            except Exception as e:
                logger.error(
                    f"Error comparing student's title PDF file to corpus: {e}")
                pass
    else:
        form = UploadDocumentsForm()
    return render(request, "accounts/student/student_dashboard/student_uploads/upload_title.html", {'form': form, 'nearest_neighbors': nearest_neighbors})

# STUDENT UPLOAD DOCUMENT FOR SIMILARITY - PROPOSAL


@login_required(login_url='login')
@allowed_users(allowed_roles=['Student'])
def upload_proposal_defense(request):
    nearest_neighbors = None
    if request.method == "POST":
        form = UploadDocumentsForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                proposal_user = form.save(commit=False)
                proposal_user.user = request.user
                proposal_user.document_type = "PROPOSAL DEFENSE DOCUMENT"
                proposal_user.save()

                # extract the text from the student's PDF file
                student_title = form.cleaned_data['student_title']
                student_proponents = form.cleaned_data['student_proponents']
                student_pdf_file = form.cleaned_data["student_pdf_file"]
                adviser = form.cleaned_data["adviser"]
                school_year = form.cleaned_data["school_year"]

                
                vectorizer = TfidfVectorizer()
                all_docs = []
                for file in RepositoryFiles.objects.all().values('text_file', 'title','proponents','adviser','school_year'):
                    file_path = file['text_file']
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        all_docs.append(f.read())
                all_docs = [preprocess(text) for text in all_docs]
                vectorizer.fit(all_docs)
                k = 5
                user_id = request.user
                query_matrix = student_pdf_text(student_pdf_file, vectorizer)
                nearest_neighbors = vectorize(query_matrix, vectorizer, k, student_title, user_id)
                
                threshold = 0
                last_threshold = SimilarityThreshold.objects.all().last()
                if last_threshold:
                    threshold = last_threshold.threshold
                    
                for neighbor in nearest_neighbors:
                    # Retrieve the title, proponents, advisor and school_year fields from the RepositoryFiles model
                    repository_file = RepositoryFiles.objects.get(title=neighbor['title'])
                    neighbor['title'] = repository_file.title
                    neighbor['proponents'] = repository_file.proponents
                    neighbor['adviser'] = repository_file.adviser
                    neighbor['school_year'] = repository_file.school_year

                    # Save the data in the Documents model
                    document = Documents(
                        docs_title=neighbor['title'], 
                        title_similarity=neighbor['title_similarity'], 
                        content_similarity=neighbor['content_similarity'], 
                        uploaded_at=timezone.now(),
                        proponents=neighbor['proponents'],
                        adviser=neighbor['adviser'],
                        school_year=neighbor['school_year']
                    )
                    document.save()
                    proposal_user.most_similar_documents.add(document)
                    proposal_user.save()
                    
                    if neighbor['content_similarity'] > threshold:
                        proposal_user.threshold_result = "above threshold"
                        proposal_user.save()
                    else:
                        proposal_user.threshold_result = "below threshold"
                        proposal_user.save()
                
                if student_title and student_proponents and adviser and school_year and student_pdf_file :
                    repository_file = RepositoryFiles()
                    repository_file.title = student_title
                    repository_file.proponents = student_proponents
                    repository_file.adviser = adviser
                    repository_file.school_year = school_year
                    repository_file.student_pdf_file = student_pdf_file
                    repository_file.user = request.user
                    repository_file.description = "uploads"
                    extract_pdf_text(student_pdf_file, repository_file)
                    repository_file.save()
                else:
                    logger.info(f"Missing field values. Not able to save the RepositoryFiles.")
                    
                context = {"form": form, "nearest_neighbors": nearest_neighbors,
                           "student_title": student_title, "student_proponents": student_proponents}
                return render(request, "accounts/student/student_dashboard/student_uploads/upload_proposal.html", context)
            except Exception as e:
                logger.error(
                    f"Error comparing student's PDF file to corpus: {e}")
                pass
    else:
        form = UploadDocumentsForm()
    return render(request, "accounts/student/student_dashboard/student_uploads/upload_proposal.html", {"form": form})

# STUDENT UPLOAD DOCUMENT FOR SIMILARITY - FINAL


@login_required(login_url='login')
@allowed_users(allowed_roles=['Student'])
def upload_final_defense(request):
    if request.method == "POST":
        form = UploadDocumentsForm(request.POST, request.FILES)
        if form.is_valid():
            final_user = form.save(commit=False)
            final_user.user = request.user
            final_user.document_type = "FINAL DEFENSE DOCUMENT"
            final_user.save()

            student_title = form.cleaned_data["student_title"]
            student_proponents = form.cleaned_data["student_proponents"]
            adviser = form.cleaned_data["adviser"]
            school_year = form.cleaned_data["school_year"]
            pdf_file = request.FILES['student_pdf_file']
            abstract = form.cleaned_data["abstract"]

            if student_title and student_proponents and adviser and school_year and pdf_file and abstract:
                repository_file = RepositoryFiles()
                repository_file.title = student_title
                repository_file.proponents = student_proponents
                repository_file.adviser = adviser
                repository_file.school_year = school_year
                repository_file.pdf_file = pdf_file
                repository_file.abstract = abstract
                repository_file.user = request.user
                repository_file.description = "repository"
                extract_pdf_text(pdf_file, repository_file)
                repository_file.save()
                logger.info(
                    f"Successfully extracted text from PDF file {pdf_file} and saved it to a .txt file")
                return redirect("student_dashboard")
            else:
                logger.info(
                    f"Missing field values. Not able to save the RepositoryFiles.")
    else:
        form = UploadDocumentsForm()
    return render(request, "accounts/student/student_dashboard/student_uploads/upload_final.html", {"form": form})

# STUDENT VIEW UPLOADED FILES


@login_required(login_url='login')
@allowed_users(allowed_roles=['Student'])
def view_uploads(request):
    user = request.user
    uploads = UploadDocuments.objects.filter(user_id=user.id)
    return render(request, 'accounts/student/student_dashboard/uploads_result/uploads_result.html', {'uploads': uploads})

# STUDENT VIEW STUDENT DETAILS


@login_required(login_url='login')
@allowed_users(allowed_roles=['Student'])
def student_details(request):
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES)
        if form.is_valid():
            student_profiles = Student.objects.get(user=request.user)
            student_profiles.profile_picture = form.cleaned_data['profile_picture']
            student_profiles.save()
            return redirect('student_details')
    else:
        form = ProfilePictureForm()

    student_profiles = Student.objects.filter(user=request.user)
    students = StudentUsers.objects.filter(Student_Id=request.user.student_id)
    uploads = UploadDocuments.objects.filter(user=request.user)
    comparisons = DocumentComparison.objects.filter(user=request.user)
    context = {
        'student_profiles': student_profiles,
        'students': students,
        'uploads': uploads,
        'comparisons': comparisons,
        'form': form
    }
    return render(request, 'accounts/student/student_dashboard/student_details/settings.html', context)

#WORKING
# def student_details(request):
#     students = StudentUsers.objects.filter(Student_Id=request.user.student_id)
#     uploads = UploadDocuments.objects.filter(user=request.user)
#     comparisons = DocumentComparison.objects.filter(user=request.user)
#     context = {
#         'students': students,
#         'uploads': uploads,
#         'comparisons': comparisons
#     }
#     return render(request, 'accounts/student/student_dashboard/student_details/settings.html', context)

# STUDENT VIEW REPOSITORY FILES 
def view_pdf_repository(request, id):
    object = RepositoryFiles.objects.get(id=id)
    pdf_file = object.pdf_file.path
    pdf_file_date = os.path.getmtime(pdf_file)
    pdf_file_date = datetime.fromtimestamp(pdf_file_date)
    pdf_file_size = os.path.getsize(pdf_file)
    pdf_file_etag = f'"{pdf_file_size}-{int(pdf_file_date.timestamp())}"'
    response = FileResponse(open(pdf_file, 'rb'), content_type='application/pdf; inline=1')
    response['Content-Disposition'] = 'inline; filename="' + pdf_file + '"'
    response['Last-Modified'] = pdf_file_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
    response['ETag'] = pdf_file_etag
    response['Vary'] = 'User-Agent'
    return response

def view_abstract(request, id):
    abstracts = RepositoryFiles.objects.get(id=id)
    context = {
        "abstracts": abstracts
    }
    return render(request, 'accounts/student/student_dashboard/student_repository/abstract.html', context)

# def view_pdf_repository(request, id):
#     object = RepositoryFiles.objects.get(id=id)
#     pdf_file = object.pdf_file.path
#     with open(pdf_file, 'rb') as pdf:
#         response = FileResponse(open(pdf_file, 'rb'), content_type='application/pdf; inline=1')
#         response['Content-Disposition'] = 'inline; filename="' + pdf_file + '"'
#         response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#         response['Pragma'] = 'no-cache'
#         response['Expires'] = '0'
#     return response

# STUDENT DOCUMENT COMPARISON


@login_required(login_url='login')
@allowed_users(allowed_roles=['Student'])
def document_comparison(request):
    if request.method == "POST":
        form = DocumentComparisonForm(request.POST, request.FILES)
        if form.is_valid():
            comparison = form.save(commit=False)
            comparison.user = request.user
            comparison.save()
            print("Form is valid, comparison instance: ", comparison)  # Debugging statement
            try:
                 
                doc1_title = form.cleaned_data['doc1_title']
                doc1_proponents = form.cleaned_data['doc1_proponents']
                doc1 = request.FILES['doc1_pdf_file']
                
                doc2_title = form.cleaned_data['doc2_title']
                doc2_proponents = form.cleaned_data['doc2_proponents']
                doc2 = request.FILES['doc2_pdf_file']
                
                text1 = pdf_to_text(doc1)
                text2 = pdf_to_text(doc2)
                
                prep1 = preprocess(text1)
                prep2 = preprocess(text2)
                
                result = compare_documents(prep1, prep2)
                comparison.comparison_result = result
                comparison.save()
                context = {
                    "form": form,
                    "doc1_title": doc1_title,
                    "doc1_proponents": doc1_proponents,
                    "doc2_title": doc2_title,
                    "doc2_proponents": doc2_proponents,
                    "result": result,
                }
                return render(request,'accounts/student/student_dashboard/document_comparison/document_comparison.html', context)
            except Exception as e:
                print("Error saving form: ", e)  # Debugging statement
        else:
            print("Form is not valid, errors: ", form.errors)  # Debugging statement
    else:
        form = DocumentComparisonForm()
    return render(request, 'accounts/student/student_dashboard/document_comparison/document_comparison.html', {'form': form})


# PANEL DASHBOARD
@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def panel_dashboard(request):
    repository = RepositoryFiles.objects.filter(description='repository')
    context = {"repository": repository}
    return render(request, 'accounts/panel/panel_dashboard/table_repository/table_repository_panel.html', context)

# PANEL REGISTER
@unauthenticate_user
def panel_register(request):
    if request.method == 'POST':
        form = PanelUsersForm(request.POST)
        if form.is_valid():
            
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                context = {'form': form, 'error': 'Email already exists.'}
                return render(request, 'accounts/panel/panel_registration/panel_register.html', context)
            except User.DoesNotExist:
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                username = form.cleaned_data['username']

                user = User.objects.create_user(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    password=password,
                    email=email,
                    group='Panel'
                )
                user.is_active = False
                user.save()
                group, created = Group.objects.get_or_create(name='Panel')
                group.user_set.add(user)

                panel = Panel(user=user)
                panel.save()
                activateEmail(request, user, form.cleaned_data.get('email'))
                return redirect('panel_register')
    else:
        form = PanelUsersForm()
    return render(request, 'accounts/panel/panel_registration/panel_register.html', {'form': form})

# PANEL VIEW UPLOADED DOCUMENTS FOR SIMILARITY - TITLE


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def uploaded_title_docs(request):
    titles = UploadDocuments.objects.filter(document_type='TITLE DEFENSE DOCUMENT')
    # similar_docs = titles.most_similar_documents.all()
    context = {"titles": titles}
    return render(request, 'accounts/panel/panel_dashboard/table_docs/table_title.html', context)

# PANEL VIEW UPLOADED DOCUMENTS FOR SIMILARITY - PROPOSAL


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def uploaded_proposal_docs(request):
    proposals = UploadDocuments.objects.filter(document_type='PROPOSAL DEFENSE DOCUMENT')
    return render(request, 'accounts/panel/panel_dashboard/table_docs/table_proposal.html', {'proposals': proposals})

# PANEL VIEW UPLOADED DOCUMENTS FOR SIMILARITY - FINAL


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def uploaded_final_docs(request):
    finals = UploadDocuments.objects.filter(document_type='FINAL DEFENSE DOCUMENT')
    return render(request, 'accounts/panel/panel_dashboard/table_docs/table_final.html', {'finals': finals})

# PANEL STATUS DOCUMENTS - TITLE


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def approve_title(request, id):
    title = UploadDocuments.objects.get(id=id)
    title.status = "APPROVED"
    title.status_updated_at = timezone.now()
    title.status_updated_by = request.user
    title.save()
    return redirect('uploaded_title_docs')


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def reject_title(request, id):
    title = UploadDocuments.objects.get(id=id)
    title.status = "REJECTED"
    title.status_updated_at = timezone.now()
    title.status_updated_by = request.user
    title.save()
    return redirect('uploaded_title_docs')

# PANEL STATUS DOCUMENTS - PROPOSAL


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def approve_proposal(request, id):
    proposal = UploadDocuments.objects.get(id=id)
    proposal.status = "APPROVED"
    proposal.status_updated_at = timezone.now()
    proposal.status_updated_by = request.user
    proposal.save()
    return redirect('uploaded_proposal_docs')


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def reject_proposal(request, id):
    proposal = UploadDocuments.objects.get(id=id)
    proposal.status = "REJECTED"
    proposal.status_updated_at = timezone.now()
    proposal.status_updated_by = request.user
    proposal.save()
    return redirect('uploaded_proposal_docs')

# PANEL STATUS DOCUMENTS - FINAL


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def approve_final(request, id):
    final = UploadDocuments.objects.get(id=id)
    final.status = "APPROVED"
    final.status_updated_at = timezone.now()
    final.status_updated_by = request.user
    final.save()
    return redirect('uploaded_final_docs')


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def reject_final(request, id):
    final = UploadDocuments.objects.get(id=id)
    final.status = "REJECTED"
    final.status_updated_at = timezone.now()
    final.status_updated_by = request.user
    final.save()
    return redirect('uploaded_final_docs')

# PANEL COMMENTS DOCUMENTS - TITLE


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def comments_title(request, id):
    if request.method == "POST":
        title = UploadDocuments.objects.get(id=id)
        new_comment = Comment.objects.create(
            comment=request.POST.get("comments"),
            docs_defense=title
        )
        new_comment.save()
        new_comment.user.add(request.user)
        title.comments.add(new_comment)
        return redirect('uploaded_title_docs')
    else:
        messages.error(request, "Invalid request!")
        return redirect("uploaded_title_docs")


# PANEL COMMENTS DOCUMENTS - PROPOSAL
@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def comments_proposal(request, id):
    if request.method == "POST":
        proposal = UploadDocuments.objects.get(id=id)
        new_comment = Comment.objects.create(
            comment=request.POST.get("comments"),
            docs_defense=proposal
        )
        new_comment.save()
        new_comment.user.add(request.user)
        proposal.comments.add(new_comment)
        return redirect('uploaded_proposal_docs')
    else:
        messages.error(request, "Invalid request!")
        return redirect("uploaded_proposal_docs")

# PANEL COMMENTS DOCUMENTS - FINAL


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def comments_final(request, id):
    if request.method == "POST":
        final = UploadDocuments.objects.get(id=id)
        new_comment = Comment.objects.create(
            comment=request.POST.get("comments"),
            docs_defense=final
        )
        new_comment.save()
        new_comment.user.add(request.user)
        final.comments.add(new_comment)
        return redirect('uploaded_final_docs')
    else:
        messages.error(request, "Invalid request!")
        return redirect("uploaded_final_docs")

# PANEL STATUS TABLE


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def status_approved(request):
    status_approved = UploadDocuments.objects.filter(status='APPROVED')
    return render(request, 'accounts/panel/panel_dashboard/table_status/table_approved.html', {'status_approved': status_approved})


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def status_rejected(request):
    status_rejected = UploadDocuments.objects.filter(status='REJECTED')
    return render(request, 'accounts/panel/panel_dashboard/table_status/table_rejected.html', {'status_rejected': status_rejected})

# PANEL ACCOUNT DETAILS


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def panel_details(request):
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES)
        if form.is_valid():
            panel_profiles = Panel.objects.get(user=request.user)
            panel_profiles.profile_picture = form.cleaned_data['profile_picture']
            panel_profiles.save()
            return redirect('panel_details')
    else:
        form = ProfilePictureForm()
        
        
    panels = Panel.objects.filter(user=request.user)
    updated_by = UploadDocuments.objects.filter(status_updated_by=request.user)

    context = {'panels': panels, 'updated_by': updated_by}
    return render(request, 'accounts/panel/panel_dashboard/panel_details/settings.html', context)


def view_def_documents(request, id):
    object = UploadDocuments.objects.get(id=id)
    pdf_file = object.student_pdf_file.path
    pdf_file_date = os.path.getmtime(pdf_file)
    pdf_file_date = datetime.fromtimestamp(pdf_file_date)
    pdf_file_size = os.path.getsize(pdf_file)
    pdf_file_etag = f'"{pdf_file_size}-{int(pdf_file_date.timestamp())}"'
    response = FileResponse(open(pdf_file, 'rb'), content_type='application/pdf; inline=1')
    response['Content-Disposition'] = 'inline; filename="' + pdf_file + '"'
    response['Last-Modified'] = pdf_file_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
    response['ETag'] = pdf_file_etag
    response['Vary'] = 'User-Agent'
    return response


@login_required(login_url='login')
@allowed_users(allowed_roles=['Panel'])
def TableStudentsPanel(request):
    # add the views for the table registered users
    repository = RepositoryFiles.objects.all()
    students = StudentUsers.objects.all()
    total_students_enrolled = students.count()
    total_repository = repository.count()
    # documents
    docs = UploadDocuments.objects.all()
    total_docs = docs.count()

    student_group = Group.objects.get(name='Student')
    registered_student = User.objects.filter(groups=student_group)

    status_rejected = UploadDocuments.objects.filter(status='REJECTED')
    total_rejected = status_rejected.count()
    status_approved = UploadDocuments.objects.filter(status='APPROVED')
    total_approved = status_approved.count()

    user_docs = UploadDocuments.objects.filter(user__in=registered_student.values_list('id', flat=True))
    
    context = {
        "total_repository": total_repository,
        "repository": repository,
        "students": students,
        "total_students_enrolled": total_students_enrolled,
        "registered_student": registered_student,
        "docs": docs,
        "total_docs": total_docs,
        "status_rejected": status_rejected,
        "total_rejected": total_rejected,
        "status_approved": status_approved,
        "total_approved": total_approved,
        "user_docs": user_docs,
    }
    return render(request, "accounts/panel/panel_dashboard/table_students/table/table_registered_students.html", context)