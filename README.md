# ⚽ Quiniela Mundial

Aplicación web completa para gestionar una quiniela del mundial de fútbol. Sistema profesional con backend FastAPI y frontend React.

## 🌟 Características

- **Gestión de Usuarios**: Registro y autenticación de usuarios
- **Predicciones**: Los usuarios pueden pronosticar resultados de partidos
- **Sistema de Puntos**:
  - 3 puntos por resultado exacto
  - 1 punto por tendencia correcta (ganador o empate)
  - 0 puntos por predicción incorrecta
- **Tabla de Clasificación**: Ranking de usuarios por puntos
- **Panel de Administración**: Crear partidos y actualizar resultados
- **Filtros**: Ver partidos por fase o estado
- **Banderas de Países**: Visualización con imágenes PNG de alta calidad (ver [BANDERAS.md](BANDERAS.md))
  - 40+ países con bandera disponible
  - Lista de pendientes en [BANDERAS_FALTANTES.md](BANDERAS_FALTANTES.md)

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.8+
- Node.js 16+
- PowerShell (Windows)

### Instalación y Ejecución

#### Opción 1: Usar el script automatizado (Recomendado)

```powershell
.\start-quiniela.ps1
```

Este script:

1. Instala el backend de Python
2. Instala el frontend de Node.js
3. Inicia ambos servicios automáticamente
4. Abre tu navegador automáticamente

#### Opción 2: Instalación manual

**Backend (Terminal 1)**:

```powershell
cd Quiniela\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

El backend estará disponible en: `http://localhost:8000`

**Frontend (Terminal 2)**:

```powershell
cd Quiniela\frontend
npm install
npm run dev
```

El frontend estará disponible en: `http://localhost:5173`

## 📱 Uso de la Aplicación

### Para Usuarios

1. **Registro**: Crea una cuenta nueva con usuario, email y contraseña
2. **Login**: Inicia sesión con tu usuario y contraseña
3. **Ver Partidos**: Navega a "Partidos" para ver todos los partidos del mundial
4. **Hacer Predicciones**:
   - Ingresa tu pronóstico de goles para cada equipo
   - Solo puedes hacer predicciones antes de que comience el partido
   - Puedes modificar tus predicciones hasta que inicie el partido
5. **Ver Clasificación**: Consulta tu posición en la tabla de puntos
6. **Mis Predicciones**: Revisa el historial de tus pronósticos y puntos ganados

### Para Administradores

Para hacer a un usuario administrador, necesitas acceder a la base de datos directamente:

```python
# Ejecuta Python en el backend
from main import SessionLocal, User

db = SessionLocal()
user = db.query(User).filter(User.username == "nombre_usuario").first()
user.is_admin = True
db.commit()
```

Como administrador puedes:

- Crear nuevos partidos (equipos, fecha, fase)
- Actualizar resultados de partidos
- Marcar partidos como finalizados
- Eliminar partidos

## 🏗️ Estructura del Proyecto

```
Quiniela/
├── backend/
│   ├── main.py             # API FastAPI con todos los endpoints
│   ├── requirements.txt    # Dependencias de Python
│   └── quiniela.db        # Base de datos SQLite (se crea automáticamente)
│
└── frontend/
    ├── src/
    │   ├── components/    # Componentes React
    │   │   ├── Login.jsx
    │   │   ├── Register.jsx
    │   │   ├── MatchList.jsx
    │   │   ├── Predictions.jsx
    │   │   ├── Leaderboard.jsx
    │   │   ├── AdminPanel.jsx
    │   │   └── TeamFlag.jsx
    │   ├── App.jsx        # Componente principal con rutas
    │   ├── api.js         # Cliente API para comunicación con backend
    │   └── index.css      # Estilos Tailwind
    ├── package.json
    ├── vite.config.js
    └── tailwind.config.js
```

## 🏴 Banderas de Países

La aplicación usa **imágenes locales PNG** para las banderas, ubicadas en `/frontend/public/flags/`.

### Banderas Disponibles ✅

**40+ países ya tienen bandera**, incluyendo:

- **CONCACAF**: México, Estados Unidos, Canadá, Panamá, Haití, Curazao
- **CONMEBOL**: Argentina, Brasil, Uruguay, Colombia, Paraguay, Ecuador
- **UEFA**: España, Alemania, Francia, Inglaterra, Portugal, Países Bajos, Bélgica, Croacia, Suiza, Austria, Noruega
- **AFC**: Japón, Corea del Sur, Arabia Saudita, Irán, Australia, Qatar, Jordania, Uzbekistán
- **CAF**: Marruecos, Senegal, Túnez, Ghana, Egipto, Argelia, Costa de Marfil, Cabo Verde, Sudáfrica, Seychelles
- **OFC**: Nueva Zelanda

### Banderas Faltantes (Por Clasificar) ⏳

**19 países aún necesitan imagen de bandera**:

- **CONCACAF** (3): Costa Rica, Jamaica, Honduras
- **CONMEBOL** (4): Chile, Perú, Venezuela, Bolivia
- **UEFA** (10): Italia, Dinamarca, Suecia, Polonia, Serbia, Ucrania, Gales, Escocia, República Checa
- **CAF** (2): Camerún, Nigeria

**Ver detalles completos**: [BANDERAS_FALTANTES.md](BANDERAS_FALTANTES.md)

### Uso de Banderas

Para que las banderas aparezcan correctamente, **usa los nombres exactos de los países** al crear partidos en el panel de administración.

**Ejemplos**:

- ✅ "Argentina" → Muestra bandera PNG
- ✅ "México" → Muestra bandera PNG (con acento)
- ❌ "Mexico" → 🏴 (sin acento, no reconocido)
- ❌ "ARG" → 🏴 (abreviatura, no reconocido)

### Agregar Banderas Faltantes

1. Descarga la imagen PNG (proporción 3:2 recomendada)
2. Guarda en `Quiniela/frontend/public/flags/` con el nombre exacto (ej: `CL.png` para Chile)
3. La bandera aparece automáticamente sin reiniciar

**Lista completa de países**: Ver [BANDERAS.md](BANDERAS.md)

````

## 🔌 API Endpoints

### Usuarios

- `POST /api/users/register` - Registrar nuevo usuario
- `POST /api/users/login` - Iniciar sesión
- `GET /api/users` - Listar usuarios

### Partidos

- `GET /api/matches` - Listar todos los partidos
- `GET /api/matches/{id}` - Obtener un partido
- `POST /api/matches` - Crear partido (admin)
- `PUT /api/matches/{id}` - Actualizar resultado (admin)
- `DELETE /api/matches/{id}` - Eliminar partido (admin)

### Predicciones

- `POST /api/predictions?user_id={id}` - Crear/actualizar predicción
- `GET /api/predictions/user/{user_id}` - Predicciones de un usuario
- `GET /api/predictions/match/{match_id}` - Predicciones de un partido

### Clasificación

- `GET /api/leaderboard` - Tabla de clasificación

## 🎨 Tecnologías Utilizadas

### Backend

- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy**: ORM para base de datos
- **SQLite**: Base de datos ligera
- **Pydantic**: Validación de datos
- **Uvicorn**: Servidor ASGI

### Frontend

- **React 18**: Biblioteca de UI
- **Vite**: Build tool rápido
- **Tailwind CSS**: Framework de CSS utility-first
- **React Router**: Navegación
- **Axios**: Cliente HTTP

## 💡 Consejos de Uso

1. **Primera vez**: Registra un usuario y conviértelo en admin para poder cargar los partidos
2. **Partidos del Mundial**: Usa el panel de admin para crear todos los partidos del mundial
3. **Actualizar Resultados**: Cuando termine un partido real, actualiza el resultado en el panel de admin
4. **Cálculo de Puntos**: Los puntos se calculan automáticamente cuando marcas un partido como finalizado

## 🔐 Seguridad

- Las contraseñas se hashean con SHA256
- CORS habilitado para desarrollo (ajustar en producción)
- Validación de datos con Pydantic
- No se pueden hacer predicciones después de que inicie el partido

## 📝 Notas

- La base de datos SQLite se crea automáticamente al iniciar el backend
- Los datos persisten en el archivo `quiniela.db`
- Para reset completo, elimina el archivo `quiniela.db`

## 🐛 Troubleshooting

**Error: Puerto 8000 ya en uso**

```powershell
# Encuentra y detiene el proceso
Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess | Stop-Process
````

**Error: Puerto 5173 ya en uso**

```powershell
# Encuentra y detiene el proceso
Get-NetTCPConnection -LocalPort 5173 | Select-Object -ExpandProperty OwningProcess | Stop-Process
```

**Backend no conecta con frontend**

- Verifica que el backend esté corriendo en `localhost:8000`
- Verifica la configuración del proxy en `vite.config.js`

## 📄 Licencia

Proyecto personal - Uso libre

## 👨‍💻 Autor

Creado para gestionar quinielas del mundial de forma profesional.

---

¡Disfruta de tu quiniela del mundial! ⚽🏆
#   e n f e l m o r s  
 