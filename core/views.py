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
from .models import Escola, FolhaAlteracao, FolhaPdf, Frequencia, Servidor, TransferenciaServidor
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


def escola_folha_request(request):
    if not request.user.is_superuser:
        return escola_do_usuario(request.user)

    escola_id = request.GET.get('escola')
    if escola_id:
        return get_object_or_404(Escola, pk=escola_id)
    return None


def servidores_folha_request(request):
    servidores = servidores_permitidos(request.user).filter(ativo=True).order_by('nome')
    escola = escola_folha_request(request)
    if request.user.is_superuser and escola:
        servidores = servidores.filter(escola=escola)
    return list(servidores), escola


def querystring_escola(escola):
    return f'?escola={escola.pk}' if escola else ''


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
        item['percentual_css'] = int(round((item['total'] / max_funcoes) * 100))
    for item in cargos:
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
    return redirect(request.GET.get('next') or 'dashboard')


@login_required
def folha_selecionar(request):
    form = FolhaFiltroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        return redirect('folha_mensal', mes=form.cleaned_data['mes'], ano=form.cleaned_data['ano'])
    return render(request, 'core/folha_selecionar.html', {'form': form})


@login_required
def folha_mensal(request, mes, ano):
    servidores, escola = servidores_folha_request(request)
    frequencias = {
        frequencia.servidor_id: frequencia
        for frequencia in Frequencia.objects.filter(servidor__in=servidores, mes=mes, ano=ano)
    }

    if request.method == 'POST':
        for servidor in servidores:
            faltas = int(request.POST.get(f'faltas_{servidor.pk}') or 0)
            observacoes = request.POST.get(f'observacoes_{servidor.pk}', '')
            frequencia_atual = frequencias.get(servidor.pk)
            alteracoes = []
            if frequencia_atual:
                if frequencia_atual.faltas != faltas:
                    alteracoes.append(('Faltas', str(frequencia_atual.faltas), str(faltas)))
                if frequencia_atual.observacoes != observacoes:
                    alteracoes.append(('Observações', frequencia_atual.observacoes, observacoes))
            elif faltas or observacoes:
                alteracoes.append(('Registro', '', 'Folha preenchida'))

            Frequencia.objects.update_or_create(
                servidor=servidor,
                mes=mes,
                ano=ano,
                defaults={'faltas': faltas, 'observacoes': observacoes},
            )
            for campo, anterior, novo in alteracoes:
                FolhaAlteracao.objects.create(
                    escola=servidor.escola,
                    servidor=servidor,
                    mes=mes,
                    ano=ano,
                    campo=campo,
                    valor_anterior=anterior,
                    valor_novo=novo,
                    usuario=request.user,
                )
        messages.success(request, 'Folha salva com sucesso.')
        return redirect(f"{redirect('folha_mensal', mes=mes, ano=ano).url}{querystring_escola(escola)}")

    linhas = [{'servidor': servidor, 'frequencia': frequencias.get(servidor.pk)} for servidor in servidores]
    contexto = {
        'linhas': linhas,
        'mes': mes,
        'ano': ano,
        'nome_mes': dict(Frequencia.MESES_CHOICES).get(mes, mes),
        'obs_choices': Frequencia.OBS_CHOICES,
        'escola': escola,
        'querystring': querystring_escola(escola),
    }
    return render(request, 'core/folha_mensal.html', contexto)


@login_required
def relatorios(request):
    frequencias = Frequencia.objects.filter(servidor__in=servidores_permitidos(request.user))
    agrupamento = ['mes', 'ano']
    if request.user.is_superuser:
        agrupamento.extend(['servidor__escola_id', 'servidor__escola__nome'])

    ordenacao = ['-ano', '-mes']
    if request.user.is_superuser:
        ordenacao.append('servidor__escola__nome')

    folhas = list(
        frequencias
        .values(*agrupamento)
        .annotate(total=Count('id'), atualizado_em=Max('atualizado_em'))
        .order_by(*ordenacao)
    )
    meses = dict(Frequencia.MESES_CHOICES)
    for folha in folhas:
        folha['nome_mes'] = meses.get(folha['mes'], folha['mes'])
        escola_id = folha.get('servidor__escola_id')
        folha['escola_id'] = escola_id
        folha['escola_nome'] = folha.get('servidor__escola__nome') or escola_do_usuario(request.user)
        folha['querystring'] = f'?escola={escola_id}' if request.user.is_superuser and escola_id else ''
        folha['alteracoes'] = []
        if request.user.is_superuser and escola_id:
            folha['alteracoes'] = list(
                FolhaAlteracao.objects
                .filter(escola_id=escola_id, mes=folha['mes'], ano=folha['ano'])
                .select_related('servidor', 'usuario')
                .order_by('-criado_em')[:4]
            )
    return render(request, 'core/relatorios.html', {'folhas': folhas})


@login_required
def relatorio_folha(request, mes, ano):
    servidores, escola = servidores_folha_request(request)
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
        'escola': escola,
        'querystring': querystring_escola(escola),
    }
    return render(request, 'core/relatorio_folha.html', contexto)


@login_required
def relatorio_folha_pdf(request, mes, ano):
    servidores, escola = servidores_folha_request(request)
    frequencias = {
        frequencia.servidor_id: frequencia
        for frequencia in Frequencia.objects.filter(servidor__in=servidores, mes=mes, ano=ano)
    }
    linhas = [{'servidor': servidor, 'frequencia': frequencias.get(servidor.pk)} for servidor in servidores]
    nome_mes = dict(Frequencia.MESES_CHOICES).get(mes, mes)
    escola_nome = escola.nome if escola else 'semed'
    nome_arquivo = f'Frequência Mensal ({nome_mes}/{ano}).pdf'
    nome_storage = f'frequencia-mensal-{slugify(escola_nome)}-{slugify(nome_mes)}-{ano}.pdf'
    storage_path = f'folhas/{ano}/{mes}/{nome_storage}'
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
