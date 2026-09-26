from django.urls import path
from . import views
from .views import *
from Admin.views import *

urlpatterns = [
    # Auth
    path("logout/", views.logout_view, name="logout"),
    path("login/", views.login_view, name="login"),  
    path("academics/", views.academics, name="academics"),
    path("about/", views.about, name="about"),
     path("majors/", views.majors, name="majors"),
     path("schools/", views.schools, name="schools"),
     


  
    
    # Website URL's
    # path('', website, name='home_page'),
    path('admissions/', admissions, name='admissions'),

    # path("login/", views.login_view, name="login"),   
    
    path('admissions/', views.admissions, name='admissions'),
    path('research/', views.research, name='research'),
    # Dashboards 
    path("dashboard/admin/<uuid:uuid>/", views.admin_dashboard, name="admin_dashboard"),
    path("faculty/dashboard/<uuid:uuid>/", views.faculty_dashboard, name="faculty_dashboard"),
    path("staff/dashboard/<uuid:uuid>/", views.staff_dashboard, name="staff_dashboard"),
    

    # Jack Urls Start
    path("medical/dashboard/<uuid:uuid>",  views.medical_dashboard, name="medical_dashboard"),
    # Jack Urls End

    #<-----------------Blaze code start---------------->

    # path('hostel-dashboard/<uuid:uuid>/', views.hostel_dashboard, name='hostel_dashboard'),

    #<-----------------Blaze code End---------------->


    # Website
    path("", views.website, name="home_page"),

    #student life style
    path('studentlifestyle/',views.student_lifestyle, name='studentlifestyle'),
    # Athletics
    path("athletics/",views.athletics,name="athletics"),
    
    # News
    path("news/",views.news_page,name="news_page"),
    path("campus_news/",views.campus_news,name="campus_news"),
    path("science_news/",views.science_news,name="science_news"),
    path("health_news/",views.health_news,name="health_news"),
    path("society_news/",views.society_news,name="society_news"),
    path("state_news/",views.state_news,name="state_news"),
    path("athletics/",views.athletics,name="athlete"),
    
    # news details
    path("news/<slug:slug>",views.expanded_news,name="expanded_news"),
    path("api/news/<slug:slug>/",views.get_newsarticle_data,name="get_newsarticle_data"),

    #Guide Speed 
    path("guide/", views.guide, name="guide"),

    path('actuarialscience/',views.actuarialscience,name="actuarialscience"),

     

    #Rixie code 
      path('accountingcourse/',views.accountingcourse,name='accountingcourse'),
    #Speed code 
     path('program-courses/', views.academic_course_details, name='academic_course_details'),
     path('course-designation/', views.course_designation_page, name='course_designation_page'),
     path('course-requisites/', views.course_requisites_page, name='course_requisites_page'),
     path('department/<slug:slug>/', views.acedemic_department_details, name='acedemic_department_details'),

    #Rixie code
     path('graduate-programs/',views.graduate_programs, name='graduate_programs'),
     path('graduate-page/',views.graduate_page, name='graduate_page'),
     path('academic_advise/',views.academic_advising,name='academic_advising'),
     path('domain_about/',views.academic_advising_about,name='academic_about'),
     path('domain_contact',views.academic_advising_contact,name='academic_contact'),
     path('findadvisor/',views.findadvisor,name='findadvisor'),
     path('student_searchandenroll/',views.student_searchandenroll,name='student_searchandenroll'),
     path('student_thirdsection/',views.student_thirdsection,name='student_thirdsection'),
     path('student_resources/',views.student_resources,name='student_resources'),
     path('depart_and_programs/',views.depart_and_programs,name='depart_and_programs'),
     path('student_fourthsection/',views.student_fourthsection,name='student_fourthsection'),
     path('prospective/',views.prospective,name='prospective'),
     path('leadership/',views.leadership_page,name='leadership'),
     path('explorefacts/',views.explore,name='explorepage'),
     path('meetleader/',views.meetleader,name='meetleader'),
     path('reg/',views.reghome,name='reghome'),
     path('transfercredit/',views.transfer,name='transfercredit'),
     path('coursecredit/',views.coursecreditevaluation,name='coursecredit'),
     path('testcredit/',views.testcredit,name='testcredit'),
]