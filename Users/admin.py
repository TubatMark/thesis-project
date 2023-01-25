from django.contrib import admin
from .models import *

#USERS
admin.site.register(StudentUsers),
admin.site.register(PanelUsers),

#UPLOAD DOCS BY STUDENTS
admin.site.register(UploadDocuments),

#STUDENT DASHBOARD
admin.site.register(RepositoryFiles),


