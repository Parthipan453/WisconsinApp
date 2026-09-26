"""
URL configuration for wisconsin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.decorators.cache import never_cache



# MOBILE APP APIs

from Admin.bela_admin.views import programs_api, interests_api


""" Dominic Code Start's """
@never_cache
def service_worker_view(request):
    sw_path = settings.BASE_DIR / 'static' / 'js' / 'sw.js'
    with open(sw_path, 'r') as f:
        content = f.read()
    response = HttpResponse(content, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response
""" Dominic Code End's """

urlpatterns = [
    path("admin/", admin.site.urls),

    # Dominic Code Start's
    path("sw.js", service_worker_view, name="service_worker"),
    # Dominic Code End's

      # Bela  - department URl
    path(
        'department/',
        include('Admin.bela_admin.urls')
    ),
    # Website URL
    path("", include("General.urls")),
    path("dashboard/", include("Admin.urls")),
    # Permission URL
    path("permission/", include("PermissionAccess.urls", namespace="Permission")),
    path("faculty/", include("Faculty.urls")),
    path("student/", include("Students.urls")),
    # Gayathri G - Faculty URL and Events URL
    path('events/', include('Events.urls')),
    path('staff/', include('Staff.urls')),

    # ================ Jordan code Start's Here ===============

    path('research/', include('Research.urls')),

    # ================ Jordan code End's Here ===============

    # Navina
    path("library/", include("Library.urls")),
    # Steve  - Colleges URL
    path("colleges/", include("Admin.Colleges.urls")),
  
    
    

    # rupa
    path('library/', include('Library.urls')),

    path('attendancestudent/', include('Students.Elsa.urls')),

    # ___Eric code___
    # applicants urls
    path("applicants/", include("Applicants.urls")),
    # ____Eric code end____
    
    path("medical/", include("Medical.urls")),

        
    # MOBILE APP APIs
    
    path('api/programs/', programs_api, name='api_programs'),
    path('api/interests/', interests_api, name='api_interests'),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)