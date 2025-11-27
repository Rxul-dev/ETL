# 🚀 Deployment Automático en DigitalOcean

## ✅ Configuración Completa

Cuando hagas push a `main`, el sistema automáticamente:

1. **Crea los droplets** con Terraform (si están configurados los secrets)
2. **Espera** a que los droplets estén listos (~2-3 minutos)
3. **Despliega el backend** en el droplet de backend
4. **Despliega el frontend** en el droplet de frontend
5. **Configura Nginx** automáticamente

## 📋 Secrets Requeridos en GitHub

### Para Terraform (Crear Droplets)
- `DO_TOKEN`: Token de API de DigitalOcean
- `DO_SSH_KEY_ID`: ID de la clave SSH en DigitalOcean

### Para Deployment (Desplegar Código)
- `DO_SSH_KEY`: Clave privada SSH para conectarse a los droplets

### Opcional (Fallback a Hetzner)
- `HETZNER_HOST`: IP de Hetzner (si no usas DigitalOcean)
- `HETZNER_USER`: Usuario SSH de Hetzner
- `HETZNER_SSH_KEY`: Clave SSH de Hetzner

## 🔄 Flujo Automático

```
Push a main
    ↓
Terraform Apply (crea 7 droplets)
    ↓
Guarda IPs en artifact
    ↓
Backend CD - DigitalOcean (despliega backend)
    ↓
Frontend CD - DigitalOcean (despliega frontend)
    ↓
✅ Todo funcionando
```

## 📝 Cómo Funciona

1. **Terraform crea los droplets** y guarda las IPs en un artifact
2. **Los workflows de CD** descargan las IPs del artifact
3. **Si hay IPs de DigitalOcean**, despliegan ahí
4. **Si no hay IPs**, usan Hetzner como fallback

## ⚙️ Configuración de Secrets

### 1. Obtener DO_SSH_KEY

La clave SSH que usas para conectarte a DigitalOcean debe ser la misma que agregaste a DigitalOcean:

```bash
# Ver tu clave privada
cat ~/.ssh/github_actions_deploy

# O la que usaste para DigitalOcean
cat ~/.ssh/do_key
```

Copia el contenido completo (incluyendo `-----BEGIN` y `-----END`) y agrégalo como `DO_SSH_KEY` en GitHub.

## 🎯 Próximos Pasos

1. Configura los secrets en GitHub
2. Haz push a `main`
3. Espera a que Terraform cree los droplets
4. Los workflows de CD desplegarán automáticamente

## ⚠️ Notas Importantes

- Los droplets tardan ~2-3 minutos en estar listos
- El deployment espera automáticamente antes de conectarse
- Si falla, verifica que la clave SSH sea correcta
- Los archivos `.env` se crean automáticamente con valores por defecto (debes actualizarlos)

## 🔍 Verificar Deployment

Después del push:

1. Ve a GitHub Actions: https://github.com/Rxul-dev/ETL/actions
2. Verás:
   - ✅ Terraform Apply (crea droplets)
   - ✅ Backend CD - DigitalOcean (despliega backend)
   - ✅ Frontend CD - DigitalOcean (despliega frontend)

3. Las IPs de los droplets aparecerán en el summary de Terraform Apply

