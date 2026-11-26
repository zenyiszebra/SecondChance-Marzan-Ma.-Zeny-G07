from django.urls import path

from . import views

app_name = 'pipeline'

urlpatterns = [
    path('', views.inmate_list, name='inmate_list'),
    path('inmates/new/', views.inmate_create, name='inmate_create'),
    path('inmates/<int:pk>/', views.inmate_detail, name='inmate_detail'),
    path('inmates/<int:pk>/edit/', views.inmate_edit, name='inmate_edit'),
    path('inmates/<int:pk>/delete/', views.inmate_delete, name='inmate_delete'),
    path('inmates/<int:inmate_pk>/progress/new/', views.progress_create, name='progress_create'),
    path('progress/<int:pk>/edit/', views.progress_edit, name='progress_edit'),
    path('progress/<int:pk>/delete/', views.progress_delete, name='progress_delete'),
]
