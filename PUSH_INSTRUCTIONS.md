# Instrucciones para Push y Deployment

## 🚀 Workflows que se Ejecutarán

Al hacer push a `main`, se activarán automáticamente:

### CI (Continuous Integration) - Tests
1. **Backend CI** (`.github/workflows/backend-ci.yml`)
   - Ejecuta tests del backend
   - Se ejecuta en cada push a `main`

2. **Frontend CI** (`.github/workflows/frontend-ci.yml`)
   - Ejecuta tests del frontend
   - Se ejecuta en cada push a `main`

### CD (Continuous Deployment) - Deploy Automático
3. **Backend CD** (`.github/workflows/backend-cd.yml`)
   - Despliega el backend a la VM automáticamente
   - Se ejecuta solo si hay cambios en el backend

4. **Frontend CD** (`.github/workflows/frontend-cd.yml`)
   - Despliega el frontend a la VM automáticamente
   - Se ejecuta solo si hay cambios en el frontend

## ⚠️ Requisitos Antes del Push

### 1. GitHub Secrets Configurados

Verifica que tengas estos secrets en GitHub (Settings > Secrets > Actions):

- ✅ `HETZNER_HOST` = `91.98.64.119`
- ✅ `HETZNER_USER` = tu usuario SSH
- ✅ `HETZNER_SSH_KEY` = tu clave privada SSH completa
- ✅ `HETZNER_SSH_KEY_PASSPHRASE` = (vacío si no usas passphrase)
- ⚠️ `VITE_API_URL` = (opcional, para frontend)

### 2. Clave SSH en el Servidor

Asegúrate de que la clave pública SSH esté en el servidor:
```bash
# Verificar que puedes conectarte
ssh -i ~/.ssh/github_actions_deploy usuario@91.98.64.119
```

## 📝 Comandos para Hacer Push

```bash
# 1. Verificar que estás en main
git branch

# 2. Verificar estado
git status

# 3. Si hay cambios, hacer commit
git add .
git commit -m "tu mensaje"

# 4. Hacer push a main
git push origin main
```

## 🔍 Verificar el Progreso

Después del push:

1. Ve a tu repositorio en GitHub: `https://github.com/Rxul-dev/ETL`
2. Haz clic en la pestaña **"Actions"**
3. Verás los workflows ejecutándose:
   - ✅ Backend CI
   - ✅ Frontend CI
   - ✅ Backend CD (si hay cambios en backend)
   - ✅ Frontend CD (si hay cambios en frontend)

## ⚠️ Si el Deployment Falla

### Error de SSH
- Verifica que `HETZNER_SSH_KEY` esté configurado correctamente
- Verifica que la clave pública esté en el servidor

### Error de Tests
- Revisa los logs en la pestaña "Actions"
- Corrige los errores de tests antes de hacer push

### Error de Build
- Verifica que todas las dependencias estén en `requirements.txt` o `package.json`
- Revisa los logs para ver qué falta

## ✅ Después del Deployment Exitoso

1. **Verificar en la VM**:
   ```bash
   ssh usuario@91.98.64.119
   cd /opt/rxul-chat-backend
   docker-compose ps
   ```

2. **Verificar que el API funciona**:
   ```bash
   curl http://91.98.64.119/api/
   ```

3. **Verificar que el frontend funciona**:
   - Abre en el navegador: `http://91.98.64.119/`

## 📋 Checklist Pre-Push

- [ ] Estás en la rama `main`
- [ ] Todos los cambios están commiteados
- [ ] GitHub Secrets configurados
- [ ] Clave SSH agregada al servidor
- [ ] Tests pasan localmente (opcional pero recomendado)
- [ ] Listo para hacer push

