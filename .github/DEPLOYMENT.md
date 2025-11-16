# Configuración de Deployment

Los workflows de CD (Continuous Deployment) están configurados para desplegar automáticamente a un servidor Hetzner cuando se hace push a la rama `main`.

## Secrets Requeridos

Para que el deployment funcione, necesitas configurar los siguientes secrets en GitHub:

### Configuración en GitHub

1. Ve a tu repositorio en GitHub
2. Ve a **Settings** > **Secrets and variables** > **Actions**
3. Haz clic en **New repository secret**
4. Agrega los siguientes secrets:

#### Backend CD

- `HETZNER_HOST`: IP o dominio del servidor Hetzner (ej: `123.45.67.89` o `api.tudominio.com`)
- `HETZNER_USER`: Usuario SSH para conectarse al servidor (ej: `root` o `deploy`)
- `HETZNER_SSH_KEY`: Clave privada SSH para autenticación

#### Frontend CD

- `HETZNER_HOST`: IP o dominio del servidor Hetzner
- `HETZNER_USER`: Usuario SSH
- `HETZNER_SSH_KEY`: Clave privada SSH
- `VITE_API_URL`: URL de la API para el build del frontend (opcional, ej: `https://api.tudominio.com`)

## Generar Clave SSH

Si no tienes una clave SSH, puedes generar una:

```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions
```

Luego:
1. Copia el contenido de `~/.ssh/github_actions` (clave privada) y agrégalo como `HETZNER_SSH_KEY`
2. Copia el contenido de `~/.ssh/github_actions.pub` (clave pública) y agrégalo al archivo `~/.ssh/authorized_keys` en tu servidor Hetzner

## Configuración del Servidor

### Backend

El servidor debe tener:
- Docker y Docker Compose instalados
- El repositorio clonado en `/opt/rxul-chat-backend`
- Permisos de escritura en el directorio

### Frontend

El servidor debe tener:
- Nginx instalado y configurado
- El directorio `/opt/rxul-chat-frontend/dist` creado
- Permisos de escritura en el directorio

## Comportamiento

- Si los secrets **NO** están configurados:
  - Los workflows de CD se ejecutarán pero mostrarán un mensaje informativo
  - El deployment se saltará automáticamente
  - Los workflows **NO** fallarán

- Si los secrets **SÍ** están configurados:
  - El deployment se ejecutará automáticamente en cada push a `main`
  - El backend se reconstruirá y reiniciará
  - El frontend se construirá y desplegará

## Testing Local

Para probar el deployment localmente, puedes usar:

```bash
# Backend
ssh user@your-server "cd /opt/rxul-chat-backend && git pull && docker-compose up -d --build"

# Frontend
npm run build
scp -r frontend/dist/* user@your-server:/opt/rxul-chat-frontend/dist/
ssh user@your-server "sudo systemctl restart nginx"
```

