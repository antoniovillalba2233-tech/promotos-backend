from fastapi import FastAPI, APIRouter, HTTPException, Header, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
import certifi
client = AsyncIOMotorClient(mongo_url, tlsCAFile=certifi.where())
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

from fastapi.responses import HTMLResponse

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    """Panel web simple para aprobar/rechazar pagos manuales (CBU/AstroPay/WhatsApp)."""
    html_path = ROOT_DIR / "static_admin.html"
    return html_path.read_text(encoding="utf-8")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============= MODELS =============

class User(BaseModel):
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email: str
    name: str
    picture: Optional[str] = None
    password_hash: Optional[str] = None
    is_premium: bool = False  # true = compró el curso completo (acceso de por vida)
    credits: int = 0  # saldo de créditos (1 crédito = US$1 = 1 lección)
    unlocked_lessons: List[str] = []  # lesson_ids desbloqueados individualmente
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    session_token: str
    user_id: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionRequest(BaseModel):
    session_token: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class Module(BaseModel):
    module_id: str
    title: str
    description: str
    order: int
    lessons: List[str] = []  # lesson_ids
    exam_id: Optional[str] = None

class Lesson(BaseModel):
    lesson_id: str = Field(default_factory=lambda: f"lesson_{uuid.uuid4().hex[:12]}")
    module_id: str
    title: str
    duration: str
    video_url: str
    order: int
    is_free: bool = False

class Question(BaseModel):
    question_id: str = Field(default_factory=lambda: f"q_{uuid.uuid4().hex[:12]}")
    text: str
    type: str  # "multiple_choice" or "true_false"
    options: List[str]  # For multiple choice
    correct_answer: str

class Exam(BaseModel):
    exam_id: str = Field(default_factory=lambda: f"exam_{uuid.uuid4().hex[:12]}")
    module_id: str
    title: str
    questions: List[Question]
    passing_score: int = 70

class UserProgress(BaseModel):
    progress_id: str = Field(default_factory=lambda: f"prog_{uuid.uuid4().hex[:12]}")
    user_id: str
    lesson_id: str
    completed: bool = False
    completed_at: Optional[datetime] = None

class ExamResult(BaseModel):
    result_id: str = Field(default_factory=lambda: f"result_{uuid.uuid4().hex[:12]}")
    user_id: str
    exam_id: str
    module_id: str
    score: int
    passed: bool
    answers: Dict[str, str]
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ExamSubmission(BaseModel):
    exam_id: str
    answers: Dict[str, str]

# PayPal Models
# ============= AUTH HELPER =============

def is_user_premium(user: Optional[Dict]) -> bool:
    """True si el usuario tiene acceso al curso completo (compra de por vida o suscripción activa)"""
    if not user:
        return False
    if not user.get("is_premium", False):
        return False

    expires_at = user.get("premium_expires_at")
    if expires_at is None:
        # Sin fecha de vencimiento = acceso de por vida (compra del curso completo)
        return True

    if isinstance(expires_at, datetime):
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at > datetime.now(timezone.utc)

    return False

def has_lesson_access(user: Optional[Dict], lesson: Dict) -> bool:
    """True si el usuario puede ver esta lección: es gratis, tiene el curso completo,
    o la desbloqueó individualmente gastando créditos."""
    if lesson.get("is_free"):
        return True
    if is_user_premium(user):
        return True
    if user and lesson.get("lesson_id") in user.get("unlocked_lessons", []):
        return True
    return False

async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[Dict]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    
    # Find session
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        return None
    
    # Check expiration
    expires_at = session.get("expires_at")
    if isinstance(expires_at, datetime):
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return None
    
    # Get user
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    
    # Auto-expire premium if past expiration
    if user and user.get("is_premium") and user.get("premium_expires_at"):
        exp = user["premium_expires_at"]
        if isinstance(exp, datetime):
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < datetime.now(timezone.utc):
                await db.users.update_one(
                    {"user_id": user["user_id"]},
                    {"$set": {"is_premium": False}}
                )
                user["is_premium"] = False
    
    return user

# ============= AUTH ROUTES =============

@api_router.post("/auth/session")
async def create_session(request: SessionRequest):
    """Exchange session_token for user data and store in DB"""
    try:
        # Call Emergent auth API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": request.session_token},
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session token")
            
            data = response.json()
            session_token = data.get("session_token")
            user_data = {
                "email": data.get("email"),
                "name": data.get("name"),
                "picture": data.get("picture")
            }
        
        # Upsert user by email
        existing_user = await db.users.find_one({"email": user_data["email"]}, {"_id": 0})
        
        if existing_user:
            user_id = existing_user["user_id"]
            # Update user info
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "name": user_data["name"],
                    "picture": user_data["picture"]
                }}
            )
        else:
            # Create new user
            new_user = User(**user_data)
            user_id = new_user.user_id
            await db.users.insert_one(new_user.dict())
        
        # Store session
        session = UserSession(
            session_token=session_token,
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        
        # Delete old sessions for this user
        await db.user_sessions.delete_many({"user_id": user_id})
        await db.user_sessions.insert_one(session.dict())
        
        # Get updated user
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        
        return {
            "session_token": session_token,
            "user": user
        }
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Auth service timeout")
    except Exception as e:
        logging.error(f"Session creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@api_router.post("/auth/register")
async def register(request: RegisterRequest):
    """Registro con email y contraseña (no depende de ningún servicio externo)."""
    email = request.email.strip().lower()

    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese email")

    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")

    password_hash = pwd_context.hash(request.password)
    new_user = User(email=email, name=request.name.strip(), password_hash=password_hash)
    await db.users.insert_one(new_user.dict())

    session_token = f"sess_{uuid.uuid4().hex}"
    session = UserSession(
        session_token=session_token,
        user_id=new_user.user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    await db.user_sessions.insert_one(session.dict())

    user = await db.users.find_one({"user_id": new_user.user_id}, {"_id": 0, "password_hash": 0})
    return {"session_token": session_token, "user": user}

@api_router.post("/auth/login")
async def login_with_password(request: LoginRequest):
    """Login con email y contraseña."""
    email = request.email.strip().lower()
    user = await db.users.find_one({"email": email}, {"_id": 0})

    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    if not pwd_context.verify(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    session_token = f"sess_{uuid.uuid4().hex}"
    session = UserSession(
        session_token=session_token,
        user_id=user["user_id"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    await db.user_sessions.delete_many({"user_id": user["user_id"]})
    await db.user_sessions.insert_one(session.dict())

    user.pop("password_hash", None)
    return {"session_token": session_token, "user": user}

@api_router.get("/auth/me")
async def get_me(authorization: Optional[str] = Header(None)):
    """Get current user"""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user

@api_router.post("/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    await db.user_sessions.delete_many({"session_token": token})
    
    return {"message": "Logged out successfully"}

# ============= COURSE ROUTES =============

@api_router.get("/modules")
async def get_modules(authorization: Optional[str] = Header(None)):
    """Get all course modules"""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    modules = await db.modules.find({}, {"_id": 0}).sort("order", 1).to_list(1000)
    
    # Add progress info
    for module in modules:
        lessons = await db.lessons.find(
            {"module_id": module["module_id"]},
            {"_id": 0}
        ).sort("order", 1).to_list(1000)

        locked_count = 0
        for lesson in lessons:
            unlocked = has_lesson_access(user, lesson)
            lesson["unlocked"] = unlocked
            lesson["price_credits"] = 0 if lesson.get("is_free") else 1
            if not unlocked:
                locked_count += 1

        module["lessons"] = lessons
        module["unlock_price_credits"] = locked_count  # costo de desbloquear todo el módulo de una vez
        module["fully_unlocked"] = locked_count == 0
        
        # Calculate progress
        total_lessons = len(lessons)
        if total_lessons > 0:
            completed = await db.user_progress.count_documents({
                "user_id": user["user_id"],
                "lesson_id": {"$in": [l["lesson_id"] for l in lessons]},
                "completed": True
            })
            module["progress"] = int((completed / total_lessons) * 100)
        else:
            module["progress"] = 0
    
    return modules

@api_router.get("/credits/balance")
async def get_credits_balance(authorization: Optional[str] = Header(None)):
    """Devuelve el saldo de créditos del usuario y si tiene el curso completo."""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "credits": user.get("credits", 0),
        "has_full_course": is_user_premium(user),
    }

@api_router.post("/lessons/{lesson_id}/unlock")
async def unlock_lesson(lesson_id: str, authorization: Optional[str] = Header(None)):
    """Gasta 1 crédito para desbloquear una lección puntual."""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    lesson = await db.lessons.find_one({"lesson_id": lesson_id}, {"_id": 0})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if has_lesson_access(user, lesson):
        return {"status": "already_unlocked", "credits": user.get("credits", 0)}

    if user.get("credits", 0) < 1:
        raise HTTPException(status_code=402, detail="No tenés créditos suficientes")

    result = await db.users.update_one(
        {"user_id": user["user_id"], "credits": {"$gte": 1}},
        {
            "$inc": {"credits": -1},
            "$addToSet": {"unlocked_lessons": lesson_id},
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=402, detail="No tenés créditos suficientes")

    updated = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0, "credits": 1})
    return {"status": "unlocked", "credits": updated.get("credits", 0)}

@api_router.post("/modules/{module_id}/unlock")
async def unlock_module(module_id: str, authorization: Optional[str] = Header(None)):
    """Gasta créditos (1 por cada lección bloqueada) para desbloquear todo el módulo."""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    module = await db.modules.find_one({"module_id": module_id}, {"_id": 0})
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    lessons = await db.lessons.find({"module_id": module_id}, {"_id": 0}).to_list(1000)
    locked_ids = [l["lesson_id"] for l in lessons if not has_lesson_access(user, l)]

    if not locked_ids:
        return {"status": "already_unlocked", "credits": user.get("credits", 0)}

    cost = len(locked_ids)
    if user.get("credits", 0) < cost:
        raise HTTPException(status_code=402, detail=f"Necesitás {cost} créditos, tenés {user.get('credits', 0)}")

    result = await db.users.update_one(
        {"user_id": user["user_id"], "credits": {"$gte": cost}},
        {
            "$inc": {"credits": -cost},
            "$addToSet": {"unlocked_lessons": {"$each": locked_ids}},
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=402, detail="No tenés créditos suficientes")

    updated = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0, "credits": 1})
    return {"status": "unlocked", "credits": updated.get("credits", 0), "lessons_unlocked": len(locked_ids)}

@api_router.post("/course/unlock-full")
async def unlock_full_course(authorization: Optional[str] = Header(None)):
    """Gasta créditos (1 por cada lección premium restante en TODO el curso) para
    desbloquear el curso completo de por vida."""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if is_user_premium(user):
        return {"status": "already_unlocked", "credits": user.get("credits", 0)}

    all_lessons = await db.lessons.find({}, {"_id": 0}).to_list(10000)
    locked_ids = [l["lesson_id"] for l in all_lessons if not has_lesson_access(user, l)]
    cost = len(locked_ids)

    if user.get("credits", 0) < cost:
        raise HTTPException(status_code=402, detail=f"Necesitás {cost} créditos, tenés {user.get('credits', 0)}")

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {
            "$inc": {"credits": -cost},
            "$set": {"is_premium": True, "premium_expires_at": None},
        }
    )
    updated = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0, "credits": 1})
    return {"status": "unlocked", "credits": updated.get("credits", 0)}

@api_router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: str, authorization: Optional[str] = Header(None)):
    """Get a specific lesson"""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    lesson = await db.lessons.find_one({"lesson_id": lesson_id}, {"_id": 0})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Check if user has access (gratis, curso completo, o desbloqueada con créditos)
    if not has_lesson_access(user, lesson):
        return {**lesson, "locked": True, "video_url": None}
    
    # Get progress
    progress = await db.user_progress.find_one({
        "user_id": user["user_id"],
        "lesson_id": lesson_id
    }, {"_id": 0})
    
    return {**lesson, "locked": False, "completed": progress["completed"] if progress else False}

@api_router.post("/lessons/{lesson_id}/complete")
async def mark_lesson_complete(lesson_id: str, authorization: Optional[str] = Header(None)):
    """Mark a lesson as complete"""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Check if lesson exists
    lesson = await db.lessons.find_one({"lesson_id": lesson_id}, {"_id": 0})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Upsert progress
    await db.user_progress.update_one(
        {"user_id": user["user_id"], "lesson_id": lesson_id},
        {
            "$set": {
                "completed": True,
                "completed_at": datetime.now(timezone.utc)
            },
            "$setOnInsert": {
                "progress_id": f"prog_{uuid.uuid4().hex[:12]}",
                "user_id": user["user_id"],
                "lesson_id": lesson_id
            }
        },
        upsert=True
    )
    
    return {"message": "Lesson marked as complete"}

# ============= EXAM ROUTES =============

@api_router.get("/exams/{exam_id}")
async def get_exam(exam_id: str, authorization: Optional[str] = Header(None)):
    """Get exam questions"""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    exam = await db.exams.find_one({"exam_id": exam_id}, {"_id": 0})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Remove correct answers from response
    questions = []
    for q in exam["questions"]:
        questions.append({
            "question_id": q["question_id"],
            "text": q["text"],
            "type": q["type"],
            "options": q["options"]
        })
    
    return {
        "exam_id": exam["exam_id"],
        "module_id": exam["module_id"],
        "title": exam["title"],
        "questions": questions,
        "passing_score": exam["passing_score"]
    }

@api_router.post("/exams/submit")
async def submit_exam(submission: ExamSubmission, authorization: Optional[str] = Header(None)):
    """Submit exam and get results"""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    exam = await db.exams.find_one({"exam_id": submission.exam_id}, {"_id": 0})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Calculate score
    correct = 0
    total = len(exam["questions"])
    
    for question in exam["questions"]:
        user_answer = submission.answers.get(question["question_id"], "")
        if user_answer.lower() == question["correct_answer"].lower():
            correct += 1
    
    score = int((correct / total) * 100) if total > 0 else 0
    passed = score >= exam["passing_score"]
    
    # Store result
    result = ExamResult(
        user_id=user["user_id"],
        exam_id=submission.exam_id,
        module_id=exam["module_id"],
        score=score,
        passed=passed,
        answers=submission.answers
    )
    
    await db.exam_results.insert_one(result.dict())
    
    return {
        "score": score,
        "passed": passed,
        "correct": correct,
        "total": total
    }

@api_router.get("/progress")
async def get_user_progress(authorization: Optional[str] = Header(None)):
    """Get user's overall progress"""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get all modules
    modules = await db.modules.find({}, {"_id": 0}).to_list(1000)
    
    total_lessons = 0
    completed_lessons = 0
    
    progress_by_module = []
    
    for module in modules:
        lessons = await db.lessons.find({"module_id": module["module_id"]}, {"_id": 0}).to_list(1000)
        lesson_ids = [l["lesson_id"] for l in lessons]
        
        total_lessons += len(lessons)
        
        completed = await db.user_progress.count_documents({
            "user_id": user["user_id"],
            "lesson_id": {"$in": lesson_ids},
            "completed": True
        })
        
        completed_lessons += completed
        
        # Get exam result
        exam_result = None
        if module.get("exam_id"):
            result = await db.exam_results.find_one(
                {"user_id": user["user_id"], "exam_id": module["exam_id"]},
                {"_id": 0},
                sort=[("submitted_at", -1)]
            )
            if result:
                exam_result = {
                    "score": result["score"],
                    "passed": result["passed"]
                }
        
        progress_by_module.append({
            "module_id": module["module_id"],
            "title": module["title"],
            "total_lessons": len(lessons),
            "completed_lessons": completed,
            "progress": int((completed / len(lessons)) * 100) if len(lessons) > 0 else 0,
            "exam_result": exam_result
        })
    
    overall_progress = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
    
    return {
        "user": user,
        "overall_progress": overall_progress,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "modules": progress_by_module
    }

# ============= PAYMENT ROUTES (CBU / AstroPay / WhatsApp) =============

# Plan configurations (Argentina - CBU/AstroPay/WhatsApp)
CREDIT_PACKS = {
    "pack_1": {
        "credits": 1,
        "amount_usd": "1.00",
        "amount_ars": "1000",
        "currency": "USD",
        "description": "Pro Motos - 1 crédito (1 lección)"
    },
    "pack_10": {
        "credits": 10,
        "amount_usd": "10.00",
        "amount_ars": "10000",
        "currency": "USD",
        "description": "Pro Motos - 10 créditos (10 lecciones)"
    },
    "pack_25": {
        "credits": 25,
        "amount_usd": "25.00",
        "amount_ars": "25000",
        "currency": "USD",
        "description": "Pro Motos - 25 créditos (25 lecciones)"
    },
    "full_course": {
        "credits": None,  # se calcula dinámicamente: todas las lecciones premium del curso
        "amount_usd": "129.00",
        "amount_ars": "129000",
        "currency": "USD",
        "description": "Pro Motos - Curso completo (acceso de por vida)"
    }
}

# Payment methods configuration
PAYMENT_METHODS = {
    "cbu": {
        "cbu": "1430001713015367820013",
        "alias": "ser.bru.22",
        "holder": "Sergio Antonio Villalba",
        "bank": "Bruban",
        "instructions": "Transfiere el monto exacto al CBU y envía el comprobante por WhatsApp"
    },
    "astropay": {
        "email": "servillalba.49.sv@gmail.com",
        "cbu_ars": "0000177500099546600465",
        "holder": "Sergio Antonio Villalba",
        "account_number": "848422020650",
        "routing_number": "043087080",
        "swift": "SSBAUS32",
        "account_type": "Corriente (Checking)",
        "bank": "SSB Bank",
        "bank_address": "8700 Perry Hwy, Pittsburgh, Pennsylvania, 15237, USA",
        "instructions": "Transfiere desde AstroPay y envía el comprobante por WhatsApp"
    },
    "whatsapp": {
        "number": "+5491122728226",
        "name": "Sergio",
        "default_message": "Hola! Quiero suscribirme a Pro Motos Solucción"
    }
}

class PaymentRequest(BaseModel):
    plan: str  # "pack_1", "pack_10", "pack_25", or "full_course"
    method: str  # "cbu", "astropay", or "whatsapp"

class ConfirmPaymentRequest(BaseModel):
    payment_id: str
    transfer_reference: Optional[str] = None
    notes: Optional[str] = None

@api_router.get("/payment/config")
async def get_payment_config():
    """Get available payment methods and credit packs (public endpoint)"""
    return {
        "plans": CREDIT_PACKS,
        "methods": PAYMENT_METHODS,
        "currency_ars_symbol": "$",
        "currency_usd_symbol": "US$"
    }

@api_router.post("/payment/request")
async def create_payment_request(request: PaymentRequest, authorization: Optional[str] = Header(None)):
    """Create a pending payment request. User will complete payment via their chosen method."""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if request.plan not in CREDIT_PACKS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    if request.method not in ["cbu", "astropay", "whatsapp"]:
        raise HTTPException(status_code=400, detail="Invalid payment method")
    
    pack = CREDIT_PACKS[request.plan]
    payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    
    payment_record = {
        "payment_id": payment_id,
        "order_id": payment_id,  # keep unique index compat
        "user_id": user["user_id"],
        "user_email": user["email"],
        "user_name": user.get("name", ""),
        "plan": request.plan,
        "method": request.method,
        "amount_usd": float(pack["amount_usd"]),
        "amount_ars": float(pack["amount_ars"]),
        "currency": pack["currency"],
        "status": "pending",  # pending -> verified -> completed | rejected
        "created_at": datetime.now(timezone.utc),
    }
    
    await db.payments.insert_one(payment_record)
    
    # Build WhatsApp confirmation message
    whatsapp_num = PAYMENT_METHODS["whatsapp"]["number"].replace("+", "").replace(" ", "")
    plan_label = pack["description"]
    
    method_data = PAYMENT_METHODS[request.method]
    
    message = (
        f"Hola! Quiero comprar en Pro Motos Solucción.%0A"
        f"Producto: {plan_label}%0A"
        f"Monto: US${pack['amount_usd']} / ${pack['amount_ars']} ARS%0A"
        f"Método: {request.method.upper()}%0A"
        f"ID de Pago: {payment_id}%0A"
        f"Email: {user['email']}"
    )
    whatsapp_url = f"https://wa.me/{whatsapp_num}?text={message}"
    
    return {
        "payment_id": payment_id,
        "plan": request.plan,
        "method": request.method,
        "amount_usd": pack["amount_usd"],
        "amount_ars": pack["amount_ars"],
        "status": "pending",
        "payment_info": method_data,
        "whatsapp_url": whatsapp_url,
        "message": "Pago registrado. Completa la transferencia y confirma por WhatsApp."
    }

@api_router.post("/payment/confirm")
async def confirm_payment(request: ConfirmPaymentRequest, authorization: Optional[str] = Header(None)):
    """User marks payment as sent - awaits admin verification"""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    payment = await db.payments.find_one(
        {"payment_id": request.payment_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment["status"] not in ("pending", "awaiting_verification"):
        raise HTTPException(status_code=400, detail="Payment already processed")
    
    await db.payments.update_one(
        {"payment_id": request.payment_id},
        {"$set": {
            "status": "awaiting_verification",
            "transfer_reference": request.transfer_reference,
            "notes": request.notes,
            "confirmed_at": datetime.now(timezone.utc)
        }}
    )
    
    return {
        "status": "awaiting_verification",
        "message": "Tu pago está siendo verificado. Te activaremos el premium en breve.",
        "payment_id": request.payment_id
    }

@api_router.get("/payment/status/{payment_id}")
async def get_payment_status(payment_id: str, authorization: Optional[str] = Header(None)):
    """Get status of a specific payment"""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    payment = await db.payments.find_one(
        {"payment_id": payment_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {
        "payment_id": payment["payment_id"],
        "status": payment["status"],
        "plan": payment["plan"],
        "method": payment["method"],
        "amount_usd": payment["amount_usd"],
        "amount_ars": payment["amount_ars"]
    }

ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")

@api_router.get("/admin/payments/pending")
async def admin_list_pending_payments(x_admin_secret: Optional[str] = Header(None)):
    """Lista los pagos manuales (CBU/AstroPay/WhatsApp) pendientes de aprobar."""
    if not ADMIN_SECRET or x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    payments = await db.payments.find(
        {"status": {"$in": ["pending", "awaiting_verification"]}, "method": {"$ne": "google_play"}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    return payments

@api_router.post("/admin/payments/{payment_id}/approve")
async def admin_approve_payment(payment_id: str, x_admin_secret: Optional[str] = Header(None)):
    """Aprobar manualmente un pago por CBU/AstroPay/WhatsApp y acreditar los
    créditos (o activar el curso completo) al usuario correspondiente.
    Requiere el header X-Admin-Secret con el valor de la variable de entorno ADMIN_SECRET."""
    if not ADMIN_SECRET or x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    payment = await db.payments.find_one({"payment_id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment["status"] == "completed":
        return {"status": "already_completed"}

    plan_id = payment["plan"]
    pack = CREDIT_PACKS.get(plan_id)
    if not pack:
        raise HTTPException(status_code=400, detail="Plan desconocido en este pago")

    if plan_id == "full_course":
        await db.users.update_one(
            {"user_id": payment["user_id"]},
            {"$set": {"is_premium": True, "premium_expires_at": None}}
        )
    else:
        await db.users.update_one(
            {"user_id": payment["user_id"]},
            {"$inc": {"credits": pack["credits"]}}
        )

    await db.payments.update_one(
        {"payment_id": payment_id},
        {"$set": {"status": "completed", "approved_at": datetime.now(timezone.utc)}}
    )
    return {"status": "completed", "plan": plan_id}

@api_router.post("/admin/payments/{payment_id}/reject")
async def admin_reject_payment(payment_id: str, x_admin_secret: Optional[str] = Header(None)):
    """Rechazar un pago manual (por ejemplo si el comprobante no es válido)."""
    if not ADMIN_SECRET or x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    payment = await db.payments.find_one({"payment_id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    await db.payments.update_one(
        {"payment_id": payment_id},
        {"$set": {"status": "rejected", "rejected_at": datetime.now(timezone.utc)}}
    )
    return {"status": "rejected"}

@api_router.get("/payment/my-payments")
async def get_my_payments(authorization: Optional[str] = Header(None)):
    """Get user's payment history"""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    payments = await db.payments.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return payments

# ============= GOOGLE PLAY BILLING (RevenueCat) =============
#
# RevenueCat notifica a este endpoint cada vez que ocurre un evento de
# suscripción real en Google Play (compra inicial, renovación, cancelación,
# reembolso, etc). Así el backend se mantiene sincronizado con Google sin que
# el celular del usuario tenga que estar conectado en ese momento.
#
# Setup pendiente:
# 1. En el dashboard de RevenueCat: Project Settings > Integrations > Webhooks
# 2. URL del webhook: https://TU_BACKEND/api/payment/revenuecat-webhook
# 3. Copiar el "Authorization header" que genera RevenueCat y ponerlo en la
#    variable de entorno REVENUECAT_WEBHOOK_SECRET
# 4. IMPORTANTE: en el SDK del frontend (billing.ts), configurar RevenueCat
#    con appUserID = user_id de tu propio sistema (el mismo que usás en el
#    JWT/session token), para que este webhook pueda encontrar al usuario.
# 5. Productos a crear en Google Play Console (todos como "producto administrado"
#    o "producto consumible" según corresponda):
#    - "credits_1"  (consumible) -> 1 crédito  -> US$1
#    - "credits_10" (consumible) -> 10 créditos -> US$10
#    - "full_course" (no consumible, compra única) -> acceso de por vida

REVENUECAT_WEBHOOK_SECRET = os.environ.get("REVENUECAT_WEBHOOK_SECRET", "")

# Cuántos créditos otorga cada producto consumible
CREDIT_PRODUCTS = {
    "credits_1": 1,
    "credits_10": 10,
    "credits_25": 25,
}

# Productos que dan acceso de por vida al curso completo directamente
FULL_COURSE_PRODUCTS = {"full_course"}

@api_router.post("/payment/revenuecat-webhook")
async def revenuecat_webhook(request: Request, authorization: Optional[str] = Header(None)):
    """Recibe eventos de RevenueCat (compras de créditos o del curso completo vía Google Play)."""
    if REVENUECAT_WEBHOOK_SECRET and authorization != f"Bearer {REVENUECAT_WEBHOOK_SECRET}":
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    body = await request.json()
    event = body.get("event", {})
    event_type = event.get("type")
    app_user_id = event.get("app_user_id")  # debe ser el user_id de tu sistema
    product_id = event.get("product_id", "")

    if not app_user_id:
        return {"status": "ignored", "reason": "no app_user_id"}

    user = await db.users.find_one({"user_id": app_user_id})
    if not user:
        logger.warning(f"RevenueCat webhook: usuario {app_user_id} no encontrado")
        return {"status": "ignored", "reason": "user not found"}

    if event_type in ("INITIAL_PURCHASE", "NON_RENEWING_PURCHASE"):
        amount_usd = float(event.get("price_in_purchased_currency", 0) or 0)

        if product_id in FULL_COURSE_PRODUCTS:
            await db.users.update_one(
                {"user_id": app_user_id},
                {"$set": {"is_premium": True, "premium_expires_at": None}}
            )
            plan_label = "full_course"
        else:
            credits_to_add = CREDIT_PRODUCTS.get(product_id, 1)
            await db.users.update_one(
                {"user_id": app_user_id},
                {"$inc": {"credits": credits_to_add}}
            )
            plan_label = f"credits_{credits_to_add}"

        await db.payments.insert_one({
            "payment_id": f"rc_{uuid.uuid4().hex[:12]}",
            "order_id": f"rc_{event.get('id', uuid.uuid4().hex[:12])}",
            "user_id": app_user_id,
            "user_email": user.get("email", ""),
            "plan": plan_label,
            "method": "google_play",
            "amount_usd": amount_usd,
            "amount_ars": 0.0,
            "currency": event.get("currency", "USD"),
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        })

    # Los créditos y el curso completo son compras únicas: no hay renovación ni
    # cancelación que revertir (a diferencia de una suscripción). Si en el futuro
    # se agregan reembolsos, se puede manejar el evento "REFUND" acá.

    return {"status": "ok"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============= INDEXES =============

@app.on_event("startup")
async def create_indexes():
    """Create MongoDB indexes"""
    try:
        await db.users.create_index("email", unique=True)
        await db.users.create_index("user_id", unique=True)
        await db.user_sessions.create_index("session_token", unique=True)
        await db.user_sessions.create_index("user_id")
        await db.user_sessions.create_index("expires_at", expireAfterSeconds=0)
        await db.modules.create_index("module_id", unique=True)
        await db.lessons.create_index("lesson_id", unique=True)
        await db.exams.create_index("exam_id", unique=True)
        # SEC: Prevent payment replay attacks with unique order_id
        await db.payments.create_index("order_id", unique=True)
        await db.payments.create_index("user_id")
        logger.info("Indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
