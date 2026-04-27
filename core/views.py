from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    cards = [
        {'label': 'Servidores', 'value': '0', 'hint': 'Cadastros ativos'},
        {'label': 'Lotacoes', 'value': '0', 'hint': 'Unidades vinculadas'},
        {'label': 'Folha', 'value': '0', 'hint': 'Registros do mes'},
    ]
    return render(request, 'core/dashboard.html', {'cards': cards})
