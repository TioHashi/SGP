from django.utils import timezone
from django.urls import reverse

from .models import TransferenciaServidor


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
        codigo = f'folha-{hoje.year}-{hoje.month}'
        alertas.append({
            'codigo': codigo,
            'tipo': 'folha',
            'titulo': 'Entrega da folha',
            'texto': 'A folha de frequência deve ser entregue a partir do dia 15 deste mês.',
            'destino_url': reverse('folha_mensal', args=[str(hoje.month), str(hoje.year)]),
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
