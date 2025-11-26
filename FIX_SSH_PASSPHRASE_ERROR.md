# Solución: Error de Passphrase SSH

## 🔴 Error Actual

```
ssh.ParsePrivateKey: ssh: key is not password protected
ssh: handshake failed: ssh: unable to authenticate, attempted methods [none], no supported methods remain
```

## ✅ Solución

El error indica que GitHub Actions está intentando usar un passphrase cuando tu clave SSH **NO tiene passphrase**.

### Opción 1: Dejar el Secret Vacío (Recomendado)

1. Ve a GitHub: **Settings** > **Secrets and variables** > **Actions**
2. Busca `HETZNER_SSH_KEY_PASSPHRASE`
3. Si existe, **edítalo y déjalo completamente vacío** (o elimínalo)
4. Guarda los cambios

### Opción 2: Verificar que la Clave Pública Esté en el Servidor

El error también puede indicar que la clave pública no está en el servidor. Verifica:

```bash
# Desde tu máquina local, prueba la conexión
ssh -i ~/.ssh/github_actions_deploy usuario@91.98.64.119
```

Si **NO puedes conectarte**, necesitas agregar la clave pública al servidor:

```bash
# Agregar la clave pública al servidor
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub usuario@91.98.64.119
```

O manualmente en el servidor:

```bash
# En la VM
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII4s55gAmp53Pyv4dgcuMyGCfMkq1cF1omwfBm7MnPLb github-actions" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Opción 3: Verificar el Formato de la Clave en GitHub Secrets

Asegúrate de que `HETZNER_SSH_KEY` contenga la clave privada **completa**:

1. Ve a GitHub Secrets
2. Edita `HETZNER_SSH_KEY`
3. Verifica que tenga este formato:
   ```
   -----BEGIN OPENSSH PRIVATE KEY-----
   b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAACFwAAAAdzc2gtcn
   ...
   -----END OPENSSH PRIVATE KEY-----
   ```
4. Debe incluir las líneas `-----BEGIN...` y `-----END...`
5. No debe tener espacios extra al inicio o final

## 📋 Checklist de Verificación

- [ ] `HETZNER_SSH_KEY_PASSPHRASE` está vacío o no existe en GitHub Secrets
- [ ] `HETZNER_SSH_KEY` contiene la clave privada completa (con BEGIN/END)
- [ ] La clave pública está en `~/.ssh/authorized_keys` en el servidor
- [ ] Puedes conectarte manualmente: `ssh -i ~/.ssh/github_actions_deploy usuario@91.98.64.119`
- [ ] Permisos correctos en el servidor: `chmod 700 ~/.ssh` y `chmod 600 ~/.ssh/authorized_keys`

## 🔧 Verificación Rápida

```bash
# 1. Verificar que puedes conectarte manualmente
ssh -i ~/.ssh/github_actions_deploy usuario@91.98.64.119

# 2. Si funciona, el problema es solo el passphrase en GitHub Secrets
# 3. Si no funciona, necesitas agregar la clave pública al servidor
```

## ✅ Después de Corregir

1. Deja `HETZNER_SSH_KEY_PASSPHRASE` vacío en GitHub Secrets
2. Verifica que la clave pública esté en el servidor
3. Haz un nuevo push o re-ejecuta el workflow desde GitHub Actions

