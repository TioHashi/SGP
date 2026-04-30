import logging
from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)

_firebase_app = None


def firebase_is_configured():
    return settings.FIREBASE_ENABLED and settings.FIREBASE_PROJECT_ID


def get_firebase_app():
    global _firebase_app
    if not firebase_is_configured():
        return None

    if _firebase_app is not None:
        return _firebase_app

    import firebase_admin
    from firebase_admin import credentials

    options = {'storageBucket': settings.FIREBASE_STORAGE_BUCKET}
    if settings.FIREBASE_PROJECT_ID:
        options['projectId'] = settings.FIREBASE_PROJECT_ID

    if settings.GOOGLE_APPLICATION_CREDENTIALS:
        cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
        _firebase_app = firebase_admin.initialize_app(cred, options)
    else:
        _firebase_app = firebase_admin.initialize_app(options=options)
    return _firebase_app


def firestore_client():
    app = get_firebase_app()
    if app is None:
        return None

    from firebase_admin import firestore

    return firestore.client(app)


def storage_bucket():
    app = get_firebase_app()
    if app is None or not settings.FIREBASE_STORAGE_BUCKET:
        return None

    from firebase_admin import storage

    return storage.bucket(app=app)


def firebase_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, 'pk'):
        return value.pk
    return value


def model_payload(instance):
    payload = {
        key: firebase_value(value)
        for key, value in model_to_dict(instance).items()
    }
    payload['id'] = instance.pk
    payload['model'] = instance._meta.label_lower
    return payload


def collection_name(instance):
    return instance._meta.model_name


def sync_model(instance):
    client = firestore_client()
    if client is None or not instance.pk:
        return False

    try:
        client.collection(collection_name(instance)).document(str(instance.pk)).set(model_payload(instance))
        return True
    except Exception:
        logger.exception('Falha ao sincronizar %s %s com o Firestore.', instance._meta.label, instance.pk)
        return False


def delete_model(instance):
    client = firestore_client()
    if client is None or not instance.pk:
        return False

    try:
        client.collection(collection_name(instance)).document(str(instance.pk)).delete()
        return True
    except Exception:
        logger.exception('Falha ao remover %s %s do Firestore.', instance._meta.label, instance.pk)
        return False


def upload_pdf(path, pdf_bytes):
    bucket = storage_bucket()
    if bucket is None:
        return False

    try:
        blob = bucket.blob(path)
        blob.upload_from_string(pdf_bytes, content_type='application/pdf')
        return True
    except Exception:
        logger.exception('Falha ao enviar PDF para o Firebase Storage: %s.', path)
        return False
