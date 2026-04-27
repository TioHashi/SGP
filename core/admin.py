from django.contrib import admin

from .models import Escola, PerfilUsuario, Servidor


@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativa')
    list_filter = ('ativa',)
    search_fields = ('nome',)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'escola')
    list_filter = ('escola',)
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'escola__nome')
    autocomplete_fields = ('usuario', 'escola')


@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'escola', 'cargo', 'vinculo', 'ativo')
    list_filter = ('escola', 'cargo', 'vinculo', 'ativo')
    search_fields = ('nome', 'cpf', 'rg', 'escola__nome')
    autocomplete_fields = ('escola',)
