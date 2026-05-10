# Deploy AWS EC2

Este projeto pode rodar em uma instancia AWS EC2 com Docker. O Django fica hospedado na instancia e os dados sao sincronizados com o Firebase Firestore. Os PDFs gerados sao enviados para o Firebase Storage.

## Arquivos necessarios

- `.env.production`, criado a partir de `.env.production.example`
- `firebase-service-account.json`, baixado no Firebase Console
- codigo do projeto na instancia

O arquivo `firebase-service-account.json` nao deve ser commitado no Git.

## Preparar a instancia

Em uma instancia Ubuntu:

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

No grupo de seguranca da EC2, libere entrada TCP na porta `8000` para testar pelo IP publico. Depois, se for usar dominio e HTTPS, o ideal e colocar Nginx nas portas `80` e `443`.

## Configurar o projeto

Copie o projeto para a instancia e entre na pasta:

```bash
cd SGP-Novo
cp .env.production.example .env.production
nano .env.production
```

Preencha:

```text
DJANGO_ALLOWED_HOSTS=IP_DA_INSTANCIA,SEU_DOMINIO.com.br
DJANGO_CSRF_TRUSTED_ORIGINS=http://IP_DA_INSTANCIA,https://SEU_DOMINIO.com.br
FIREBASE_PROJECT_ID=ID_DO_PROJETO_FIREBASE
FIREBASE_STORAGE_BUCKET=BUCKET_DO_FIREBASE
```

Coloque a credencial do Firebase na raiz do projeto:

```bash
firebase-service-account.json
```

## Subir o sistema

```bash
docker compose up -d --build
```

O sistema ficara em:

```text
http://IP_DA_INSTANCIA:8000/
```

## Conferir logs

```bash
docker compose logs -f sgp
```

## Parar ou reiniciar

```bash
docker compose restart sgp
docker compose down
```

## Observacao sobre os dados

O banco principal do Django fica persistido no volume Docker `sgp_data` em `/app/data/db.sqlite3`. Sempre que registros importantes sao criados, editados ou excluidos, o sistema sincroniza esses dados com o Firestore. Ao gerar folhas, os PDFs sao enviados para o Firebase Storage.

Se quiser que o Firestore seja o banco principal, sem SQLite, isso exige uma refatoracao maior porque o Django nao usa Firestore como banco relacional nativo.
