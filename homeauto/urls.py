from django.urls import path
from . import views

urlpatterns = [
    path('', views.logs_page, name='logs_page'),
    path('dashboard/', views.dashboard_page, name='dashboard_page'),
    path('toggle_sensor/', views.toggle_sensor, name='toggle_sensor'),
    path('fetch_logs/<str:log_type>/', views.fetch_logs, name='fetch_logs'),
] 