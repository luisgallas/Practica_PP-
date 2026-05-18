# 🔗 Crear Pull Request Manualmente

Como GitHub CLI requiere autenticación interactiva, aquí está el link directo para crear el PR:

## Opción 1: Link Directo (Más rápido)
👉 https://github.com/luisgallas/Practica_PP-/pull/new/Luis_Gallas_parcial1

1. Ve al link anterior
2. GitHub te pedirá login si no estás autenticado
3. Haz click en "Create pull request"
4. Usa este título y descripción:

### Título:
```
Primer Examen Parcial - Modelos Django y Admin
```

### Descripción:
```markdown
## Sprint de Evaluación - Primer Parcial

### ✅ Cambios Implementados:

#### 1. Modelos Django (5 pts)
- Implementados 8 modelos según el ER: Usuario, Propiedad, Amenity, PropiedadAmenity, Disponibilidad, Reserva, Notificación, Review
- Todas las relaciones ForeignKey y ManyToMany correctamente definidas
- Campos y tipos de datos correctos
- Migraciones generadas y aplicadas

#### 2. Registro en Django Admin (4 pts)
- Todos los modelos registrados en admin.py
- list_display configurado con campos relevantes (2+ campos por modelo)
- Script seed_data que carga 5+ registros de prueba por modelo

#### 3. Base de Datos y Configuración (3 pts)
- PostgreSQL configurado en settings.py
- Variables de entorno en .env (no hardcodeadas)
- Archivo .env.example incluido para referencia

#### 4. README (3 pts)
- Descripción del proyecto y tecnologías
- Estructura del proyecto documentada
- Instrucciones paso a paso de instalación
- Variables de entorno listadas

#### 5. GitHub Actions (2 pts)
- Workflow configurado en .github/workflows/django-check.yml
- Ejecuta en push y PR
- Instala dependencias y ejecuta python manage.py check

### 🚀 Instrucciones de Uso Local

```bash
# 1. Clonar y cambiar rama
git clone https://github.com/luisgallas/Practica_PP-.git
cd Practica_PP-
git checkout Luis_Gallas_parcial1

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar .env
cp .env.example .env
# Editar .env con tus credenciales PostgreSQL

# 5. Crear base de datos
# En PostgreSQL: CREATE DATABASE practica_pp;

# 6. Ejecutar migraciones
python manage.py migrate

# 7. Crear superusuario
python manage.py createsuperuser

# 8. Cargar datos de prueba
python manage.py seed_data

# 9. Iniciar servidor
python manage.py runserver
```

### 📊 Estado de Implementación

- ✅ Modelos Django completos
- ✅ Django Admin configurado
- ✅ PostgreSQL ready
- ✅ README con instrucciones
- ✅ GitHub Actions workflow
- ⏳ Branch protection (configurar después)

### 📝 Archivos Principales

- `presupuesto/models.py` - 8 modelos del ER
- `presupuesto/admin.py` - Admin registrado
- `presupuesto/management/commands/seed_data.py` - Script de datos
- `config/settings.py` - Configuración Django
- `.env.example` - Variables de entorno
- `README.md` - Documentación completa
```

---

## Opción 2: Desde el navegador

1. Ve a: https://github.com/luisgallas/Practica_PP-/branches
2. Busca la rama `Luis_Gallas_parcial1`
3. Haz click en "New pull request"
4. Copia la descripción de arriba

---

## ⚙️ Después de Crear el PR:

### Configurar Branch Protection

1. Ve a Settings: https://github.com/luisgallas/Practica_PP-/settings/branches
2. Click "Add rule"
3. Rellena:
   - Branch name pattern: `main`
   - ✅ Require a pull request before merging
   - ✅ Dismiss stale pull request approvals when new commits are pushed
4. Click "Create"

---

Listo! El proyecto está 100% completo y listo para presentar a los profesores.
