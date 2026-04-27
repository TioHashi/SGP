"""
URL configuration for config project.

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
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from core.views import (
    dashboard,
    folha_mensal,
    folha_selecionar,
    relatorio_folha,
    relatorios,
    servidor_criar,
    servidor_editar,
    servidor_lista,
    servidor_transferir,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('servidores/', servidor_lista, name='servidor_lista'),
    path('servidores/novo/', servidor_criar, name='servidor_criar'),
    path('servidores/<int:pk>/editar/', servidor_editar, name='servidor_editar'),
    path('servidores/<int:pk>/transferir/', servidor_transferir, name='servidor_transferir'),
    path('folha/', folha_selecionar, name='folha_selecionar'),
    path('folha/<str:mes>/<str:ano>/', folha_mensal, name='folha_mensal'),
    path('relatorios/', relatorios, name='relatorios'),
    path('relatorios/folha/<str:mes>/<str:ano>/', relatorio_folha, name='relatorio_folha'),
]
