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
        ('Assistente Administrativo', 'Assistente Administrativo'),
        ('Auxiliar Administrativo', 'Auxiliar Administrativo'),
        ('ASG', 'ASG'),
        ('Coordenador(a)', 'Coordenador(a)'),
        ('Professor(a)', 'Professor(a)'),
        ('Vigia', 'Vigia'),
        ('Merendeira', 'Merendeira'),
        ('Monitor(a)', 'Monitor(a)'),
        ('Motorista', 'Motorista'),
        ('Diretor(a)', 'Diretor(a)'),
        ('Mediadora Social', 'Mediadora Social'),
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
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'servidor'
        verbose_name_plural = 'servidores'

    def __str__(self):
        return self.nome


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
