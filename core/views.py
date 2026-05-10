from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Max, Q
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.http import content_disposition_header, url_has_allowed_host_and_scheme
from django.utils.text import slugify
from playwright.sync_api import sync_playwright

from .forms import FolhaFiltroForm, ServidorForm, TransferirServidorForm
from .firebase import upload_pdf
from .models import Escola, FolhaAlteracao, FolhaExclusao, FolhaPdf, Frequencia, Servidor, ServidorObservacao, TransferenciaServidor
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
    servidores = servidores_permitidos(request.user).filter(
        Q(ativo=True) | Q(motivo_inativo='Licenca')
    ).order_by('nome')
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
    total_servidores = servidores.count()
    total_ativos = servidores_ativos.count() or 1
    folha_saude = round((servidores_ativos.count() / total_servidores) * 100) if total_servidores else 100
    if folha_saude >= 80:
        folha_saude_cor = '#0aa56f'
    elif folha_saude >= 50:
        folha_saude_cor = '#f2c94c'
    else:
        folha_saude_cor = '#c93d3d'
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
        'folha_saude': folha_saude,
        'folha_saude_cor': folha_saude_cor,
        'dashboard_data': dashboard_data,
    }
    return render(request, 'core/dashboard.html', contexto)


@login_required
def servidor_lista(request):
    servidores = servidores_permitidos(request.user)
    busca = request.GET.get('q', '').strip()
    escola_filtro = request.GET.get('escola', '').strip()
    escolas = Escola.objects.filter(ativa=True)
    if request.user.is_superuser and escola_filtro:
        servidores = servidores.filter(escola_id=escola_filtro)
    if busca:
        servidores = servidores.filter(nome__icontains=busca)

    transferencias_pendentes = TransferenciaServidor.objects.filter(status='pendente').select_related(
        'servidor',
        'escola_origem',
        'escola_destino',
    )
    if not request.user.is_superuser:
        escola = escola_do_usuario(request.user)
        transferencias_pendentes = transferencias_pendentes.filter(escola_destino=escola)

    contexto = {
        'servidores': servidores,
        'busca': busca,
        'escolas': escolas,
        'escola_filtro': escola_filtro,
        'transferencias_pendentes': transferencias_pendentes,
    }
    return render(request, 'core/servidor_lista.html', contexto)


def servidor_ficha_contexto(request, servidor):
    campos_historico = {'Cargo', 'Carga horária', 'Carga horaria', 'Função', 'Funcao'}
    eventos = []
    for alteracao in servidor.alteracoes_folha.select_related('usuario').filter(campo__in=campos_historico).order_by('-criado_em')[:16]:
        eventos.append({
            'data': alteracao.criado_em,
            'titulo': alteracao.campo,
            'texto': f'De "{alteracao.valor_anterior or "vazio"}" para "{alteracao.valor_novo or "vazio"}".',
            'tipo': 'Alteração',
        })

    return {
        'servidor': servidor,
        'eventos': eventos,
        'observacoes': servidor.observacoes_funcionais.select_related('criado_por'),
    }


@login_required
def servidor_ficha(request, pk):
    servidor = get_object_or_404(servidores_permitidos(request.user), pk=pk)
    if request.method == 'POST':
        texto = request.POST.get('observacao_manual', '').strip()
        if texto:
            ServidorObservacao.objects.create(servidor=servidor, texto=texto, criado_por=request.user)
            messages.success(request, 'Observação adicionada à ficha do servidor.')
        else:
            messages.error(request, 'Escreva uma observação antes de salvar.')
        return redirect('servidor_ficha', pk=servidor.pk)

    return render(request, 'core/servidor_ficha.html', servidor_ficha_contexto(request, servidor))


@login_required
def servidor_ficha_pdf(request, pk):
    servidor = get_object_or_404(servidores_permitidos(request.user), pk=pk)
    contexto = servidor_ficha_contexto(request, servidor)
    html = render_to_string('core/servidor_ficha.html', contexto, request=request)
    css_path = settings.BASE_DIR / 'static' / 'css' / 'app.css'
    css = css_path.read_text(encoding='utf-8') if css_path.exists() else ''
    html = html.replace('</head>', f'<style>{css}</style></head>')

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html, wait_until='networkidle')
        page.emulate_media(media='print')
        pdf = page.pdf(
            format='A4',
            print_background=True,
            prefer_css_page_size=True,
            margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'},
        )
        browser.close()

    nome_arquivo = f'{servidor.nome} - {servidor.escola.nome}.pdf'
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = content_disposition_header(True, nome_arquivo)
    return response


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
    destino = request.GET.get('next')
    if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
        return redirect(destino)
    return redirect('dashboard')


@login_required
def folha_selecionar(request):
    ano = request.GET.get('ano') or str(timezone.localdate().year)
    escola = escola_folha_request(request)
    hoje = timezone.localdate()
    servidores = servidores_permitidos(request.user)
    if request.user.is_superuser and escola:
        servidores = servidores.filter(escola=escola)
    meses = []
    nomes = dict(Frequencia.MESES_CHOICES)
    meses_disponiveis = [1, 2, 3, 4, 5, 6, 14, 7, 8, 9, 10, 11, 13, 12]
    querystring = querystring_escola(escola)
    for mes in meses_disponiveis:
        mes_str = str(mes)
        iniciado = mes > 12 or int(ano) < hoje.year or (int(ano) == hoje.year and mes <= hoje.month)
        registros = Frequencia.objects.filter(servidor__in=servidores, mes=mes_str, ano=ano).count()
        processada = bool(registros) or (ano == '2026' and mes <= 5)
        meses.append({
            'mes': mes_str,
            'ano': ano,
            'nome': nomes.get(mes_str, mes_str),
            'iniciado': iniciado,
            'processada': processada,
            'registros': registros,
            'querystring': querystring,
        })
    return render(request, 'core/folha_selecionar.html', {
        'ano': ano,
        'anos': [choice[0] for choice in Frequencia.ANO_CHOICES],
        'meses': meses,
        'escola': escola,
        'escolas': Escola.objects.filter(ativa=True),
    })


def observacao_licenca(servidor, mes, ano, observacao_atual=''):
    if observacao_atual:
        return observacao_atual
    if int(mes) > 12:
        return observacao_atual
    if servidor.em_licenca_no_periodo(mes, ano):
        return servidor.licenca_tipo
    return observacao_atual


def folha_extra(mes):
    return str(mes) in {'13', '14'}


@login_required
def folha_mensal(request, mes, ano):
    servidores, escola = servidores_folha_request(request)
    especial = folha_extra(mes)
    exclusoes_ids = set(
        FolhaExclusao.objects
        .filter(servidor__in=servidores, mes=mes, ano=ano)
        .values_list('servidor_id', flat=True)
    )
    if especial:
        servidores_processamento = servidores
        servidores_visiveis = [servidor for servidor in servidores if servidor.pk not in exclusoes_ids]
    else:
        servidores_processamento = servidores
        servidores_visiveis = servidores
    frequencias = {
        frequencia.servidor_id: frequencia
        for frequencia in Frequencia.objects.filter(servidor__in=servidores_processamento, mes=mes, ano=ano)
    }

    if request.method == 'POST':
        excluidos_post = {
            int(key.replace('excluir_', ''))
            for key in request.POST
            if key.startswith('excluir_')
        } if especial else set()
        for servidor_id in excluidos_post:
            servidor = next((item for item in servidores_processamento if item.pk == servidor_id), None)
            if servidor:
                FolhaExclusao.objects.update_or_create(
                    servidor=servidor,
                    mes=mes,
                    ano=ano,
                    defaults={'motivo': 'Adiantamento já solicitado', 'criado_por': request.user},
                )
                Frequencia.objects.filter(servidor=servidor, mes=mes, ano=ano).delete()
                FolhaAlteracao.objects.create(
                    escola=servidor.escola,
                    servidor=servidor,
                    mes=mes,
                    ano=ano,
                    campo='Exclusão',
                    valor_anterior='Na folha',
                    valor_novo='Excluído da folha extra',
                    usuario=request.user,
                )

        for servidor in servidores_processamento:
            if servidor.pk in excluidos_post or (especial and servidor.pk in exclusoes_ids):
                continue
            faltas = int(request.POST.get(f'faltas_{servidor.pk}') or 0)
            observacoes = observacao_licenca(servidor, mes, ano, request.POST.get(f'observacoes_{servidor.pk}', ''))
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

    linhas = []
    for servidor in servidores_visiveis:
        frequencia = frequencias.get(servidor.pk)
        observacao_sugerida = observacao_licenca(servidor, mes, ano, frequencia.observacoes if frequencia else '')
        linhas.append({'servidor': servidor, 'frequencia': frequencia, 'observacao_sugerida': observacao_sugerida})
    contexto = {
        'linhas': linhas,
        'mes': mes,
        'ano': ano,
        'nome_mes': dict(Frequencia.MESES_CHOICES).get(mes, mes),
        'obs_choices': Frequencia.OBS_CHOICES,
        'escola': escola,
        'querystring': querystring_escola(escola),
        'folha_extra': especial,
    }
    return render(request, 'core/folha_mensal.html', contexto)


@login_required
def relatorios(request):
    frequencias = Frequencia.objects.filter(servidor__in=servidores_permitidos(request.user))
    escola_filtro = request.GET.get('escola', '')
    mes_filtro = request.GET.get('mes', '')
    ano_filtro = request.GET.get('ano', '')
    if request.user.is_superuser and escola_filtro:
        frequencias = frequencias.filter(servidor__escola_id=escola_filtro)
    if mes_filtro:
        frequencias = frequencias.filter(mes=mes_filtro)
    if ano_filtro:
        frequencias = frequencias.filter(ano=ano_filtro)
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
    return render(request, 'core/relatorios.html', {
        'folhas': folhas,
        'escolas': Escola.objects.filter(ativa=True),
        'meses': Frequencia.MESES_CHOICES,
        'anos': [choice[0] for choice in Frequencia.ANO_CHOICES],
        'filtros': {'escola': escola_filtro, 'mes': mes_filtro, 'ano': ano_filtro},
    })


@login_required
def relatorio_folha(request, mes, ano):
    servidores, escola = servidores_folha_request(request)
    if folha_extra(mes):
        servidores = [
            servidor for servidor in servidores
            if not FolhaExclusao.objects.filter(servidor=servidor, mes=mes, ano=ano).exists()
        ]
    frequencias = {
        frequencia.servidor_id: frequencia
        for frequencia in Frequencia.objects.filter(servidor__in=servidores, mes=mes, ano=ano)
    }
    linhas = []
    for servidor in servidores:
        frequencia = frequencias.get(servidor.pk)
        if frequencia and not frequencia.observacoes and servidor.em_licenca_no_periodo(mes, ano):
            frequencia.observacoes = servidor.licenca_tipo
        linhas.append({'servidor': servidor, 'frequencia': frequencia})
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
def relatorio_folha_excluir(request, mes, ano):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    servidores, escola = servidores_folha_request(request)
    if request.user.is_superuser and not escola:
        messages.error(request, 'Selecione uma escola para excluir a folha.')
        return redirect('relatorios')

    frequencias_removidas, _ = Frequencia.objects.filter(
        servidor__in=servidores,
        mes=mes,
        ano=ano,
    ).delete()
    FolhaExclusao.objects.filter(
        servidor__in=servidores,
        mes=mes,
        ano=ano,
    ).delete()
    FolhaPdf.objects.filter(
        escola=escola,
        mes=mes,
        ano=ano,
    ).delete()

    nome_mes = dict(Frequencia.MESES_CHOICES).get(mes, mes)
    escola_nome = escola.nome if escola else 'sua escola'
    messages.success(request, f'Folha de {nome_mes}/{ano} de {escola_nome} excluída. {frequencias_removidas} registro(s) removido(s).')
    destino = f"{redirect('folha_selecionar').url}?ano={ano}{'&escola=' + str(escola.pk) if escola else ''}"
    return redirect(destino)


@login_required
def relatorio_folha_pdf(request, mes, ano):
    servidores, escola = servidores_folha_request(request)
    if folha_extra(mes):
        servidores = [
            servidor for servidor in servidores
            if not FolhaExclusao.objects.filter(servidor=servidor, mes=mes, ano=ano).exists()
        ]
    frequencias = {
        frequencia.servidor_id: frequencia
        for frequencia in Frequencia.objects.filter(servidor__in=servidores, mes=mes, ano=ano)
    }
    linhas = []
    for servidor in servidores:
        frequencia = frequencias.get(servidor.pk)
        if frequencia and not frequencia.observacoes and servidor.em_licenca_no_periodo(mes, ano):
            frequencia.observacoes = servidor.licenca_tipo
        linhas.append({'servidor': servidor, 'frequencia': frequencia})
    nome_mes = dict(Frequencia.MESES_CHOICES).get(mes, mes)
    escola_nome = escola.nome if escola else 'SEMED'
    nome_arquivo = f'Frequência Mensal - {escola_nome} ({nome_mes}-{ano}).pdf'
    nome_storage = f'frequencia-mensal-{slugify(escola_nome)}-{slugify(nome_mes)}-{ano}.pdf'
    storage_path = f'folhas/{ano}/{mes}/{nome_storage}'
    pdf = folha_pdf_bytes(linhas, mes, ano, escola)

    upload_pdf(storage_path, pdf)
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
