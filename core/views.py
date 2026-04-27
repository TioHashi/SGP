from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ServidorForm
from .models import Escola, Servidor


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
    escolas = Escola.objects.filter(ativa=True)
    if not request.user.is_superuser:
        escola = escola_do_usuario(request.user)
        escolas = escolas.filter(pk=escola.pk) if escola else escolas.none()

    cards = [
        {'label': 'Servidores', 'value': servidores.filter(ativo=True).count(), 'hint': 'Cadastros ativos'},
        {'label': 'Escolas', 'value': escolas.count(), 'hint': 'Unidades acessiveis'},
        {'label': 'Vinculos', 'value': servidores.values('vinculo').exclude(vinculo='').distinct().count(), 'hint': 'Tipos cadastrados'},
    ]
    por_escola = servidores.values('escola__nome').annotate(total=Count('id')).order_by('escola__nome')
    return render(request, 'core/dashboard.html', {'cards': cards, 'por_escola': por_escola})


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
