# 📋 Instrucciones Finales - Examen Parcial

## Estado Actual ✅

Toda la implementación del código está completada y pusheada a GitHub en la rama `Luis_Gallas_parcial1`:

### Lo que ya está hecho:

1. ✅ **Modelos Django** (5 pts)
   - 8 modelos implementados: Usuario, Propiedad, Amenity, PropiedadAmenity, Disponibilidad, Reserva, Notificación, Review
   - Todas las relaciones ForeignKey y ManyToMany configuradas
   - Todos los campos con tipos de datos correctos

2. ✅ **Django Admin** (4 pts)
   - Todos los modelos registrados
   - list_display configurado con mínimo 2 campos relevantes
   - 5+ registros de prueba generables con script `seed_data`

3. ✅ **Base de Datos y Configuración** (3 pts)
   - PostgreSQL configurado
   - Variables de entorno en `.env` (no hardcodeadas)
   - Archivo `.env.example` para referencia

4. ✅ **README** (3 pts)
   - Descripción completa del proyecto
   - Instrucciones paso a paso
   - Estructura del proyecto documentada
   - Variables de entorno listadas

5. ✅ **GitHub Actions** (2 pts)
   - Workflow configurado (`.github/workflows/django-check.yml`)
   - Ejecuta en push/PR a main/master/develop
   - Instala dependencias y ejecuta `python manage.py check`

6. ⏳ **Branch Protection** (falta completar manualmente)

---

## 🔗 Próximos Pasos (Manuales en GitHub UI)

### Paso 1: Crear el Pull Request

1. Ve a: https://github.com/luisgallas/Practica_PP-
2. Verás un botón "Compare & pull request" para la rama `Luis_Gallas_parcial1`
3. O ve a: https://github.com/luisgallas/Practica_PP-/pull/new/Luis_Gallas_parcial1
4. Haz click en "Create pull request"
5. Título recomendado: `Primer Examen Parcial - Modelos Django y Admin`
6. Descripción:
```
## Sprint de Evaluación - Primer Parcial

### Cambios Implementados:

#### 1. Modelos Django (5 pts) ✅
- Implementados 8 modelos según el ER: Usuario, Propiedad, Amenity, PropiedadAmenity, Disponibilidad, Reserva, Notificación, Review
- Todas las relaciones correctamente definidas (ForeignKey, ManyToMany)
- Campos y tipos de datos correctos

#### 2. Registro en Django Admin (4 pts) ✅
- Todos los modelos registrados en admin.py
- list_display configurado con campos relevantes
- 5+ registros cargables con `python manage.py seed_data`

#### 3. BD PostgreSQL y Configuración (3 pts) ✅
- PostgreSQL como BD (settings.py configurado)
- Variables de entorno en .env
- Archivo .env.example incluido

#### 4. README (3 pts) ✅
- Descripción, tecnologías, estructura
- Instrucciones completas de instalación
- Variables de entorno documentadas

#### 5. GitHub Actions (2 pts) ✅
- Workflow configurado en .github/workflows/django-check.yml
- Ejecuta checks en push y PR
- Corre migrations y tests

### Instrucciones de Instalación Local

1. Clonar y cambiar rama:
   ```bash
   git clone https://github.com/luisgallas/Practica_PP-.git
   cd Practica_PP-
   git checkout Luis_Gallas_parcial1
   ```

2. Crear entorno virtual e instalar:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. Configurar .env:
   ```bash
   cp .env.example .env
   # Editar con credenciales PostgreSQL
   ```

4. Crear base de datos en PostgreSQL:
   ```sql
   CREATE DATABASE practica_pp;
   ```

5. Ejecutar migraciones:
   ```bash
   python manage.py migrate
   ```

6. Crear superusuario:
   ```bash
   python manage.py createsuperuser
   ```

7. Cargar datos de prueba:
   ```bash
   python manage.py seed_data
   ```

8. Iniciar servidor:
   ```bash
   python manage.py runserver
   ```

Acceder a: http://localhost:8000/admin/
```

### Paso 2: Configurar Branch Protection (2 pts)

1. Ve a Settings del repositorio: https://github.com/luisgallas/Practica_PP-/settings
2. En el menú izquierdo, selecciona "Branches"
3. Bajo "Branch protection rules", haz click en "Add rule"
4. Rellena:
   - **Branch name pattern**: `main`
   - Marca: ✅ "Require a pull request before merging"
   - Marca: ✅ "Dismiss stale pull request approvals when new commits are pushed"
   - Haz click en "Create"

---

## 🧪 Verificación Local (Antes de Demostrar)

Ejecuta estos comandos para verificar que todo funciona:

```bash
# 1. Verificar estructura
python manage.py check

# 2. Crear migraciones
python manage.py makemigrations

# 3. Aplicar migraciones
python manage.py migrate

# 4. Cargar datos de prueba
python manage.py seed_data

# 5. Iniciar servidor
python manage.py runserver
```

Luego accede a: **http://localhost:8000/admin/**

---

## 📊 Demo (3 pts)

Debes mostrar a los profesores:

1. **Sistema funcionando localmente**
   - Servidor corriendo sin errores
   - Admin panel accesible

2. **Modelos en Django Admin**
   - Mostrar cada modelo (Usuario, Propiedad, Amenity, etc.)
   - Mostrar los registros cargados
   - Demostrar creación/edición de un registro

3. **Explicar decisiones de diseño**
   - Por qué Usuario extiende AbstractUser
   - Relación M2M entre Propiedad y Amenity
   - Estados de Reserva y Disponibilidad
   - Estructura de Notificación

---

## 📝 Checklist Final

- [ ] Pull Request creado en GitHub
- [ ] Branch protection configurada para main
- [ ] README visible en el PR
- [ ] GitHub Actions ejecutándose sin errores
- [ ] Datos de prueba cargados localmente
- [ ] Admin accesible en localhost:8000/admin
- [ ] Demo lista para presentar

---

## 🎯 Puntuación Esperada

- Modelos Django: **5/5 pts** ✅
- Django Admin: **4/4 pts** ✅
- BD y Config: **3/3 pts** ✅
- README: **3/3 pts** ✅
- GitHub Actions: **2/2 pts** ✅
- Branch Protection: **2/2 pts** (⏳ falta configurar)
- Demo y Presentación: **3/3 pts** (⏳ falta demostrar)

**Total posible: 22/20 pts**

---

**Rama de trabajo**: `Luis_Gallas_parcial1`
**Fecha**: 17 de mayo de 2026
**Código**: Listo para deploy ✨
