from django.urls import path
from . import views

urlpatterns = [
    path('students/', views.students_list),
    path('teachers/', views.teachers_list), 
      
]