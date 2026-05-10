from django.contrib import admin

from .models import Escola, FolhaAlteracao, FolhaExclusao, FolhaPdf, Frequencia, PerfilUsuario, Servidor, ServidorObservacao, TransferenciaServidor


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
    list_display = ('nome', 'cpf', 'escola', 'cargo', 'vinculo', 'ativo', 'motivo_inativo', 'licenca_tipo', 'licenca_inicio', 'licenca_fim')
    list_filter = ('escola', 'cargo', 'vinculo', 'ativo', 'motivo_inativo', 'licenca_tipo')
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


@admin.register(FolhaAlteracao)
class FolhaAlteracaoAdmin(admin.ModelAdmin):
    list_display = ('servidor', 'escola', 'mes', 'ano', 'campo', 'valor_anterior', 'valor_novo', 'usuario', 'criado_em')
    list_filter = ('ano', 'mes', 'escola', 'campo')
    search_fields = ('servidor__nome', 'escola__nome', 'valor_anterior', 'valor_novo')
    autocomplete_fields = ('escola', 'servidor', 'usuario')


@admin.register(FolhaExclusao)
class FolhaExclusaoAdmin(admin.ModelAdmin):
    list_display = ('servidor', 'mes', 'ano', 'motivo', 'criado_por', 'criado_em')
    list_filter = ('ano', 'mes', 'servidor__escola')
    search_fields = ('servidor__nome', 'motivo')
    autocomplete_fields = ('servidor', 'criado_por')


@admin.register(ServidorObservacao)
class ServidorObservacaoAdmin(admin.ModelAdmin):
    list_display = ('servidor', 'criado_por', 'criado_em')
    list_filter = ('servidor__escola', 'criado_em')
    search_fields = ('servidor__nome', 'texto')
    autocomplete_fields = ('servidor', 'criado_por')


@admin.register(TransferenciaServidor)
class TransferenciaServidorAdmin(admin.ModelAdmin):
    list_display = ('servidor', 'escola_origem', 'escola_destino', 'status', 'criado_em', 'respondido_em')
    list_filter = ('status', 'escola_origem', 'escola_destino')
    search_fields = ('servidor__nome', 'escola_origem__nome', 'escola_destino__nome')
    autocomplete_fields = ('servidor', 'escola_origem', 'escola_destino', 'solicitado_por', 'respondido_por')
