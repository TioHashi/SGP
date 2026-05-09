from django.utils import timezone
from django.urls import reverse

from .models import Frequencia, Servidor, TransferenciaServidor


def escola_do_usuario(user):
    perfil = getattr(user, 'perfilusuario', None)
    return perfil.escola if perfil else None


def alertas_sgp(request):
    if not request.user.is_authenticated:
        return {'alertas_sgp': [], 'alertas_total': 0, 'alertas_nao_lidos': 0}

    alertas = []
    lidas = set(request.session.get('notificacoes_lidas', []))
    hoje = timezone.localdate()
    if hoje.day >= 15:
        servidores = Servidor.objects.filter(ativo=True)
        escola = escola_do_usuario(request.user)
        if not request.user.is_superuser:
            servidores = servidores.filter(escola=escola)
        folha_processada = Frequencia.objects.filter(
            servidor__in=servidores,
            mes=str(hoje.month),
            ano=str(hoje.year),
        ).exists()

        codigo = f'folha-atrasada-{hoje.year}-{hoje.month}'
        if not folha_processada:
            alertas.append({
                'codigo': codigo,
                'tipo': 'folha',
                'titulo': 'Folha em atraso',
                'texto': 'A folha de frequência precisa ser processada para este mês.',
                'destino_url': reverse('folha_mensal', args=[str(hoje.month), str(hoje.year)]),
                'lida': codigo in lidas,
            })
        codigo = f'envio-secretaria-{hoje.year}-{hoje.month}'
        alertas.append({
            'codigo': codigo,
            'tipo': 'folha',
            'titulo': 'Enviar à secretaria',
            'texto': 'O relatório mensal deve ser enviado à secretaria até o dia 15.',
            'destino_url': reverse('relatorio_folha', args=[str(hoje.month), str(hoje.year)]),
            'lida': codigo in lidas,
        })

    transferencias = TransferenciaServidor.objects.filter(status='pendente').select_related(
        'servidor',
        'escola_origem',
        'escola_destino',
    )
    escola = escola_do_usuario(request.user)
    if not request.user.is_superuser:
        transferencias = transferencias.filter(escola_destino=escola)

    for transferencia in transferencias[:6]:
        codigo = f'transferencia-{transferencia.pk}'
        alertas.append({
            'codigo': codigo,
            'tipo': 'transferencia',
            'titulo': 'Transferência pendente',
            'texto': f'{transferencia.servidor.nome} enviado de {transferencia.escola_origem.nome} para {transferencia.escola_destino.nome}.',
            'transferencia': transferencia,
            'destino_url': f"{reverse('servidor_lista')}#transferencias",
            'lida': codigo in lidas,
        })

    alertas_nao_lidos = sum(1 for alerta in alertas if not alerta['lida'])
    return {'alertas_sgp': alertas, 'alertas_total': len(alertas), 'alertas_nao_lidos': alertas_nao_lidos}
