from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('setting/', views.setting, name="setting"),
    path('upload/', views.upload, name="upload"),
    path('save/', views.savesetting, name="save"),
]