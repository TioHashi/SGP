from django.contrib import admin

from .models import Escola, FolhaPdf, Frequencia, PerfilUsuario, Servidor, TransferenciaServidor


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
    list_display = ('nome', 'cpf', 'escola', 'cargo', 'vinculo', 'ativo', 'motivo_inativo')
    list_filter = ('escola', 'cargo', 'vinculo', 'ativo', 'motivo_inativo')
    search_fields = ('nome', 'cpf', 'rg', 'escola__nome')
    autocomplete_fields = ('escola',)


@admin.register(Frequencia)
class FrequenciaAdmin(admin.ModelAdmin):
    list_display = ('servidor', 'mes', 'ano', 'faltas', 'observacoes')
    list_filter = ('ano', 'mes', 'servidor__escola')
    search_fields = ('servidor__nome', 'servidor__cpf')
    autocomplete_fields = ('servidor',)


@admin.register(FolhaPdf)
class FolhaPdfAdmin(admin.ModelAdmin):
    list_display = ('nome_arquivo', 'escola', 'mes', 'ano', 'tamanho_bytes', 'criado_em')
    list_filter = ('ano', 'mes', 'escola')
    search_fields = ('nome_arquivo', 'storage_path', 'escola__nome')
    autocomplete_fields = ('escola', 'criado_por')


@admin.register(TransferenciaServidor)
class TransferenciaServidorAdmin(admin.ModelAdmin):
    list_display = ('servidor', 'escola_origem', 'escola_destino', 'status', 'criado_em', 'respondido_em')
    list_filter = ('status', 'escola_origem', 'escola_destino')
    search_fields = ('servidor__nome', 'escola_origem__nome', 'escola_destino__nome')
    autocomplete_fields = ('servidor', 'escola_origem', 'escola_destino', 'solicitado_por', 'respondido_por')
