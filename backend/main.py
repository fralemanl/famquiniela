from fastapi import File, UploadFile
from fastapi import Request
# ...existing code...
from pydantic import Field
try:
    from .database import SessionLocal, engine, Base
    from .models import User, Match, Prediction, ChampionPrediction
except ImportError:
    from database import SessionLocal, engine, Base
    from models import User, Match, Prediction, ChampionPrediction
import secrets
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional, List
from fastapi import Body
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CLASES Pydantic FALTANTES ---
class PasswordResetRequest(BaseModel):
    password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    champion: str

class UserLogin(BaseModel):
    username: str
    password: str

class MatchCreate(BaseModel):
    team_home: str
    team_away: str
    match_date: str
    score_home: Optional[int] = None
    score_away: Optional[int] = None
    winner: Optional[str] = None
    is_finished: Optional[bool] = False
    phase: Optional[str] = None
    stadium: Optional[str] = None

class MatchUpdate(BaseModel):
    team_home: Optional[str] = None
    team_away: Optional[str] = None
    match_date: Optional[str] = None
    score_home: Optional[int] = None
    score_away: Optional[int] = None
    winner: Optional[str] = None
    is_finished: Optional[bool] = None
    phase: Optional[str] = None
    stadium: Optional[str] = None

class MatchResponse(BaseModel):
    id: int
    team_home: str
    team_away: str
    match_date: str  # ISO string
    score_home: Optional[int]
    score_away: Optional[int]
    winner: Optional[str]
    is_finished: bool
    phase: Optional[str]
    stadium: Optional[str]
    @staticmethod
    def from_orm_force_string(obj):
        # Convierte match_date a string ISO antes de crear el modelo
        return MatchResponse(
            id=obj.id,
            team_home=obj.team_home,
            team_away=obj.team_away,
            match_date=utc_naive_to_iso_z(obj.match_date),
            score_home=obj.score_home,
            score_away=obj.score_away,
            winner=obj.winner,
            is_finished=obj.is_finished,
            phase=obj.phase,
            stadium=getattr(obj, 'stadium', None),
        )
    class Config:
        orm_mode = True

class PredictionCreate(BaseModel):
    match_id: int
    predicted_home: int
    predicted_away: int
    winner: Optional[str] = None

class PredictionResponse(BaseModel):
    id: int
    user_id: int
    match_id: int
    predicted_home: int
    predicted_away: int
    winner: Optional[str]
    points: int
    class Config:
        orm_mode = True

class LeaderboardEntry(BaseModel):
    id: int
    username: str
    empresa: Optional[str] = None
    champion: Optional[str] = None
    total_points: int
    correct_results: int
    correct_scores: int

class AdjustPointsRequest(BaseModel):
    prediction_id: int
    new_points: int
    admin_user_id: int

class ChampionPredictionUpdate(BaseModel):
    team: str
    admin_user_id: int

# Endpoint para ajustar manualmente los puntos de una predicción

# ...existing code...

# (Colocar el endpoint después de la creación de la app y las importaciones)

# ...existing code...
from fastapi import status
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel

# Pydantic para predicción de campeón (debe ir después de importar BaseModel)
class ChampionPredictionCreate(BaseModel):
    team: str

class ChampionPredictionResponse(BaseModel):
    user_id: int
    team: str
    class Config:
        orm_mode = True
from datetime import datetime, timezone
from typing import List, Optional


def parse_iso_to_utc_naive(date_value: str) -> datetime:
    """Parsea ISO 8601 y normaliza a UTC naive para persistencia consistente."""
    dt = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def utc_naive_to_iso_z(dt: Optional[datetime]) -> Optional[str]:
    """Convierte datetime a string ISO 8601 en UTC con sufijo Z."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

# Modelos Pydantic necesarios para endpoints
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    class Config:
        orm_mode = True

# Modelo para actualizar usuario
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    is_admin: Optional[bool] = None
    password: Optional[str] = None

# FastAPI App
app = FastAPI(title="Quiniela Mundial API")

# Cache en memoria para la clasificación (TTL corto para reducir latencia).
LEADERBOARD_CACHE_TTL_SECONDS = int(os.environ.get("LEADERBOARD_CACHE_TTL_SECONDS", "30"))
_leaderboard_cache = {
    "expires_at": 0.0,
    "data": None,
}


def invalidate_leaderboard_cache() -> None:
    _leaderboard_cache["expires_at"] = 0.0
    _leaderboard_cache["data"] = None


def get_cached_leaderboard():
    now_ts = datetime.utcnow().timestamp()
    if _leaderboard_cache["data"] is not None and _leaderboard_cache["expires_at"] > now_ts:
        return _leaderboard_cache["data"]
    return None


def set_cached_leaderboard(leaderboard_payload):
    _leaderboard_cache["data"] = leaderboard_payload
    _leaderboard_cache["expires_at"] = datetime.utcnow().timestamp() + LEADERBOARD_CACHE_TTL_SECONDS


@app.get("/")
def root_status():
    return {"status": "ok", "service": "famquiniela-backend"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
def run_migrations():
    """Crea tablas si no existen y agrega columnas nuevas (migracion automatica)."""
    from sqlalchemy import text
    try:
        from .database import Base as _Base, engine as _engine, SessionLocal as _SessionLocal
    except ImportError:
        from database import Base as _Base, engine as _engine, SessionLocal as _SessionLocal
    # Crear todas las tablas si la BD está vacía o es nueva
    _Base.metadata.create_all(bind=_engine)
    # Migraciones: agregar columnas nuevas si no existen
    migrations = [
        "ALTER TABLE users ADD COLUMN empresa TEXT",
        "ALTER TABLE users ADD COLUMN reset_token TEXT",
        "ALTER TABLE users ADD COLUMN reset_token_expires DATETIME",
    ]
    db = _SessionLocal()
    try:
        for sql in migrations:
            try:
                db.execute(text(sql))
                db.commit()
            except Exception:
                db.rollback()  # Columna ya existe
    finally:
        db.close()

# CORS
cors_origins_env = os.environ.get("CORS_ORIGINS", "")
cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
frontend_url = os.environ.get("FRONTEND_URL", "").strip()
required_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://famquiniela.vercel.app",
    "https://pnp-quiniela.vercel.app",
]

if not cors_origins:
    cors_origins = required_origins.copy()

for origin in required_origins:
    if origin not in cors_origins:
        cors_origins.append(origin)

if frontend_url and frontend_url not in cors_origins:
    cors_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    # Keep APIs reachable from Vercel previews and production even when origin vars drift.
    allow_origins=["*"],
    allow_origin_regex=r"https://.*\.vercel\.app$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint para obtener la predicción de campeón de un usuario
@app.get("/api/champion/{user_id}", response_model=ChampionPredictionResponse)
def get_champion_prediction(user_id: int, db: Session = Depends(get_db)):
    champion = db.query(ChampionPrediction).filter(ChampionPrediction.user_id == user_id).first()
    if not champion:
        raise HTTPException(status_code=404, detail="Predicción de campeón no encontrada")
    return champion

@app.put("/api/champion/{user_id}", response_model=ChampionPredictionResponse)
def update_champion_prediction(user_id: int, champion_update: ChampionPredictionUpdate, db: Session = Depends(get_db)):
    admin_user = db.query(User).filter(
        User.id == champion_update.admin_user_id,
        User.is_admin == True,
    ).first()
    if not admin_user:
        raise HTTPException(status_code=403, detail="Solo un administrador puede cambiar la predicción de campeón.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    champion = db.query(ChampionPrediction).filter(ChampionPrediction.user_id == user_id).first()
    if champion:
        champion.team = champion_update.team
    else:
        champion = ChampionPrediction(user_id=user_id, team=champion_update.team)
        db.add(champion)

    db.commit()
    db.refresh(champion)
    invalidate_leaderboard_cache()
    return champion

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# Update user endpoint
@app.put("/api/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.is_admin is not None:
        user.is_admin = user_update.is_admin
    if user_update.password is not None:
        user.password = hash_password(user_update.password)
    db.commit()
    db.refresh(user)
    invalidate_leaderboard_cache()
    return user

@app.post("/api/users/{user_id}/reset_password")
def reset_password_admin(user_id: int, req: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.password = hash_password(req.password)
    db.commit()
    db.refresh(user)
    return {"detail": "Contraseña actualizada"}


class ForgotPasswordRequest(BaseModel):
    email: str


@app.post("/api/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    # Respuesta genérica para no filtrar si el email existe o no
    if not user:
        return {"detail": "Si el email existe, recibirás un enlace."}

    token = secrets.token_urlsafe(32)
    from datetime import datetime
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/reset-password/{token}"

    html_body = f"""
    <html><body style="font-family:sans-serif;background:#0f172a;color:#e2e8f0;padding:32px">
      <h2 style="color:#22c55e">World Cup 2026 Contest</h2>
      <p>Hi <strong>{user.username}</strong>,</p>
      <p>Click the button below to reset your password. This link expires in <strong>1 hour</strong>.</p>
      <a href="{reset_link}" style="display:inline-block;background:#22c55e;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;margin:16px 0">Reset Password</a>
      <p style="color:#94a3b8;font-size:12px">Or copy this link: {reset_link}</p>
      <p style="color:#94a3b8;font-size:12px">If you did not request this, ignore this email.</p>
    </body></html>
    """

    resend_api_key = os.environ.get("RESEND_API_KEY", "")
    if resend_api_key:
        # Usar Resend (funciona en Railway sin bloqueo SMTP)
        try:
            import resend as resend_lib
            resend_lib.api_key = resend_api_key
            from_addr = os.environ.get("EMAIL_FROM", "onboarding@resend.dev")
            resend_lib.Emails.send({
                "from": from_addr,
                "to": user.email,
                "subject": "Reset your password - World Cup 2026 Contest",
                "html": html_body,
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error enviando email: {str(e)}")
    else:
        # Fallback SMTP
        smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER", "")
        smtp_pass = os.environ.get("SMTP_PASS", "")
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reset your password - World Cup 2026 Contest"
        msg["From"] = smtp_user
        msg["To"] = user.email
        msg.attach(MIMEText(html_body, "html"))
        try:
            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_user, user.email, msg.as_string())
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_user, user.email, msg.as_string())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error enviando email: {str(e)}")

    return {"detail": "Si el email existe, recibirás un enlace."}


@app.post("/api/generate-reset-link/{user_id}")
def generate_reset_link(user_id: int, db: Session = Depends(get_db)):
    """Genera un link de reset para que el admin se lo mande manualmente al usuario."""
    from datetime import datetime
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/reset-password/{token}"
    return {"link": reset_link, "expires_in": "24 horas"}


@app.post("/api/reset-password/{token}")
def confirm_reset_password(token: str, req: PasswordResetRequest, db: Session = Depends(get_db)):
    from datetime import datetime
    user = db.query(User).filter(User.reset_token == token).first()
    if not user or not user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    if datetime.utcnow() > user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Token expirado")
    user.password = hash_password(req.password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    return {"detail": "Contraseña actualizada correctamente"}
@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(user)
    db.commit()
    invalidate_leaderboard_cache()
    return {"detail": "Usuario eliminado"}
@app.post("/api/users/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Usuario o email ya existe")

    # Crear nuevo usuario
    db_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        is_admin=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Guardar predicción de campeón
    champion_prediction = ChampionPrediction(user_id=db_user.id, team=user.champion)
    db.add(champion_prediction)
    db.commit()
    invalidate_leaderboard_cache()

    return db_user

@app.post("/api/users/login", response_model=UserResponse)
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == credentials.username).first()
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")

        # Soporte para migración automática SHA-256 → bcrypt
        # Hash SHA-256 tiene 64 caracteres hex; bcrypt empieza con $2b$
        import hashlib as _hl
        sha256_hash = _hl.sha256(credentials.password.encode()).hexdigest()
        if user.password == sha256_hash:
            # Contraseña correcta con SHA-256: migrar a bcrypt
            user.password = hash_password(credentials.password)
            db.commit()
            db.refresh(user)
        elif not verify_password(credentials.password, user.password):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        return user
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Error interno en login")

@app.get("/api/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# Endpoints de Partidos
@app.post("/api/reset_all", status_code=status.HTTP_200_OK)
def reset_all(db: Session = Depends(get_db), admin_user_id: int = None):
    """
    Elimina todos los partidos, predicciones y predicción de campeón. Solo para admins.
    admin_user_id: Debe ser el ID de un usuario admin (proteger en frontend y backend si es necesario).
    """
    if admin_user_id is None:
        raise HTTPException(status_code=400, detail="Se requiere el ID de usuario admin")
    admin = db.query(User).filter(User.id == admin_user_id, User.is_admin == True).first()
    if not admin:
        raise HTTPException(status_code=403, detail="Solo los administradores pueden resetear todo")

    # Eliminar predicciones de campeón
    db.query(ChampionPrediction).delete()
    # Eliminar predicciones
    db.query(Prediction).delete()
    # NO eliminar partidos
    db.commit()
    invalidate_leaderboard_cache()
    return {"message": "Todos los puntajes y campeón han sido reseteados, los partidos se mantienen"}
@app.post("/api/matches", response_model=MatchResponse)
def create_match(match: MatchCreate, db: Session = Depends(get_db)):
    match_data = match.dict()
    # Convertir string ISO a datetime si es necesario
    if isinstance(match_data["match_date"], str):
        # Soporta offsets y normaliza a UTC
        match_data["match_date"] = parse_iso_to_utc_naive(match_data["match_date"])
    db_match = Match(**match_data)
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    invalidate_leaderboard_cache()
    return MatchResponse.from_orm_force_string(db_match)


@app.get("/api/matches", response_model=List[MatchResponse])
def get_matches(db: Session = Depends(get_db)):
    matches = db.query(Match).order_by(Match.match_date).all()
    return [MatchResponse.from_orm_force_string(m) for m in matches]


@app.get("/api/matches/{match_id}", response_model=MatchResponse)
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return MatchResponse.from_orm_force_string(match)

@app.put("/api/matches/{match_id}", response_model=MatchResponse)
def update_match(match_id: int, match_update: MatchUpdate, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    
    # Solo permitir modificar equipos, goles, estadio y finalizar partido
    if hasattr(match_update, 'team_home') and match_update.team_home is not None:
        match.team_home = match_update.team_home
    if hasattr(match_update, 'team_away') and match_update.team_away is not None:
        match.team_away = match_update.team_away
    if match_update.match_date is not None:
        try:
            if isinstance(match_update.match_date, str):
                match.match_date = parse_iso_to_utc_naive(match_update.match_date)
            else:
                match.match_date = match_update.match_date
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa ISO 8601")
    if match_update.score_home is not None or match_update.score_home == 0:
        match.score_home = match_update.score_home
    if match_update.score_away is not None or match_update.score_away == 0:
        match.score_away = match_update.score_away
    if match_update.winner is not None:
        match.winner = match_update.winner
    if match_update.stadium is not None:
        match.stadium = match_update.stadium
    if match_update.is_finished is not None:
        match.is_finished = match_update.is_finished
        if match.is_finished:
            calculate_points_for_match(match_id, db)

    db.commit()
    db.refresh(match)
    invalidate_leaderboard_cache()
    return MatchResponse.from_orm_force_string(match)

@app.delete("/api/matches/{match_id}")
def delete_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    db.delete(match)
    db.commit()
    invalidate_leaderboard_cache()
    return {"message": "Partido eliminado"}

# Endpoints de Predicciones


@app.post("/api/predictions", response_model=PredictionResponse)
def create_prediction(prediction: PredictionCreate, user_id: int, db: Session = Depends(get_db)):
    # Verificar si el partido existe
    match = db.query(Match).filter(Match.id == prediction.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
        # Verificar si el partido ya comenzó
    # Verificar si el partido ya comenzó
    if match.is_finished or datetime.utcnow() > match.match_date:
        raise HTTPException(status_code=400, detail="No se pueden hacer predicciones para partidos que ya comenzaron")

    # Calcular winner automáticamente en fase de grupos si no lo envía el usuario
    import unicodedata
    def normalize_phase(phase):
        if not phase:
            return ""
        # Quitar tildes y espacios, minúsculas
        nfkd = unicodedata.normalize("NFKD", phase)
        only_ascii = "".join([c for c in nfkd if not unicodedata.combining(c)])
        return only_ascii.replace(" ", "").lower()

    phase = match.phase or "Fase de Grupos"
    knockout_phases = [
        "dieciseisavos",
        "octavos",
        "octavosdefinal",
        "octavos de final",
        "cuartos",
        "cuartosdefinal",
        "cuartos de final",
        "cuartosdefinales",
        "semifinal",
        "semifinales",
        "final",
        "tercerlugar",
        "tercer lugar",
        "tercerpuesto",
        "tercer puesto"
    ]
    knockout_phases = [normalize_phase(p) for p in knockout_phases]
    norm_phase = normalize_phase(phase)
    winner_value = getattr(prediction, "winner", None)
    if norm_phase not in knockout_phases:
        # Solo para fase de grupos
        if winner_value is None:
            if prediction.predicted_home is not None and prediction.predicted_away is not None:
                if prediction.predicted_home > prediction.predicted_away:
                    winner_value = match.team_home
                elif prediction.predicted_home < prediction.predicted_away:
                    winner_value = match.team_away
                else:
                    winner_value = "Empate"
    else:
        # Para knockout, calcular siempre el winner aunque no sea empate
        if prediction.predicted_home is not None and prediction.predicted_away is not None:
            if prediction.predicted_home > prediction.predicted_away:
                winner_value = match.team_home
            elif prediction.predicted_home < prediction.predicted_away:
                winner_value = match.team_away
            else:
                winner_value = prediction.winner  # En empate, usar el seleccionado en penales

    # Verificar si ya existe una predicción
    existing = db.query(Prediction).filter(
        Prediction.user_id == user_id,
        Prediction.match_id == prediction.match_id
    ).first()

    if existing:
        # Actualizar predicción existente
        existing.predicted_home = prediction.predicted_home
        existing.predicted_away = prediction.predicted_away
        if norm_phase not in knockout_phases:
            if prediction.predicted_home is not None and prediction.predicted_away is not None:
                if prediction.predicted_home > prediction.predicted_away:
                    existing.winner = match.team_home
                elif prediction.predicted_home < prediction.predicted_away:
                    existing.winner = match.team_away
                else:
                    existing.winner = "Empate"
            else:
                existing.winner = None
        else:
            # Para knockout, calcular siempre el winner aunque no sea empate
            if prediction.predicted_home is not None and prediction.predicted_away is not None:
                if prediction.predicted_home > prediction.predicted_away:
                    existing.winner = match.team_home
                elif prediction.predicted_home < prediction.predicted_away:
                    existing.winner = match.team_away
                else:
                    existing.winner = prediction.winner  # En empate, usar el seleccionado en penales
            else:
                existing.winner = None
        db.commit()
        db.refresh(existing)
        invalidate_leaderboard_cache()
        return existing
    # Crear nueva predicción
    db_prediction = Prediction(
        user_id=user_id,
        match_id=prediction.match_id,
        predicted_home=prediction.predicted_home,
        predicted_away=prediction.predicted_away,
        winner=winner_value
    )
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    invalidate_leaderboard_cache()
    return db_prediction

@app.get("/api/predictions/user/{user_id}", response_model=List[PredictionResponse])
def get_user_predictions(user_id: int, db: Session = Depends(get_db)):
    predictions = db.query(Prediction).filter(Prediction.user_id == user_id).all()
    # Filtrar predicciones con match_id nulo
    return [p for p in predictions if p.match_id is not None]

@app.get("/api/predictions/match/{match_id}", response_model=List[PredictionResponse])
def get_match_predictions(match_id: int, db: Session = Depends(get_db)):
    return db.query(Prediction).filter(Prediction.match_id == match_id).all()

from fastapi import status

# Endpoint para ajustar manualmente los puntos de una predicción
@app.post("/api/predictions/adjust_points", status_code=status.HTTP_200_OK)
def adjust_prediction_points(request: AdjustPointsRequest, db: Session = Depends(get_db)):
    # Verificar que el usuario admin existe y es admin
    admin_user = db.query(User).filter(User.id == request.admin_user_id, User.is_admin == True).first()
    if not admin_user:
        raise HTTPException(status_code=403, detail="Solo un administrador puede ajustar los puntos.")
    prediction = db.query(Prediction).filter(Prediction.id == request.prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Predicción no encontrada.")
    prediction.points = request.new_points
    db.commit()
    db.refresh(prediction)
    invalidate_leaderboard_cache()
    return {"detail": f"Puntos actualizados a {request.new_points} para la predicción {request.prediction_id}"}

# Endpoint de exportación de predicciones
@app.get("/api/export/predictions")
def export_predictions(db: Session = Depends(get_db)):
    predictions = db.query(Prediction).filter(Prediction.match_id != None).all()
    pred_rows = []
    for p in predictions:
        user = db.query(User).filter(User.id == p.user_id).first()
        match = db.query(Match).filter(Match.id == p.match_id).first()
        if not user or not match:
            continue
        pred_rows.append({
            "ID Prediccion": p.id,
            "ID Usuario": p.user_id,
            "Usuario": user.username,
            "Email": user.email,
            "Empresa": getattr(user, 'empresa', '') or "",
            "ID Partido": p.match_id,
            "Local": match.team_home,
            "Visitante": match.team_away,
            "Fecha": match.match_date.isoformat() if match.match_date else "",
            "Estadio": match.stadium or "",
            "Fase": match.phase or "",
            "Pred. Local": p.predicted_home,
            "Pred. Visitante": p.predicted_away,
            "Ganador Pred.": p.winner or "",
            "Resultado Real Local": match.score_home if match.is_finished else "",
            "Resultado Real Visitante": match.score_away if match.is_finished else "",
            "Partido Finalizado": "Si" if match.is_finished else "No",
            "Ganador Real": match.winner or "",
            "Puntos": p.points,
        })

    # Hoja de usuarios con empresa y campeon
    users = db.query(User).all()
    user_rows = []
    for user in users:
        champion = user.champion_prediction.team if user.champion_prediction else ""
        user_rows.append({
            "ID": user.id,
            "Usuario": user.username,
            "Email": user.email,
            "Empresa": getattr(user, 'empresa', '') or "",
            "Campeon Predicho": champion,
            "Es Admin": "Si" if user.is_admin else "No",
        })

    return {"predicciones": pred_rows, "usuarios": user_rows}

# Endpoint de Clasificación
@app.get("/api/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(db: Session = Depends(get_db)):
    cached_leaderboard = get_cached_leaderboard()
    if cached_leaderboard is not None:
        return cached_leaderboard

    users = db.query(User).filter(User.is_admin == False).all()
    if not users:
        return []

    # Sistema de puntaje por fase para contar aciertos de marcador exacto y ganador.
    phase_points = {
        "Fase de Grupos": {"exacto": 5, "ganador": 3, "parcial": 1},
        "Dieciseisavos": {"exacto": 6, "ganador": 3},
        "Octavos": {"exacto": 7, "ganador": 4},
        "Cuartos": {"exacto": 9, "ganador": 5},
        "Semifinal": {"exacto": 12, "ganador": 6},
        "Final": {"exacto": 15, "ganador": 8},
        "Tercer Lugar": {"exacto": 10, "ganador": 5},
    }

    # Total de puntos por usuario en partidos finalizados.
    total_points_rows = (
        db.query(
            Prediction.user_id,
            func.coalesce(func.sum(Prediction.points), 0).label("total_points")
        )
        .join(Match, Match.id == Prediction.match_id)
        .filter(Match.is_finished == True)
        .group_by(Prediction.user_id)
        .all()
    )
    total_points_by_user = {row.user_id: int(row.total_points or 0) for row in total_points_rows}

    # Agrupar por usuario + fase + puntos para evitar N+1 de partidos/predicciones.
    grouped_prediction_rows = (
        db.query(
            Prediction.user_id,
            Match.phase,
            Prediction.points,
            func.count(Prediction.id).label("qty")
        )
        .join(Match, Match.id == Prediction.match_id)
        .filter(Match.is_finished == True)
        .group_by(Prediction.user_id, Match.phase, Prediction.points)
        .all()
    )

    correct_scores_by_user = {}
    correct_results_by_user = {}
    for row in grouped_prediction_rows:
        user_id = row.user_id
        phase = row.phase or "Fase de Grupos"
        points = int(row.points or 0)
        qty = int(row.qty or 0)

        if phase in phase_points:
            if points == phase_points[phase].get("exacto"):
                correct_scores_by_user[user_id] = correct_scores_by_user.get(user_id, 0) + qty
            elif points == phase_points[phase].get("ganador"):
                correct_results_by_user[user_id] = correct_results_by_user.get(user_id, 0) + qty

    # Bonus de campeón (+15) en bloque.
    champion_rows = db.query(ChampionPrediction.user_id, ChampionPrediction.team).all()
    champion_by_user = {row.user_id: row.team for row in champion_rows}

    final_winner_row = (
        db.query(Match.winner)
        .filter(Match.phase == "Final", Match.is_finished == True, Match.winner != None)
        .order_by(Match.id.desc())
        .first()
    )
    champion_bonus_users = set()
    if final_winner_row and final_winner_row.winner:
        champion_bonus_users = {
            user_id for user_id, team in champion_by_user.items() if team == final_winner_row.winner
        }

    leaderboard = []
    for user in users:
        total_points = total_points_by_user.get(user.id, 0)
        if user.id in champion_bonus_users:
            total_points += 15

        leaderboard.append(
            LeaderboardEntry(
                id=user.id,
                username=user.username,
                empresa=getattr(user, "empresa", None),
                champion=champion_by_user.get(user.id),
                total_points=total_points,
                correct_results=correct_results_by_user.get(user.id, 0),
                correct_scores=correct_scores_by_user.get(user.id, 0),
            )
        )

    leaderboard.sort(key=lambda x: x.total_points, reverse=True)
    set_cached_leaderboard([entry.dict() for entry in leaderboard])
    return leaderboard

# Función auxiliar para calcular puntos
def calculate_points_for_match(match_id: int, db: Session):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match or not match.is_finished:
        return
    
    predictions = db.query(Prediction).filter(Prediction.match_id == match_id).all()
    
    # Sistema de puntaje por fase
    phase_points = {
        "Fase de Grupos": {"exacto": 5, "ganador": 3, "parcial": 1},
        "Dieciseisavos": {"exacto": 6, "ganador": 3},
        "Octavos": {"exacto": 7, "ganador": 4},
        "Cuartos": {"exacto": 9, "ganador": 5},
        "Semifinal": {"exacto": 12, "ganador": 6},
        "Final": {"exacto": 15, "ganador": 8},
        "Tercer Lugar": {"exacto": 10, "ganador": 5},
    }
    import unicodedata
    def normalize_phase(phase):
        if not phase:
            return ""
        nfkd = unicodedata.normalize("NFKD", phase)
        only_ascii = "".join([c for c in nfkd if not unicodedata.combining(c)])
        return only_ascii.replace(" ", "").lower()

    phase = match.phase or "Fase de Grupos"
    norm_phase = normalize_phase(phase)
    # Mapeo de fases normalizadas a claves de phase_points
    phase_map = {
        normalize_phase("Fase de Grupos"): "Fase de Grupos",
        normalize_phase("Dieciseisavos"): "Dieciseisavos",
        normalize_phase("Octavos"): "Octavos",
        normalize_phase("Octavos de Final"): "Octavos",
        normalize_phase("Cuartos"): "Cuartos",
        normalize_phase("Cuartos de Final"): "Cuartos",
        normalize_phase("Semifinal"): "Semifinal",
        normalize_phase("Final"): "Final",
        normalize_phase("Tercer Lugar"): "Tercer Lugar",
        normalize_phase("Tercer Puesto"): "Tercer Lugar",
    }
    knockout_phases = [normalize_phase(p) for p in [
        "Dieciseisavos",
        "Octavos",
        "Octavos de Final",
        "Cuartos",
        "Cuartos de Final",
        "Semifinal",
        "Final",
        "Tercer Lugar",
        "Tercer Puesto"
    ]]
    for prediction in predictions:
        points = 0
        # Usar la clave normalizada para acceder a phase_points
        phase_key = phase_map.get(norm_phase, "Fase de Grupos")
        if norm_phase == normalize_phase("Dieciseisavos"):
            # 3 puntos por acertar el ganador
            if prediction.winner and match.winner and prediction.winner == match.winner:
                points += 3
            # 3 puntos adicionales si acierta ambos goles
            if prediction.predicted_home == match.score_home and prediction.predicted_away == match.score_away:
                points += 3
        elif norm_phase in knockout_phases:
            # Marcador exacto KO y Tercer Lugar
            if (
                prediction.predicted_home == match.score_home and
                prediction.predicted_away == match.score_away
            ):
                points = phase_points[phase_key]["exacto"]
            # Ganador KO y Tercer Lugar (incluye empate solo en fases que lo permiten)
            elif (
                (prediction.winner and match.winner and prediction.winner == match.winner)
            ):
                points = phase_points[phase_key]["ganador"]
        else:
            # Fase de grupos: sistema personalizado
            points = 0
            # 3 puntos si acierta el ganador (Empate, Local o Visitante)
            if prediction.winner and match.winner and prediction.winner == match.winner:
                points += 3
            # 1 punto por cada gol acertado
            if prediction.predicted_home == match.score_home:
                points += 1
            if prediction.predicted_away == match.score_away:
                points += 1
            # Máximo 5 puntos
            if points > 5:
                points = 5
        prediction.points = points
    
    db.commit()
    
from fastapi.responses import FileResponse

@app.get("/download-db")
def download_db():
    db_path = "/tmp/quiniela.db"  # O usa "/tmp/quiniela.db" si tu db está ahí
    return FileResponse(db_path, filename="quiniela.db")

@app.post("/api/import-matches")
async def import_matches(request: Request, db: Session = Depends(get_db)):
    admin_user_id = request.headers.get("admin_user_id")
    if not admin_user_id:
        raise HTTPException(status_code=400, detail="Se requiere admin_user_id en headers")
    admin = db.query(User).filter(User.id == int(admin_user_id), User.is_admin == True).first()
    if not admin:
        raise HTTPException(status_code=403, detail="Solo los administradores pueden importar partidos")
    data = await request.json()
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="El JSON debe ser una lista de partidos")
    imported = 0
    for match in data:
        exists = db.query(Match).filter(
            (Match.team_home == match.get("team_home")) &
            (Match.team_away == match.get("team_away")) &
            (Match.match_date == match.get("match_date"))
        ).first()
        if exists:
            continue
        match_data = {k: v for k, v in match.items() if k != "id"}
        if isinstance(match_data.get("match_date"), str):
            match_data["match_date"] = datetime.fromisoformat(match_data["match_date"].replace("Z", "+00:00"))
        db_match = Match(**match_data)
        db.add(db_match)
        imported += 1
    db.commit()
    if imported > 0:
        invalidate_leaderboard_cache()
    return {"imported": imported, "total": len(data)}

@app.get("/")
def root():
    return {"message": "Quiniela Mundial API - Bienvenido!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
