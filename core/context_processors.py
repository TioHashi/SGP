from django.utils import timezone

from .models import TransferenciaServidor


def escola_do_usuario(user):
    perfil = getattr(user, 'perfilusuario', None)
    return perfil.escola if perfil else None


def alertas_sgp(request):
    if not request.user.is_authenticated:
        return {'alertas_sgp': [], 'alertas_total': 0}

    alertas = []
    hoje = timezone.localdate()
    if hoje.day >= 15:
        alertas.append({
            'tipo': 'folha',
            'titulo': 'Entrega da folha',
            'texto': 'A folha de frequência deve ser entregue a partir do dia 15 deste mês.',
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
        alertas.append({
            'tipo': 'transferencia',
            'titulo': 'Transferência pendente',
            'texto': f'{transferencia.servidor.nome} enviado de {transferencia.escola_origem.nome} para {transferencia.escola_destino.nome}.',
            'transferencia': transferencia,
        })

    return {'alertas_sgp': alertas, 'alertas_total': len(alertas)}
