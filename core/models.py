import calendar
from datetime import date

from django.conf import settings
from django.db import models


class Escola(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'escola'
        verbose_name_plural = 'escolas'

    def __str__(self):
        return self.nome


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    escola = models.ForeignKey(Escola, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        verbose_name = 'perfil de usuario'
        verbose_name_plural = 'perfis de usuario'

    def __str__(self):
        if self.escola:
            return f'{self.usuario.username} - {self.escola.nome}'
        return f'{self.usuario.username} - acesso geral'


class Servidor(models.Model):
    SEXO_CHOICES = [
        ('Masculino', 'Masculino'),
        ('Feminino', 'Feminino'),
        ('Nao Especificado', 'Nao Especificado'),
    ]

    ZONA_CHOICES = [
        ('Urbana', 'Zona Urbana'),
        ('Rural', 'Zona Rural'),
    ]

    ESCOLARIDADE_CHOICES = [
        ('Ensino Fundamental', 'Ensino Fundamental'),
        ('Ensino Medio', 'Ensino Medio'),
        ('Ensino Superior', 'Ensino Superior'),
    ]

    VINCULO_CHOICES = [
        ('Efetivo', 'Efetivo'),
        ('Temporario', 'Temporario'),
    ]

    CARGO_CHOICES = [
        ('Secretario(a)', 'Secretario(a)'),
        ('Secretaria de Educacao', 'Secretária de Educação'),
        ('Assistente Administrativo', 'Assistente Administrativo'),
        ('Auxiliar Administrativo', 'Auxiliar Administrativo'),
        ('ASG', 'ASG'),
        ('Coordenador(a)', 'Coordenador(a)'),
        ('Coordenador(a) Pedagogico', 'Coordenador(a) Pedagógico'),
        ('Coordenador(a) de Sistemas', 'Coordenador(a) de Sistemas'),
        ('Professor(a)', 'Professor(a)'),
        ('Vigia', 'Vigia'),
        ('Merendeira', 'Merendeira'),
        ('Monitor(a)', 'Monitor(a)'),
        ('Motorista', 'Motorista'),
        ('Diretor(a)', 'Diretor(a)'),
        ('Mediadora Social', 'Mediadora Social'),
    ]

    MOTIVO_INATIVO_CHOICES = [
        ('', ''),
        ('Licenca', 'Licença'),
        ('Aposentado', 'Aposentado'),
        ('Obito', 'Óbito'),
        ('Outros', 'Outros'),
    ]

    LICENCA_CHOICES = [
        ('', ''),
        ('LICENCA PREMIO', 'Licença prêmio'),
        ('LICENCA MATERNIDADE', 'Licença maternidade'),
        ('LICENCA PARA ESTUDO', 'Licença para estudo'),
    ]

    escola = models.ForeignKey(Escola, on_delete=models.PROTECT, related_name='servidores')
    nome = models.CharField(max_length=255, verbose_name='Nome completo')
    sexo = models.CharField(max_length=50, choices=SEXO_CHOICES, blank=True)
    rg = models.CharField(max_length=20, verbose_name='RG', blank=True)
    cpf = models.CharField(max_length=14, verbose_name='CPF', unique=True)
    data_nascimento = models.DateField(verbose_name='Data de nascimento', null=True, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    logradouro = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=20, verbose_name='Numero', blank=True)
    zona = models.CharField(max_length=20, choices=ZONA_CHOICES, blank=True)
    bairro = models.CharField(max_length=255, verbose_name='Bairro / Vila', blank=True)
    estado = models.CharField(max_length=50, blank=True)
    municipio = models.CharField(max_length=100, verbose_name='Municipio', blank=True)
    cep = models.CharField(max_length=9, verbose_name='CEP', blank=True)
    escolaridade = models.CharField(max_length=50, choices=ESCOLARIDADE_CHOICES, blank=True)
    formacao = models.CharField(max_length=255, verbose_name='Formacao', blank=True)
    instituicao = models.CharField(max_length=255, verbose_name='Instituicao', blank=True)
    funcao = models.CharField(max_length=100, verbose_name='Funcao', blank=True)
    cargo = models.CharField(max_length=100, choices=CARGO_CHOICES, blank=True)
    vinculo = models.CharField(max_length=100, verbose_name='Vinculo', choices=VINCULO_CHOICES, blank=True)
    carga_horaria = models.PositiveIntegerField(verbose_name='Carga horaria', null=True, blank=True)
    data_admissao = models.DateField(verbose_name='Data de admissao', null=True, blank=True)
    data_inicio = models.DateField(verbose_name='Data de inicio', null=True, blank=True)
    data_saida = models.DateField(verbose_name='Data de saida', null=True, blank=True)
    banco = models.CharField(max_length=100, blank=True)
    agencia = models.CharField(max_length=20, verbose_name='Agencia', blank=True)
    conta = models.CharField(max_length=20, blank=True)
    ativo = models.BooleanField(default=True)
    motivo_inativo = models.CharField(max_length=30, choices=MOTIVO_INATIVO_CHOICES, blank=True)
    licenca_tipo = models.CharField(max_length=40, choices=LICENCA_CHOICES, blank=True)
    licenca_inicio = models.DateField(null=True, blank=True)
    licenca_fim = models.DateField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'servidor'
        verbose_name_plural = 'servidores'

    def __str__(self):
        return self.nome

    def calcular_fim_licenca(self):
        meses = {
            'LICENCA PREMIO': 3,
            'LICENCA MATERNIDADE': 6,
        }.get(self.licenca_tipo)
        if not self.licenca_inicio or not meses:
            return None

        month = self.licenca_inicio.month - 1 + meses
        year = self.licenca_inicio.year + month // 12
        month = month % 12 + 1
        day = min(self.licenca_inicio.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)

    def save(self, *args, **kwargs):
        if self.licenca_tipo in {'LICENCA PREMIO', 'LICENCA MATERNIDADE'} and self.licenca_inicio:
            self.licenca_fim = self.calcular_fim_licenca()
        elif self.licenca_tipo == 'LICENCA PARA ESTUDO':
            self.licenca_fim = None
        elif not self.licenca_tipo:
            self.licenca_inicio = None
            self.licenca_fim = None
        super().save(*args, **kwargs)

    def em_licenca_no_periodo(self, mes, ano):
        if not self.licenca_tipo or not self.licenca_inicio:
            return False
        inicio_periodo = date(int(ano), int(mes), 1)
        fim_periodo = date(int(ano), int(mes), calendar.monthrange(int(ano), int(mes))[1])
        if self.licenca_fim:
            return self.licenca_inicio <= fim_periodo and self.licenca_fim >= inicio_periodo
        return self.licenca_inicio <= fim_periodo


class TransferenciaServidor(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aceita', 'Aceita'),
        ('recusada', 'Recusada'),
    ]

    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, related_name='transferencias')
    escola_origem = models.ForeignKey(Escola, on_delete=models.PROTECT, related_name='transferencias_enviadas')
    escola_destino = models.ForeignKey(Escola, on_delete=models.PROTECT, related_name='transferencias_recebidas')
    solicitado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencias_solicitadas')
    respondido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencias_respondidas')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pendente')
    criado_em = models.DateTimeField(auto_now_add=True)
    respondido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'transferência de servidor'
        verbose_name_plural = 'transferências de servidores'

    def __str__(self):
        return f'{self.servidor.nome}: {self.escola_origem.nome} -> {self.escola_destino.nome}'


class Frequencia(models.Model):
    MESES_CHOICES = [
        ('1', 'Janeiro'),
        ('2', 'Fevereiro'),
        ('3', 'Marco'),
        ('4', 'Abril'),
        ('5', 'Maio'),
        ('6', 'Junho'),
        ('7', 'Julho'),
        ('8', 'Agosto'),
        ('9', 'Setembro'),
        ('10', 'Outubro'),
        ('11', 'Novembro'),
        ('12', 'Dezembro'),
        ('13', 'Decimo Terceiro'),
        ('14', 'Ferias'),
    ]

    ANO_CHOICES = [(str(ano), str(ano)) for ano in range(2026, 2031)]

    OBS_CHOICES = [
        ('', ''),
        ('LICENCA SEM VENCIMENTO', 'Licenca sem vencimento'),
        ('LICENCA MATERNIDADE', 'Licenca maternidade'),
        ('LICENCA PREMIO', 'Licenca premio'),
        ('LICENCA PARA ESTUDO', 'Licenca para estudo'),
        ('FERIAS', 'Ferias'),
        ('FALTA', 'Falta'),
        ('PRO-LABORE', 'Pro-labore'),
        ('DIARIA', 'Diaria'),
        ('DOBRA DE TURNO', 'Dobra de turno'),
        ('ATESTADO MEDICO', 'Atestado medico'),
        ('DECIMO TERCEIRO', 'Decimo terceiro'),
        ('DESLIGAMENTO', 'Desligamento'),
        ('INSS', 'INSS'),
        ('OUTROS', 'Outros'),
    ]

    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, related_name='frequencias')
    mes = models.CharField(max_length=2, choices=MESES_CHOICES)
    ano = models.CharField(max_length=4, choices=ANO_CHOICES)
    faltas = models.PositiveSmallIntegerField(default=0)
    observacoes = models.CharField(max_length=80, choices=OBS_CHOICES, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['servidor__nome']
        unique_together = ('servidor', 'mes', 'ano')
        verbose_name = 'frequencia'
        verbose_name_plural = 'frequencias'

    def __str__(self):
        return f'{self.servidor.nome} - {self.get_mes_display()}/{self.ano}'


class FolhaPdf(models.Model):
    mes = models.CharField(max_length=2, choices=Frequencia.MESES_CHOICES)
    ano = models.CharField(max_length=4, choices=Frequencia.ANO_CHOICES)
    escola = models.ForeignKey(Escola, on_delete=models.PROTECT, null=True, blank=True)
    storage_path = models.CharField(max_length=500)
    nome_arquivo = models.CharField(max_length=180)
    tamanho_bytes = models.PositiveIntegerField(default=0)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'PDF da folha'
        verbose_name_plural = 'PDFs das folhas'

    def __str__(self):
        escola = self.escola.nome if self.escola else 'SEMED'
        return f'{self.nome_arquivo} - {escola}'


class FolhaAlteracao(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.PROTECT, related_name='alteracoes_folha')
    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, related_name='alteracoes_folha')
    mes = models.CharField(max_length=2, choices=Frequencia.MESES_CHOICES)
    ano = models.CharField(max_length=4, choices=Frequencia.ANO_CHOICES)
    campo = models.CharField(max_length=40)
    valor_anterior = models.CharField(max_length=120, blank=True)
    valor_novo = models.CharField(max_length=120, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'alteração da folha'
        verbose_name_plural = 'alterações das folhas'

    def __str__(self):
        return f'{self.servidor.nome} - {self.campo} - {self.get_mes_display()}/{self.ano}'


class FolhaExclusao(models.Model):
    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, related_name='exclusoes_folha')
    mes = models.CharField(max_length=2, choices=Frequencia.MESES_CHOICES)
    ano = models.CharField(max_length=4, choices=Frequencia.ANO_CHOICES)
    motivo = models.CharField(max_length=160, blank=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['servidor__nome']
        unique_together = ('servidor', 'mes', 'ano')
        verbose_name = 'exclusão da folha'
        verbose_name_plural = 'exclusões das folhas'

    def __str__(self):
        return f'{self.servidor.nome} excluído de {self.get_mes_display()}/{self.ano}'


class ServidorObservacao(models.Model):
    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, related_name='observacoes_funcionais')
    texto = models.TextField()
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'observação funcional'
        verbose_name_plural = 'observações funcionais'

    def __str__(self):
        return f'{self.servidor.nome} - {self.criado_em:%d/%m/%Y}'
