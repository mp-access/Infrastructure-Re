



# Server Deployment

### Prerequisites

 * Host server with docker
 * Registered domain

### Steps

```
git clone https://github.com/mp-access/Infrastructure-Re.git
cp -R Infrastructure-Re/access .
cp Infrastructure-Re/docker-compose-prod.yml docker-compose.yml
cp Infrastructure-Re/.env .
```

Edit files:

 * Update variables in `.env`
 * Replace the ${DOMAIN} placeholder in access/nginx.conf

```
docker compose up certbot
docker run -it --rm -v ./access/:/access bash
```

Inside the bash VM, run `chown -R 1112:1000 /access/certbot/ /access/letsencrypt/` (replace the uid:gid with whatever user you're using to deploy ACCESS)

```
docker compose up postgres -d # then wait 10s
docker compose up keycloak -d # then wait 30s
docker compose up backend -d
docker compose up frontend -d
```

