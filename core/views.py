from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect, render

from .forms import FolhaFiltroForm, ServidorForm, TransferirServidorForm
from .models import Escola, Frequencia, Servidor


def escola_do_usuario(user):
    perfil = getattr(user, 'perfilusuario', None)
    return perfil.escola if perfil else None


def servidores_permitidos(user):
    queryset = Servidor.objects.select_related('escola')
    if user.is_superuser:
        return queryset

    escola = escola_do_usuario(user)
    if not escola:
        return queryset.none()

    return queryset.filter(escola=escola)


@login_required
def dashboard(request):
    servidores = servidores_permitidos(request.user)
    servidores_ativos = servidores.filter(ativo=True)
    escolas = Escola.objects.filter(ativa=True)
    escola_atual = None
    if not request.user.is_superuser:
        escola_atual = escola_do_usuario(request.user)
        escolas = escolas.filter(pk=escola_atual.pk) if escola_atual else escolas.none()

    cards = [
        {'label': 'Servidores', 'value': servidores_ativos.count(), 'hint': 'Cadastros ativos'},
        {'label': 'Escolas', 'value': escolas.count(), 'hint': 'Unidades acessiveis'},
        {'label': 'Inativos', 'value': servidores.filter(ativo=False).count(), 'hint': 'Cadastros desativados'},
        {'label': 'Funcoes', 'value': servidores.values('funcao').exclude(funcao='').distinct().count(), 'hint': 'Funcoes diferentes'},
    ]
    vinculos = list(
        servidores_ativos
        .values('vinculo')
        .annotate(total=Count('id'))
        .order_by('vinculo')
    )
    funcoes = list(
        servidores_ativos
        .values('funcao')
        .exclude(funcao='')
        .annotate(total=Count('id'))
        .order_by('-total', 'funcao')[:10]
    )
    cargos = list(
        servidores_ativos
        .values('cargo')
        .exclude(cargo='')
        .annotate(total=Count('id'))
        .order_by('-total', 'cargo')[:6]
    )

    total_vinculos = sum(item['total'] for item in vinculos) or 1
    vinculo_resumo = [
        {
            'label': item['vinculo'] or 'Nao informado',
            'total': item['total'],
            'percentual': round((item['total'] / total_vinculos) * 100, 1),
        }
        for item in vinculos
    ]

    dashboard_data = {
        'vinculos': {
            'labels': [item['label'] for item in vinculo_resumo],
            'data': [item['total'] for item in vinculo_resumo],
        },
        'funcoes': {
            'labels': [item['funcao'] or 'Nao informado' for item in funcoes],
            'data': [item['total'] for item in funcoes],
        },
    }

    contexto = {
        'cards': cards,
        'escola_atual': escola_atual,
        'vinculo_resumo': vinculo_resumo,
        'funcoes': funcoes,
        'cargos': cargos,
        'dashboard_data': dashboard_data,
    }
    return render(request, 'core/dashboard.html', contexto)


@login_required
def servidor_lista(request):
    servidores = servidores_permitidos(request.user)
    busca = request.GET.get('q', '').strip()
    if busca:
        servidores = servidores.filter(nome__icontains=busca)
    return render(request, 'core/servidor_lista.html', {'servidores': servidores, 'busca': busca})


@login_required
def servidor_criar(request):
    form = ServidorForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Servidor cadastrado com sucesso.')
        return redirect('servidor_lista')
    return render(request, 'core/servidor_form.html', {'form': form, 'titulo': 'Cadastrar servidor'})


@login_required
def servidor_editar(request, pk):
    servidor = get_object_or_404(servidores_permitidos(request.user), pk=pk)
    form = ServidorForm(request.POST or None, instance=servidor, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Servidor atualizado com sucesso.')
        return redirect('servidor_lista')
    return render(request, 'core/servidor_form.html', {'form': form, 'titulo': 'Editar servidor'})


@login_required
def servidor_transferir(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Apenas o superusuario pode transferir servidores entre escolas.')
        return redirect('servidor_lista')

    servidor = get_object_or_404(Servidor.objects.select_related('escola'), pk=pk)
    form = TransferirServidorForm(request.POST or None, servidor=servidor)
    if request.method == 'POST' and form.is_valid():
        origem = servidor.escola
        servidor.escola = form.cleaned_data['escola_destino']
        servidor.save(update_fields=['escola', 'atualizado_em'])
        messages.success(request, f'{servidor.nome} transferido de {origem.nome} para {servidor.escola.nome}.')
        return redirect('servidor_lista')

    return render(request, 'core/servidor_transferir.html', {'form': form, 'servidor': servidor})


@login_required
def folha_selecionar(request):
    form = FolhaFiltroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        return redirect('folha_mensal', mes=form.cleaned_data['mes'], ano=form.cleaned_data['ano'])
    return render(request, 'core/folha_selecionar.html', {'form': form})


@login_required
def folha_mensal(request, mes, ano):
    servidores = list(servidores_permitidos(request.user).filter(ativo=True).order_by('nome'))
    frequencias = {
        frequencia.servidor_id: frequencia
        for frequencia in Frequencia.objects.filter(servidor__in=servidores, mes=mes, ano=ano)
    }

    if request.method == 'POST':
        for servidor in servidores:
            faltas = request.POST.get(f'faltas_{servidor.pk}') or 0
            observacoes = request.POST.get(f'observacoes_{servidor.pk}', '')
            Frequencia.objects.update_or_create(
                servidor=servidor,
                mes=mes,
                ano=ano,
                defaults={'faltas': faltas, 'observacoes': observacoes},
            )
        messages.success(request, 'Folha salva com sucesso.')
        return redirect('folha_mensal', mes=mes, ano=ano)

    linhas = [{'servidor': servidor, 'frequencia': frequencias.get(servidor.pk)} for servidor in servidores]
    contexto = {
        'linhas': linhas,
        'mes': mes,
        'ano': ano,
        'nome_mes': dict(Frequencia.MESES_CHOICES).get(mes, mes),
        'obs_choices': Frequencia.OBS_CHOICES,
    }
    return render(request, 'core/folha_mensal.html', contexto)


@login_required
def relatorios(request):
    frequencias = Frequencia.objects.filter(servidor__in=servidores_permitidos(request.user))
    folhas = (
        frequencias
        .values('mes', 'ano')
        .annotate(total=Count('id'), atualizado_em=Max('atualizado_em'))
        .order_by('-ano', '-mes')
    )
    meses = dict(Frequencia.MESES_CHOICES)
    for folha in folhas:
        folha['nome_mes'] = meses.get(folha['mes'], folha['mes'])
    return render(request, 'core/relatorios.html', {'folhas': folhas})


@login_required
def relatorio_folha(request, mes, ano):
    servidores = list(servidores_permitidos(request.user).filter(ativo=True).order_by('nome'))
    frequencias = {
        frequencia.servidor_id: frequencia
        for frequencia in Frequencia.objects.filter(servidor__in=servidores, mes=mes, ano=ano)
    }
    linhas = [{'servidor': servidor, 'frequencia': frequencias.get(servidor.pk)} for servidor in servidores]
    contexto = {
        'linhas': linhas,
        'mes': mes,
        'ano': ano,
        'nome_mes': dict(Frequencia.MESES_CHOICES).get(mes, mes),
        'escola': escola_do_usuario(request.user),
    }
    return render(request, 'core/relatorio_folha.html', contexto)
