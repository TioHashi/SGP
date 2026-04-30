# Deploy Firebase + Cloud Run

Este projeto e Django. O Firebase Hosting sozinho nao executa Django, entao o Hosting fica como URL publica e encaminha tudo para um servico Cloud Run chamado `sgp`.

## 1. Criar projeto Firebase

Crie o projeto no Firebase Console, ative o Firestore e o Storage.

## 2. Configurar o projeto local

Copie `.firebaserc.example` para `.firebaserc` e troque `ID_DO_SEU_PROJETO_FIREBASE`.

Copie `.env.example` para `.env` para uso local e preencha:

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_STORAGE_BUCKET`
- `GOOGLE_APPLICATION_CREDENTIALS`

O arquivo da conta de servico deve ficar fora do Git. Use `firebase-service-account.json` somente localmente.

## 3. Sincronizar dados atuais

Com `FIREBASE_ENABLED=True` e as credenciais configuradas:

```bash
python manage.py sync_firebase
```

Depois disso, novos cadastros, edicoes, transferencias, frequencias e PDFs gerados serao sincronizados automaticamente.

## 4. Publicar backend no Cloud Run

Exemplo com `gcloud`:

```bash
gcloud run deploy sgp --source . --region southamerica-east1 --allow-unauthenticated
```

Configure as variaveis de ambiente no Cloud Run:

```bash
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=...
DJANGO_ALLOWED_HOSTS=SEU_PROJETO.web.app,SEU_PROJETO.firebaseapp.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://SEU_PROJETO.web.app,https://SEU_PROJETO.firebaseapp.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000
FIREBASE_ENABLED=True
FIREBASE_PROJECT_ID=ID_DO_SEU_PROJETO_FIREBASE
FIREBASE_STORAGE_BUCKET=ID_DO_SEU_PROJETO_FIREBASE.appspot.com
```

No Cloud Run, prefira permissao por service account em vez de enviar JSON de credenciais.

## 5. Publicar Firebase Hosting

```bash
python manage.py collectstatic --noinput
firebase deploy --only hosting
```

O arquivo `firebase.json` envia todas as rotas para o Cloud Run `sgp`.
