from django.contrib import admin
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Dashboard
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin_register/", views.admin_register, name="admin_register"),

    # DOCUMENT SIMILARITY DOCUMENTS URLS
    path("TableTitle/", views.TableTitle, name="TableTitle"),
    path("TableProposal/", views.TableProposal, name="TableProposal"),
    path("TableFinal/", views.TableFinal, name="TableFinal"),

    # repository
    path("AddRepositoryFiles/", views.AddRepositoryFiles,
         name="AddRepositoryFiles"),
    path("EditRepositoryFiles/<int:id>", views.EditRepositoryFiles),
    path("DeleteRepositoryFiles/<int:id>", views.DeleteRepositoryFiles),
    path("TableRepository/",
         views.TableRepository, name="TableRepository"),

    # status table
    path("admin_status_approved/", views.admin_status_approved,
         name="admin_status_approved"),
    path("admin_status_rejected/", views.admin_status_rejected,
         name="admin_status_rejected"),

    # enrolled students
    path("EnrolledStudentsExcel/", views.EnrolledStudentsExcel,
         name="EnrolledStudentsExcel"),
    path("EditStudentsDetails/<int:id>",
         views.EditStudentsDetails, name="EditStudentsDetails"),
    path("ViewStudentDetails/", views.ViewStudentDetails),
    path("DeleteEnrolledStudent/<int:id>", views.DeleteEnrolledStudent),
    path("TableEnrolledUsers/", views.TableEnrolledUsers,
         name="TableEnrolledUsers"),

    # registered student user
    path("TableRegisteredStudents/", views.TableRegisteredStudents,
         name="TableRegisteredStudents"),
    path("EditRegisteredStudent/<int:id>", views.EditRegisteredStudent),
    path("DeleteRegisteredStudent/<int:id>",
         views.DeleteRegisteredStudent, name="DeleteRegisteredStudent"),

    # admin view student details
    path("admin_details/", views.admin_details, name="admin_details"),


    # students
    path("student_dashboard/", views.student_dashboard,
         name="student_dashboard"),
    # upload student documents
    path("upload_title_defense/", views.upload_title_defense,
         name="upload_title_defense"),
    path("upload_proposal_defense/", views.upload_proposal_defense,
         name="upload_proposal_defense"),
    path("upload_final_defense/", views.upload_final_defense,
         name="upload_final_defense"),

    # document comparison
    path("document_comparison/", views.document_comparison,
         name="document_comparison"),

    # student view uploads
    path("view_uploads/", views.view_uploads, name="view_uploads"),

    # student view student details
    path("student_details/", views.student_details, name="student_details"),

    # student view repository pdf file
    path("view_pdf_repository/<int:id>",
         views.view_pdf_repository, name="view_pdf_repository"),
    
    # student view abstracts
        path('view_abstract/<int:id>', views.view_abstract, name='view_abstract'),

    # register student user
    path("search_student_id", views.search_student_id,
         name="search_student_id"),
    path("search_student_id/register_student",
         views.register_student, name="register_student"),
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # panel
    path("panel_dashboard/", views.panel_dashboard, name="panel_dashboard"),
    path("panel_register/", views.panel_register, name="panel_register"),
    path("uploaded_title_docs/", views.uploaded_title_docs,
         name="uploaded_title_docs"),
    path("uploaded_proposal_docs/", views.uploaded_proposal_docs,
         name="uploaded_proposal_docs"),
    path("uploaded_final_docs/", views.uploaded_final_docs,
         name="uploaded_final_docs"),
    path("TableRegisteredPanels/", views.TableRegisteredPanels,
         name="TableRegisteredPanels"),
    path("EditRegisteredPanel/<int:id>",
         views.EditRegisteredPanel, name="EditRegisteredPanel"),
    path("DeleteRegisteredPanel/<int:id>", views.DeleteRegisteredPanel),

    # panel status title
    path("approve_title/<int:id>", views.approve_title),
    path("reject_title/<int:id>", views.reject_title),

    # panel status proposal
    path("approve_proposal/<int:id>", views.approve_proposal),
    path("reject_proposal/<int:id>", views.reject_proposal),

    # panel status final
    path("approve_final/<int:id>", views.approve_final),
    path("reject_final/<int:id>", views.reject_final),

    # panel comments
    path("comments_title/<int:id>", views.comments_title),
    path("comments_proposal/<int:id>", views.comments_proposal),
    path("comments_final/<int:id>", views.comments_final),

    # panel status table
    path("status_approved/", views.status_approved, name="status_approved"),
    path("status_rejected/", views.status_rejected, name="status_rejected"),

    # panel view student details
    path("panel_details/", views.panel_details, name="panel_details"),

    # view uploaded documents
    path("view_def_documents/<int:id>",
         views.view_def_documents, name="view_def_documents"),
    
    #student table and view each uploads of the student
    path("TableStudentsPanel/", views.TableStudentsPanel, name="TableStudentsPanel"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
