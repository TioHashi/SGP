from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.firebase import sync_model
from core.models import Escola, FolhaPdf, Frequencia, PerfilUsuario, Servidor


class Command(BaseCommand):
    help = 'Sincroniza os dados atuais do banco Django para o Firestore.'

    def handle(self, *args, **options):
        total = 0
        models = [Escola, get_user_model(), PerfilUsuario, Servidor, Frequencia, FolhaPdf]
        for model in models:
            count = 0
            for instance in model.objects.all().iterator():
                if sync_model(instance):
                    count += 1
            total += count
            self.stdout.write(self.style.SUCCESS(f'{model.__name__}: {count} registro(s) sincronizado(s).'))
        self.stdout.write(self.style.SUCCESS(f'Total sincronizado: {total}.'))
