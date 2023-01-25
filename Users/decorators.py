from django.http import HttpResponse
from django.shortcuts import redirect


def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            
            group = None
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name
                
            if group in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse('You are not authorized to view this page')
                
        return wrapper_func
    return decorator


def unauthenticate_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.groups.filter(name='Admin').exists():
                return redirect('admin_dashboard')
            elif request.user.groups.filter(name='Panel').exists():
                return redirect('panel_dashboard')
            elif request.user.groups.filter(name='Student').exists():
                return redirect('student_dashboard')
        else:
            return view_func(request, *args, **kwargs)
        
    return wrapper_func
