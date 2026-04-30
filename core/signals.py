from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .firebase import delete_model, sync_model
from .models import Escola, FolhaPdf, Frequencia, PerfilUsuario, Servidor


SYNC_MODELS = (Escola, PerfilUsuario, Servidor, Frequencia, FolhaPdf, get_user_model())


@receiver(post_save)
def sync_to_firestore(sender, instance, **kwargs):
    if sender in SYNC_MODELS:
        sync_model(instance)


@receiver(post_delete)
def delete_from_firestore(sender, instance, **kwargs):
    if sender in SYNC_MODELS:
        delete_model(instance)
