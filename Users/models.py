from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings

    
class User(AbstractUser):
    # Add a new field to the user model
    student_id = models.CharField(max_length=50)
    name = models.CharField(max_length=255, blank=True, null=True)
    group = models.CharField(max_length=50, blank=True, null=True)
    
            
#PANEL    
class Panel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to=os.path.join(settings.MEDIA_ROOT, 'profile_pictures/'), blank=True, null=True)
    
class PanelUsersManager(models.Manager):
    def create_user(self, first_name, last_name, email, password, panel, group):
        panel_user = self.create(
            first_name=first_name, 
            last_name=last_name,
            email=email,
            password=password,
            panel=panel,
            group=group
        )
        panel_user.save()
        return panel_user

class PanelUsers(models.Model):
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, null=True)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    group = models.CharField(max_length=50, blank=True, null=True)
    
    objects = PanelUsersManager()
    


#ADMIN
class RepositoryFiles(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=255)
    proponents = models.CharField(max_length=255)
    adviser = models.CharField(max_length=255, blank=True, null=True)
    school_year = models.CharField(max_length=255, blank=True, null=True)
    pdf_file = models.FileField(upload_to="RepositoryFiles/")
    text_file = models.CharField(max_length=255, blank=True, null=True)    
    
    class Meta:
        db_table = "db_repository"

        
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to=os.path.join(settings.MEDIA_ROOT, 'profile_pictures/'), blank=True, null=True)

class AdminUsersManager(models.Manager):
    def create_user(self, first_name, last_name, email, password, admin, group):
        admin_user = self.create(
            first_name=first_name, 
            last_name=last_name,
            email=email,
            password=password,
            admin=admin,
            group=group
        )
        admin_user.save()
        return admin_user

class AdminUsers(models.Model):
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, null=True)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    group = models.CharField(max_length=50, blank=True, null=True)
    
    objects = AdminUsersManager()
          

class StudentUsers(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    Student_Id = models.CharField(max_length=255)
    Student_Name = models.CharField(max_length=255)
    Email = models.EmailField()
    Contact_Number = models.CharField(max_length=20, null=True)
    Course = models.CharField(max_length=255)
    SUBJECT_CODE = models.CharField(max_length=255)
    SUBJECT_DESCRIPTION = models.CharField(max_length=255)
    YR_SEC = models.CharField(max_length=255)
    SEM = models.CharField(max_length=255)
    SY = models.CharField(max_length=255)

    class Meta:
        db_table = "user_enrolled_students"
        
class StudentUsersManager(models.Manager):
    def create_user(self, student_id, name, username, email, password, student, group):
        student_user = self.create(
            first_name=first_name, 
            last_name=last_name,
            name=name,
            email=email,
            password=password,
            student=student,
            group=group
        )
        student_user.save()
        return student_user

#STUDENT
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=255)
    group = models.CharField(max_length=50, blank=True, null=True)
    profile_picture = models.ImageField(upload_to=os.path.join(settings.MEDIA_ROOT, 'profile_pictures/'), blank=True, null=True)
    objects = StudentUsersManager()
        
#SYSTEM SIMILARITY REPORT
class Documents(models.Model):
    docs_title = models.CharField(max_length=255, blank=True, null=True)
    proponents = models.CharField(max_length=255, blank=True, null=True)
    adviser = models.CharField(max_length=255, blank=True, null=True)
    school_year = models.CharField(max_length=255, blank=True, null=True)
    similarity = models.FloatField(default=0.0)
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = "db_similarity_report"
    
#COMMENT ASSOCIATED WITH A LOT OF USERS
class Comment(models.Model):
    user = models.ManyToManyField(User)
    docs_defense = models.ForeignKey('UploadDocuments', on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    
#UPLOAD FILES FOR SIMILARITY TEST
class UploadDocuments(models.Model):
    DOCUMENT_TYPE_CHOICES = (
        ('TITLE', 'Title Defense'),
        ('PROPOSAL', 'Proposal Defense'),
        ('FINAL', 'Final Defense'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
    )
    student_title = models.CharField(max_length=255)
    student_proponents = models.CharField(max_length=255)
    student_pdf_file = models.FileField(upload_to="DefFiles/")
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    uploaded_at = models.DateTimeField(default=timezone.now)
    most_similar_documents = models.ManyToManyField(Documents, related_name='similar_to')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='TITLE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    comments = models.ManyToManyField(Comment, related_name='document_comments')
    adviser = models.CharField(max_length=255, blank=True, null=True)
    school_year = models.CharField(max_length=255, blank=True, null=True)
    status_updated_at = models.DateTimeField(auto_now=True)
    status_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='upload_doc_status_updated_by')
    
    class Meta:
         db_table = "db_upload_docs"
         

class DocumentComparison(models.Model):
    doc1_title = models.CharField(max_length=255)
    doc1_proponents = models.CharField(max_length=255)
    doc1_pdf_file = models.FileField(upload_to="ComparisonDocs/")
    doc2_title = models.CharField(max_length=255)
    doc2_proponents = models.CharField(max_length=255)
    doc2_pdf_file = models.FileField(upload_to="ComparisonDocs/")
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    comparison_result = models.FloatField(null=True)
    docs_uploaded_at = models.DateTimeField(auto_now=True)
    
    class Meta:
         db_table = "db_comparison_docs"


        