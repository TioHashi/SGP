from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import content_disposition_header
from django.utils.text import slugify

from .forms import FolhaFiltroForm, ServidorForm, TransferirServidorForm
from .firebase import upload_pdf
from .models import Escola, FolhaPdf, Frequencia, Servidor, TransferenciaServidor
from .pdfs import folha_pdf_bytes


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
        .order_by('-total', 'cargo')[:10]
    )
    max_funcoes = max([item['total'] for item in funcoes] or [1])
    max_cargos = max([item['total'] for item in cargos] or [1])
    for item in funcoes:
        item['percentual'] = round((item['total'] / max_funcoes) * 100, 1)
        item['percentual_css'] = int(round((item['total'] / max_funcoes) * 100))
    for item in cargos:
        item['percentual'] = round((item['total'] / max_cargos) * 100, 1)
        item['percentual_css'] = int(round((item['total'] / max_cargos) * 100))
    total_ativos = servidores_ativos.count() or 1
    status_resumo = {
        'ativos': servidores_ativos.count(),
        'inativos': servidores.filter(ativo=False).count(),
        'percentual_ativos': round((servidores_ativos.count() / total_ativos) * 100, 1),
    }

    total_vinculos = sum(item['total'] for item in vinculos) or 1
    vinculo_resumo = [
        {
            'label': item['vinculo'] or 'Nao informado',
            'total': item['total'],
            'percentual': round((item['total'] / total_vinculos) * 100, 1),
            'percentual_css': int(round((item['total'] / total_vinculos) * 100)),
        }
        for item in vinculos
    ]
    vinculos_por_nome = {item['label']: item['total'] for item in vinculo_resumo}

    dashboard_data = {
        'vinculos': {
            'labels': [item['label'] for item in vinculo_resumo],
            'data': [item['total'] for item in vinculo_resumo],
        },
        'funcoes': {
            'labels': [item['funcao'] or 'Nao informado' for item in funcoes],
            'data': [item['total'] for item in funcoes],
        },
        'cargos': {
            'labels': [item['cargo'] or 'Nao informado' for item in cargos],
            'data': [item['total'] for item in cargos],
        },
    }

    contexto = {
        'cards': cards,
        'escola_atual': escola_atual,
        'vinculo_resumo': vinculo_resumo,
        'funcoes': funcoes,
        'cargos': cargos,
        'status_resumo': status_resumo,
        'efetivos_total': vinculos_por_nome.get('Efetivo', 0),
        'temporarios_total': vinculos_por_nome.get('Temporario', 0),
        'hoje': timezone.localdate(),
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
def servidor_ficha(request, pk):
    servidor = get_object_or_404(servidores_permitidos(request.user), pk=pk)
    return render(request, 'core/servidor_ficha.html', {'servidor': servidor})


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
    return render(request, 'core/servidor_form.html', {'form': form, 'titulo': 'Editar servidor', 'servidor': servidor})


@login_required
def servidor_transferir(request, pk):
    servidor = get_object_or_404(servidores_permitidos(request.user), pk=pk)
    form = TransferirServidorForm(request.POST or None, servidor=servidor)
    if request.method == 'POST' and form.is_valid():
        destino = form.cleaned_data['escola_destino']
        TransferenciaServidor.objects.create(
            servidor=servidor,
            escola_origem=servidor.escola,
            escola_destino=destino,
            solicitado_por=request.user,
        )
        messages.success(request, f'Solicitacao enviada para {destino.nome}. A escola destino precisa aceitar a transferencia.')
        return redirect('servidor_lista')

    return render(request, 'core/servidor_transferir.html', {'form': form, 'servidor': servidor})


@login_required
def transferencia_aceitar(request, pk):
    transferencia = get_object_or_404(
        TransferenciaServidor.objects.select_related('servidor', 'escola_destino', 'escola_origem'),
        pk=pk,
        status='pendente',
    )
    escola = escola_do_usuario(request.user)
    if not request.user.is_superuser and escola != transferencia.escola_destino:
        messages.error(request, 'Esta transferencia deve ser aceita pela escola de destino.')
        return redirect('dashboard')

    if request.method == 'POST':
        servidor = transferencia.servidor
        servidor.escola = transferencia.escola_destino
        servidor.save(update_fields=['escola', 'atualizado_em'])
        transferencia.status = 'aceita'
        transferencia.respondido_por = request.user
        transferencia.respondido_em = timezone.now()
        transferencia.save(update_fields=['status', 'respondido_por', 'respondido_em'])
        messages.success(request, f'{servidor.nome} foi transferido para {transferencia.escola_destino.nome}.')
    return redirect('dashboard')


@login_required
def notificacao_ler(request, codigo):
    lidas = set(request.session.get('notificacoes_lidas', []))
    lidas.add(codigo)
    request.session['notificacoes_lidas'] = sorted(lidas)
    request.session.modified = True
    destino = request.GET.get('next') or 'dashboard'
    return redirect(destino)


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


@login_required
def relatorio_folha_pdf(request, mes, ano):
    servidores = list(servidores_permitidos(request.user).filter(ativo=True).order_by('nome'))
    frequencias = {
        frequencia.servidor_id: frequencia
        for frequencia in Frequencia.objects.filter(servidor__in=servidores, mes=mes, ano=ano)
    }
    linhas = [{'servidor': servidor, 'frequencia': frequencias.get(servidor.pk)} for servidor in servidores]
    escola = escola_do_usuario(request.user)
    nome_mes = dict(Frequencia.MESES_CHOICES).get(mes, mes)
    escola_nome = escola.nome if escola else 'semed'
    nome_arquivo = f'Frequência Mensal ({nome_mes}-{ano}).pdf'
    storage_path = f'folhas/{ano}/{mes}/{nome_arquivo}'
    pdf = folha_pdf_bytes(linhas, mes, ano, escola)

    enviado = upload_pdf(storage_path, pdf)
    if enviado:
        FolhaPdf.objects.create(
            mes=mes,
            ano=ano,
            escola=escola,
            storage_path=storage_path,
            nome_arquivo=nome_arquivo,
            tamanho_bytes=len(pdf),
            criado_por=request.user,
        )

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = content_disposition_header(True, nome_arquivo)
    return response
