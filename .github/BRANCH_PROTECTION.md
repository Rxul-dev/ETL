# Branch Protection Rules

Para implementar GitFlow y proteger la rama `main`, sigue estos pasos:

## Configuración en GitHub

1. Ve a Settings > Branches en tu repositorio
2. Agrega una regla para la rama `main`:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (1)
   - ✅ Require status checks to pass before merging
     - Selecciona: `Backend CI / test` y `Frontend CI / test`
   - ✅ Require branches to be up to date before merging
   - ✅ Do not allow bypassing the above settings

## GitFlow Workflow

### Ramas principales:
- `main`: Código en producción (solo merge desde `develop` o `release/*`)
- `develop`: Código de desarrollo (rama principal de desarrollo)

### Ramas de soporte:
- `feature/*`: Nuevas funcionalidades
- `release/*`: Preparación de releases
- `hotfix/*`: Correcciones urgentes en producción

### Flujo de trabajo:

1. **Crear feature branch:**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/nueva-funcionalidad
   ```

2. **Desarrollar y commitear:**
   ```bash
   git add .
   git commit -m "feat: agregar nueva funcionalidad"
   ```

3. **Push y crear PR:**
   ```bash
   git push origin feature/nueva-funcionalidad
   ```
   Crear PR desde `feature/nueva-funcionalidad` hacia `develop`

4. **Merge a develop:**
   - Los tests deben pasar
   - Se requiere al menos 1 aprobación
   - Merge automático si todo está bien

5. **Release:**
   ```bash
   git checkout develop
   git checkout -b release/1.0.0
   # Hacer ajustes finales
   git checkout main
   git merge release/1.0.0
   git tag -a v1.0.0 -m "Release 1.0.0"
   git checkout develop
   git merge release/1.0.0
   ```

6. **Hotfix:**
   ```bash
   git checkout main
   git checkout -b hotfix/correccion-urgente
   # Hacer corrección
   git checkout main
   git merge hotfix/correccion-urgente
   git checkout develop
   git merge hotfix/correccion-urgente
   ```

## Convenciones de commits

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Documentación
- `style:` Formato, punto y coma faltante, etc.
- `refactor:` Refactorización de código
- `test:` Agregar o modificar tests
- `chore:` Tareas de mantenimiento

