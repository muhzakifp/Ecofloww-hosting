
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from collections import defaultdict, deque
import logging
import os
import time
import re
from app.core.database import get_db, engine, Base
from app.core.auth import get_current_user
from app.models.base import User, FermentationBatch, FermentationLog, ProductTemplate, BatchDailyLog, RoadmapProgress, ProductRecommendation
from app.schemas.base import (
    FermentationBatchCreate, FermentationBatch as BatchSchema,
    FermentationLogCreate, FermentationLog as LogSchema,
    BatchDailyLogCreate, BatchDailyLog as DailyLogSchema,
    BatchStatusUpdate,
    APIResponse, ErrorResponse
)
from app.services.eco_enzyme import EcoEnzymeService
from app.services.fermentation_assistant import FermentationAssistantService
from app.services.storage import upload_file_to_storage
from app.services.audit import AuditService
from app.routes.recommendations import router as rec_router
from app.routes.impact import router as impact_router
from app.routes.roadmap import router as roadmap_router
from app.routes.admin import router as admin_router
from app.routes.users import router as users_router
from app.api.sensors import router as sensors_router
from app.api.community import router as community_router

logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        if db.query(ProductTemplate).count() == 0:
            templates = [
                ProductTemplate(id=1, name="Pembersih Rumah Tangga", description="Pembersih serbaguna berbasis eco-enzyme untuk perabot rumah tangga", processing_instructions="Encerkan 1:10 dengan air. Semprotkan ke permukaan lalu lap bersih.", ingredients=["eco-enzyme", "air"], equipment=["botol semprot", "kain lap"], time_estimate_hours=0.5, safety_warnings="Hindari kontak langsung dengan mata."),
                ProductTemplate(id=2, name="Disinfektan", description="Disinfektan berbasis eco-enzyme untuk sanitasi", processing_instructions="Encerkan 1:5 dengan air. Aplikasikan pada permukaan, diamkan 10 menit.", ingredients=["eco-enzyme", "air"], equipment=["botol semprot", "sarung tangan"], time_estimate_hours=0.5, safety_warnings="Gunakan sarung tangan saat menangani larutan pekat."),
                ProductTemplate(id=3, name="Pupuk Cair Organik", description="Pupuk cair organik dari eco-enzyme", processing_instructions="Encerkan 1:100 dengan air. Siramkan ke tanah sekitar tanaman.", ingredients=["eco-enzyme", "air"], equipment=["gembor/alat penyiram"], time_estimate_hours=0.25, safety_warnings="Jangan aplikasikan langsung pada bagian tanaman yang dikonsumsi."),
                ProductTemplate(id=4, name="Pengusir Hama Alami", description="Pengusir hama alami berbasis eco-enzyme", processing_instructions="Encerkan 1:10 dengan air. Semprotkan pada daun tanaman.", ingredients=["eco-enzyme", "air"], equipment=["botol semprot"], time_estimate_hours=0.25, safety_warnings="Uji coba pada area kecil terlebih dahulu."),
                ProductTemplate(id=5, name="Pembersih Saluran Air", description="Pembersih dan penetral bau saluran pembuangan", processing_instructions="Tuangkan tanpa diencerkan ke saluran air. Diamkan semalaman.", ingredients=["eco-enzyme"], equipment=["gelas ukur"], time_estimate_hours=0.1, safety_warnings="Jangan dicampur dengan pembersih kimia."),
                ProductTemplate(id=6, name="Penetral Bau", description="Penetral bau alami untuk ruangan dan kain", processing_instructions="Encerkan 1:20 dengan air. Semprotkan halus ke udara atau kain.", ingredients=["eco-enzyme", "air"], equipment=["botol semprot kabut"], time_estimate_hours=0.25, safety_warnings="Uji coba pada bagian kain yang tidak mencolok."),
                ProductTemplate(id=7, name="Bahan Dasar Kosmetik", description="Bahan dasar eco-enzyme untuk produk kosmetik alami", processing_instructions="Saring dengan baik. Campurkan dengan bahan sesuai resep.", ingredients=["eco-enzyme", "minyak pembawa", "minyak esensial"], equipment=["saringan", "mangkuk pencampur", "wadah"], time_estimate_hours=2.0, safety_warnings="Lakukan uji tempel kulit sebelum penggunaan. Tidak untuk dikonsumsi."),
                ProductTemplate(id=8, name="Suplemen Pakan Ternak", description="Suplemen aditif pakan ternak berbasis eco-enzyme", processing_instructions="Encerkan 1:200 dengan air. Campurkan ke pakan ternak.", ingredients=["eco-enzyme", "air"], equipment=["gelas ukur", "ember pencampur"], time_estimate_hours=0.25, safety_warnings="Konsultasikan takaran dengan dokter hewan. Mulai dari jumlah kecil."),
            ]
            db.add_all(templates)
            db.commit()
    finally:
        db.close()
    yield

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EcoFlow API", version="0.1.0", lifespan=lifespan)

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,*.up.railway.app,*.railway.app").split(",") if h.strip()]
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,https://ecoflow-hosting.vercel.app,https://ecofloww-hosting.vercel.app").split(",") if o.strip()]
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
REDIS_URL = os.getenv("REDIS_URL", "")

# TrustedHostMiddleware dengan wildcard support untuk Railway
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)


#app.add_middleware(
#    CORSMiddleware,
#    allow_origins=["*"],
#    allow_credentials=True,
#    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#    allow_headers=["*"],
#    expose_headers=["*"]
#)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # Skip security headers for OPTIONS preflight requests
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response
    
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Relaxed CSP for Swagger UI (/docs and /openapi.json)
    if request.url.path in ["/docs", "/openapi.json", "/redoc"] or request.url.path.startswith("/docs/"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "img-src 'self' https://fastapi.tiangolo.com data:; "
            "font-src 'self' https://cdn.jsdelivr.net data:; "
            "connect-src 'self';"
        )
    else:
        # Strict CSP for other endpoints
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "connect-src 'self' https://*.vercel.app https://ecofloww-hosting-production.up.railway.app;"
        )
    
    return response

rate_buckets: dict[str, deque[float]] = defaultdict(deque)

try:
    import redis as redis_client
    _redis = redis_client.from_url(REDIS_URL, socket_connect_timeout=1) if REDIS_URL else None
    if _redis:
        _redis.ping()
        logger.info("Rate limiter: Redis-backed")
except Exception as e:
    _redis = None
    logger.warning(f"Rate limiter: falling back to in-memory ({e})")

def _rate_limit_key(scope: str, identity: str) -> str:
    return f"ratelimit:{scope}:{identity}"

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for OPTIONS preflight requests
    if request.method == "OPTIONS":
        return await call_next(request)
    
    client_ip = request.client.host if request.client else "unknown"
    if client_ip in ("127.0.0.1", "::1", "localhost"):
        return await call_next(request)
    if _redis:
        key = _rate_limit_key("ip", client_ip)
        try:
            count = _redis.incr(key)
            if count == 1:
                _redis.expire(key, RATE_LIMIT_WINDOW)
            if count > RATE_LIMIT:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"},
                )
        except Exception as e:
            logger.warning(f"Redis rate limit failed, allowing request: {e}")
    else:
        now = time.time()
        bucket = rate_buckets[client_ip]
        while bucket and bucket[0] <= now - RATE_LIMIT_WINDOW:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
            )
        bucket.append(now)
    return await call_next(request)


app.include_router(rec_router)
app.include_router(impact_router)
app.include_router(roadmap_router)
app.include_router(admin_router)
app.include_router(users_router)
app.include_router(sensors_router)
app.include_router(community_router)


@app.post("/api/v1/upload", response_model=APIResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
        MAX_FILE_SIZE = 5 * 1024 * 1024
        ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
        
        if file.content_type not in ALLOWED_MIME_TYPES:
            logger.warning(f"Rejected upload: invalid MIME type {file.content_type} from user {current_user.id}")
            raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP images allowed")
        
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 5MB)")
        
        file_ext = file.filename.split('.')[-1].lower() if file.filename else ""
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid file extension")
            
        url = await upload_file_to_storage(file, folder=f"users/{current_user.id}/logs")
        logger.info(f"Image uploaded successfully", extra={"user_id": current_user.id, "file_name": file.filename})
        
        return APIResponse(
            status="success",
            message="Image uploaded successfully",
            data={"url": url}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="File upload failed")

@app.post("/api/v1/batches", response_model=APIResponse)
async def create_batch(
    batch_data: FermentationBatchCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        calc = EcoEnzymeService.calculate_ingredients(batch_data.waste_weight_kg, batch_data.start_date)
        
        new_batch = FermentationBatch(
            user_id=current_user.id,
            name=batch_data.name,
            waste_weight_kg=batch_data.waste_weight_kg,
            water_liters=calc["ideal_water_liters"],
            sugar_kg=calc["ideal_sugar_kg"],
            start_date=batch_data.start_date,
            harvest_date=calc["expected_harvest_date"],
            status="pending_start"
        )
        db.add(new_batch)
        db.commit()
        db.refresh(new_batch)
        
        AuditService.log_from_request(
            db=db,
            request=request,
            user_id=current_user.id,
            action="CREATE",
            resource_type="batch",
            resource_id=new_batch.id,
            details={"batch_name": new_batch.name, "waste_kg": new_batch.waste_weight_kg}
        )
        
        logger.info(f"Batch created", extra={"user_id": current_user.id, "batch_id": new_batch.id})
        
        return APIResponse(
            status="success",
            message="Batch created successfully",
            data={
                "batch_id": new_batch.id,
                "waste_weight_kg": new_batch.waste_weight_kg,
                "calculated_water_liters": new_batch.water_liters,
                "calculated_sugar_kg": new_batch.sugar_kg,
                "expected_harvest_date": new_batch.harvest_date.isoformat()
            }
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input parameters")
    except Exception as e:
        logger.error(f"Batch creation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create batch")

@app.get("/api/v1/batches", response_model=APIResponse)
async def list_batches(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(FermentationBatch).filter(FermentationBatch.user_id == current_user.id)
        total = query.count()
        batches = query.order_by(FermentationBatch.created_at.desc()).limit(limit).offset(offset).all()
        
        batch_data = []
        for batch in batches:
            batch_data.append({
                "id": batch.id,
                "name": batch.name,
                "status": batch.status,
                "waste_weight_kg": batch.waste_weight_kg,
                "water_liters": batch.water_liters,
                "sugar_kg": batch.sugar_kg,
                "selected_product_id": batch.selected_product_id,
                "start_date": batch.start_date.isoformat(),
                "harvest_date": batch.harvest_date.isoformat() if batch.harvest_date else None,
                "created_at": batch.created_at.isoformat()
            })
        
        return APIResponse(
            status="success",
            data={
                "batches": batch_data,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        )
    except Exception as e:
        logger.error(f"Error fetching batches: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch batches"
        )

@app.get("/api/v1/batches/{batch_id}", response_model=APIResponse)
async def get_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    return APIResponse(
        status="success",
        data={
            "id": batch.id,
            "name": batch.name,
            "status": batch.status,
            "waste_weight_kg": batch.waste_weight_kg,
            "water_liters": batch.water_liters,
            "sugar_kg": batch.sugar_kg,
            "selected_product_id": batch.selected_product_id,
            "start_date": batch.start_date.isoformat(),
            "harvest_date": batch.harvest_date.isoformat() if batch.harvest_date else None,
            "created_at": batch.created_at.isoformat()
        }
    )

@app.post("/api/v1/batches/{batch_id}/logs", response_model=APIResponse)
async def create_fermentation_log(
    batch_id: int,
    log_data: FermentationLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    try:
        # PERBAIKAN: Validasi tanggal log tidak boleh sebelum tanggal mulai batch
        incubation_day = (log_data.log_date.date() - batch.start_date.date()).days
        if incubation_day < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tanggal log ({log_data.log_date.date()}) tidak boleh sebelum "
                       f"tanggal mulai batch ({batch.start_date.date()})"
            )
        
        # PERBAIKAN: Cek apakah sudah ada log untuk hari fermentasi yang sama
        existing_log = db.query(FermentationLog).filter(
            FermentationLog.batch_id == batch_id,
        ).all()
        for el in existing_log:
            existing_day = (el.log_date.date() - batch.start_date.date()).days
            if existing_day == incubation_day:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sudah ada catatan untuk hari fermentasi ke-{incubation_day}. "
                           f"Hapus catatan lama terlebih dahulu jika ingin mengganti."
                )
        
        # PERBAIKAN: Validasi suhu dan pH (jika ada)
        if log_data.temperature_c is not None:
            if log_data.temperature_c < -10 or log_data.temperature_c > 60:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Suhu harus antara -10°C dan 60°C"
                )
        
        status_pred, confidence, suggestion = FermentationAssistantService.classify_fermentation(
            aroma=log_data.aroma,
            color=log_data.color,
            gas_presence=log_data.gas_presence,
            temperature_c=log_data.temperature_c,
            incubation_day=incubation_day,
            ph=getattr(log_data, 'ph', None)
        )
        
        health_score = FermentationAssistantService.calculate_health_score(status_pred, confidence, incubation_day)
        
        harvest_alert = FermentationAssistantService.should_trigger_harvest_alert(
            status_pred, incubation_day, log_data.gas_presence, log_data.aroma
        )
        
        new_log = FermentationLog(
            batch_id=batch_id,
            log_date=log_data.log_date,
            aroma=log_data.aroma,
            color=log_data.color,
            gas_presence=log_data.gas_presence,
            temperature_c=log_data.temperature_c,
            notes=log_data.notes,
            image_url=log_data.image_url,
            ai_status=status_pred,
            ai_confidence=confidence,
            ai_suggestion=suggestion
        )
        db.add(new_log)
        
        if batch.status == "pending_start":
            batch.status = "in_progress"
        
        db.commit()
        db.refresh(new_log)
        
        logger.info(f"Fermentation log created", extra={"user_id": current_user.id, "batch_id": batch_id, "log_id": new_log.id})
        
        return APIResponse(
            status="success",
            message="Log recorded successfully",
            data={
                "log_id": new_log.id,
                "image_url": new_log.image_url,
                "ai_status_prediction": status_pred,
                "ai_confidence_score": confidence,
                "health_score": round(health_score, 2),
                "corrective_action_suggestion": suggestion,
                "harvest_alert_triggered": harvest_alert,
                "incubation_day": incubation_day
            }
        )
    except ValueError as e:
        logger.warning(f"Validation error in log: {str(e)}", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid log parameters")
    except Exception as e:
        logger.error(f"Log creation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create log")

@app.get("/api/v1/batches/{batch_id}/logs", response_model=APIResponse)
async def get_batch_logs(
    batch_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    query = db.query(FermentationLog).filter(FermentationLog.batch_id == batch_id)
    total = query.count()
    logs = query.order_by(FermentationLog.log_date.desc()).limit(limit).offset(offset).all()
    
    logs_data = []
    for log in logs:
        logs_data.append({
            "id": log.id,
            "log_date": log.log_date.isoformat(),
            "aroma": log.aroma,
            "color": log.color,
            "gas_presence": log.gas_presence,
            "temperature_c": log.temperature_c,
            "ai_status": log.ai_status,
            "ai_confidence": log.ai_confidence,
            "ai_suggestion": log.ai_suggestion,
            "created_at": log.created_at.isoformat()
        })
    
    return APIResponse(
        status="success",
        data={
            "logs": logs_data,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(logs_data) < total
        }
    )

@app.post("/api/v1/batches/{batch_id}/daily-logs", response_model=APIResponse)
async def create_daily_log(
    batch_id: int,
    log_data: BatchDailyLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mencatat progres harian untuk batch eco-enzyme yang sedang aktif.
    """
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    try:
        new_daily_log = BatchDailyLog(
            batch_id=batch_id,
            log_date=log_data.log_date,
            action_taken=log_data.action_taken,
            condition=log_data.condition,
            notes=log_data.notes
        )
        db.add(new_daily_log)
        db.commit()
        db.refresh(new_daily_log)
        
        logger.info(f"Daily log created", extra={"user_id": current_user.id, "batch_id": batch_id, "daily_log_id": new_daily_log.id})
        
        return APIResponse(
            status="success",
            message="Progres harian berhasil dicatat!",
            data={
                "log_id": new_daily_log.id,
                "batch_id": batch_id,
                "log_date": new_daily_log.log_date.isoformat(),
                "action_taken": new_daily_log.action_taken,
                "condition": new_daily_log.condition,
                "notes": new_daily_log.notes
            }
        )
    except Exception as e:
        logger.error(f"Daily log creation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create daily log")


@app.get("/api/v1/batches/{batch_id}/daily-logs", response_model=APIResponse)
async def get_batch_daily_logs(
    batch_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mengambil riwayat progres harian dari batch tertentu.
    """
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    query = db.query(BatchDailyLog).filter(BatchDailyLog.batch_id == batch_id)
    total = query.count()
    daily_logs = query.order_by(BatchDailyLog.log_date.desc()).limit(limit).offset(offset).all()
    
    logs_data = []
    for log in daily_logs:
        logs_data.append({
            "id": log.id,
            "batch_id": log.batch_id,
            "log_date": log.log_date.isoformat(),
            "action_taken": log.action_taken,
            "condition": log.condition,
            "notes": log.notes,
            "created_at": log.created_at.isoformat()
        })
    
    return APIResponse(
        status="success",
        data={
            "daily_logs": logs_data,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(logs_data) < total
        }
    )


@app.put("/api/v1/batches/{batch_id}/status", response_model=APIResponse)
async def update_batch_status(
    batch_id: int,
    status_data: BatchStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch tidak ditemukan")
        
    old_status = batch.status
    new_status = status_data.new_status
    valid_statuses = ["pending_start", "in_progress", "completed", "harvested", "failed", "paused"]
    
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status '{new_status}' tidak valid")
        
    valid = True
    if old_status == "pending_start" and new_status != "in_progress":
        valid = False
    elif old_status == "in_progress" and new_status not in ["completed", "failed", "paused"]:
        valid = False
    elif old_status == "paused" and new_status not in ["in_progress", "failed"]:
        valid = False
    elif old_status == "completed" and new_status != "harvested":
        valid = False
    elif old_status in ["failed", "harvested"]:
        valid = False
        
    if not valid:
        raise HTTPException(status_code=400, detail=f"Transisi status dari '{old_status}' ke '{new_status}' tidak diizinkan")
        
    batch.status = new_status
    
    if new_status in ["completed", "harvested"] and old_status not in ["completed", "harvested"]:
        current_user.waste_diverted_kg += batch.waste_weight_kg
    elif old_status in ["completed", "harvested"] and new_status not in ["completed", "harvested"]:
        current_user.waste_diverted_kg = max(0.0, current_user.waste_diverted_kg - batch.waste_weight_kg)
        
    db.commit()
    db.refresh(batch)
    
    AuditService.log_from_request(
        db=db,
        request=request,
        user_id=current_user.id,
        action="UPDATE_STATUS",
        resource_type="batch",
        resource_id=batch_id,
        details={"old_status": old_status, "new_status": new_status, "notes": status_data.notes}
    )
    
    return APIResponse(status="success", message="Status batch berhasil diperbarui", data={"id": batch.id, "status": batch.status})

@app.delete("/api/v1/batches/{batch_id}", response_model=APIResponse)
async def delete_batch(
    batch_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch tidak ditemukan")
    
    batch_name = batch.name
    batch_status = batch.status
        
    db.query(FermentationLog).filter(FermentationLog.batch_id == batch_id).delete()
    db.query(BatchDailyLog).filter(BatchDailyLog.batch_id == batch_id).delete()
    db.query(RoadmapProgress).filter(RoadmapProgress.batch_id == batch_id).delete()
    db.query(ProductRecommendation).filter(ProductRecommendation.batch_id == batch_id).delete()
    
    if batch.status in ["completed", "harvested"]:
        current_user.waste_diverted_kg = max(0.0, current_user.waste_diverted_kg - batch.waste_weight_kg)
        
    db.delete(batch)
    db.commit()
    
    AuditService.log_from_request(
        db=db,
        request=request,
        user_id=current_user.id,
        action="DELETE",
        resource_type="batch",
        resource_id=batch_id,
        details={"batch_name": batch_name, "batch_status": batch_status}
    )
    
    return APIResponse(status="success", message="Batch berhasil dihapus")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

    # Relaxed CSP for Swagger UI (/docs and /openapi.json)
    if request.url.path in ["/docs", "/openapi.json", "/redoc"] or request.url.path.startswith("/docs/"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "img-src 'self' https://fastapi.tiangolo.com data:; "
            "font-src 'self' https://cdn.jsdelivr.net data:; "
            "connect-src 'self';"
        )
    else:
        # Strict CSP for other endpoints
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "connect-src 'self' https://*.vercel.app https://ecofloww-hosting-production.up.railway.app;"
        )
    
    return response

rate_buckets: dict[str, deque[float]] = defaultdict(deque)

try:
    import redis as redis_client
    _redis = redis_client.from_url(REDIS_URL, socket_connect_timeout=1) if REDIS_URL else None
    if _redis:
        _redis.ping()
        logger.info("Rate limiter: Redis-backed")
except Exception as e:
    _redis = None
    logger.warning(f"Rate limiter: falling back to in-memory ({e})")

def _rate_limit_key(scope: str, identity: str) -> str:
    return f"ratelimit:{scope}:{identity}"

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for OPTIONS preflight requests
    if request.method == "OPTIONS":
        return await call_next(request)
    
    client_ip = request.client.host if request.client else "unknown"
    if client_ip in ("127.0.0.1", "::1", "localhost"):
        return await call_next(request)
    if _redis:
        key = _rate_limit_key("ip", client_ip)
        try:
            count = _redis.incr(key)
            if count == 1:
                _redis.expire(key, RATE_LIMIT_WINDOW)
            if count > RATE_LIMIT:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"},
                )
        except Exception as e:
            logger.warning(f"Redis rate limit failed, allowing request: {e}")
    else:
        now = time.time()
        bucket = rate_buckets[client_ip]
        while bucket and bucket[0] <= now - RATE_LIMIT_WINDOW:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
            )
        bucket.append(now)
    return await call_next(request)


app.include_router(rec_router)
app.include_router(impact_router)
app.include_router(roadmap_router)
app.include_router(admin_router)
app.include_router(users_router)
app.include_router(sensors_router)
app.include_router(community_router)


@app.post("/api/v1/upload", response_model=APIResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
        MAX_FILE_SIZE = 5 * 1024 * 1024
        ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
        
        if file.content_type not in ALLOWED_MIME_TYPES:
            logger.warning(f"Rejected upload: invalid MIME type {file.content_type} from user {current_user.id}")
            raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP images allowed")
        
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 5MB)")
        
        file_ext = file.filename.split('.')[-1].lower() if file.filename else ""
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid file extension")
            
        url = await upload_file_to_storage(file, folder=f"users/{current_user.id}/logs")
        logger.info(f"Image uploaded successfully", extra={"user_id": current_user.id, "file_name": file.filename})
        
        return APIResponse(
            status="success",
            message="Image uploaded successfully",
            data={"url": url}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="File upload failed")

@app.post("/api/v1/batches", response_model=APIResponse)
async def create_batch(
    batch_data: FermentationBatchCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        calc = EcoEnzymeService.calculate_ingredients(batch_data.waste_weight_kg, batch_data.start_date)
        
        new_batch = FermentationBatch(
            user_id=current_user.id,
            name=batch_data.name,
            waste_weight_kg=batch_data.waste_weight_kg,
            water_liters=calc["ideal_water_liters"],
            sugar_kg=calc["ideal_sugar_kg"],
            start_date=batch_data.start_date,
            harvest_date=calc["expected_harvest_date"],
            status="pending_start"
        )
        db.add(new_batch)
        db.commit()
        db.refresh(new_batch)
        
        AuditService.log_from_request(
            db=db,
            request=request,
            user_id=current_user.id,
            action="CREATE",
            resource_type="batch",
            resource_id=new_batch.id,
            details={"batch_name": new_batch.name, "waste_kg": new_batch.waste_weight_kg}
        )
        
        logger.info(f"Batch created", extra={"user_id": current_user.id, "batch_id": new_batch.id})
        
        return APIResponse(
            status="success",
            message="Batch created successfully",
            data={
                "batch_id": new_batch.id,
                "waste_weight_kg": new_batch.waste_weight_kg,
                "calculated_water_liters": new_batch.water_liters,
                "calculated_sugar_kg": new_batch.sugar_kg,
                "expected_harvest_date": new_batch.harvest_date.isoformat()
            }
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input parameters")
    except Exception as e:
        logger.error(f"Batch creation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create batch")

@app.get("/api/v1/batches", response_model=APIResponse)
async def list_batches(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(FermentationBatch).filter(FermentationBatch.user_id == current_user.id)
        total = query.count()
        batches = query.order_by(FermentationBatch.created_at.desc()).limit(limit).offset(offset).all()
        
        batch_data = []
        for batch in batches:
            batch_data.append({
                "id": batch.id,
                "name": batch.name,
                "status": batch.status,
                "waste_weight_kg": batch.waste_weight_kg,
                "water_liters": batch.water_liters,
                "sugar_kg": batch.sugar_kg,
                "selected_product_id": batch.selected_product_id,
                "start_date": batch.start_date.isoformat(),
                "harvest_date": batch.harvest_date.isoformat() if batch.harvest_date else None,
                "created_at": batch.created_at.isoformat()
            })
        
        return APIResponse(
            status="success",
            data={
                "batches": batch_data,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        )
    except Exception as e:
        logger.error(f"Error fetching batches: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch batches"
        )

@app.get("/api/v1/batches/{batch_id}", response_model=APIResponse)
async def get_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    return APIResponse(
        status="success",
        data={
            "id": batch.id,
            "name": batch.name,
            "status": batch.status,
            "waste_weight_kg": batch.waste_weight_kg,
            "water_liters": batch.water_liters,
            "sugar_kg": batch.sugar_kg,
            "selected_product_id": batch.selected_product_id,
            "start_date": batch.start_date.isoformat(),
            "harvest_date": batch.harvest_date.isoformat() if batch.harvest_date else None,
            "created_at": batch.created_at.isoformat()
        }
    )

@app.post("/api/v1/batches/{batch_id}/logs", response_model=APIResponse)
async def create_fermentation_log(
    batch_id: int,
    log_data: FermentationLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    try:
        # PERBAIKAN: Validasi tanggal log tidak boleh sebelum tanggal mulai batch
        incubation_day = (log_data.log_date.date() - batch.start_date.date()).days
        if incubation_day < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tanggal log ({log_data.log_date.date()}) tidak boleh sebelum "
                       f"tanggal mulai batch ({batch.start_date.date()})"
            )
        
        # PERBAIKAN: Cek apakah sudah ada log untuk hari fermentasi yang sama
        existing_log = db.query(FermentationLog).filter(
            FermentationLog.batch_id == batch_id,
        ).all()
        for el in existing_log:
            existing_day = (el.log_date.date() - batch.start_date.date()).days
            if existing_day == incubation_day:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sudah ada catatan untuk hari fermentasi ke-{incubation_day}. "
                           f"Hapus catatan lama terlebih dahulu jika ingin mengganti."
                )
        
        # PERBAIKAN: Validasi suhu dan pH (jika ada)
        if log_data.temperature_c is not None:
            if log_data.temperature_c < -10 or log_data.temperature_c > 60:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Suhu harus antara -10°C dan 60°C"
                )
        
        status_pred, confidence, suggestion = FermentationAssistantService.classify_fermentation(
            aroma=log_data.aroma,
            color=log_data.color,
            gas_presence=log_data.gas_presence,
            temperature_c=log_data.temperature_c,
            incubation_day=incubation_day,
            ph=getattr(log_data, 'ph', None)
        )
        
        health_score = FermentationAssistantService.calculate_health_score(status_pred, confidence, incubation_day)
        
        harvest_alert = FermentationAssistantService.should_trigger_harvest_alert(
            status_pred, incubation_day, log_data.gas_presence, log_data.aroma
        )
        
        new_log = FermentationLog(
            batch_id=batch_id,
            log_date=log_data.log_date,
            aroma=log_data.aroma,
            color=log_data.color,
            gas_presence=log_data.gas_presence,
            temperature_c=log_data.temperature_c,
            notes=log_data.notes,
            image_url=log_data.image_url,
            ai_status=status_pred,
            ai_confidence=confidence,
            ai_suggestion=suggestion
        )
        db.add(new_log)
        
        if batch.status == "pending_start":
            batch.status = "in_progress"
        
        db.commit()
        db.refresh(new_log)
        
        logger.info(f"Fermentation log created", extra={"user_id": current_user.id, "batch_id": batch_id, "log_id": new_log.id})
        
        return APIResponse(
            status="success",
            message="Log recorded successfully",
            data={
                "log_id": new_log.id,
                "image_url": new_log.image_url,
                "ai_status_prediction": status_pred,
                "ai_confidence_score": confidence,
                "health_score": round(health_score, 2),
                "corrective_action_suggestion": suggestion,
                "harvest_alert_triggered": harvest_alert,
                "incubation_day": incubation_day
            }
        )
    except ValueError as e:
        logger.warning(f"Validation error in log: {str(e)}", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid log parameters")
    except Exception as e:
        logger.error(f"Log creation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create log")

@app.get("/api/v1/batches/{batch_id}/logs", response_model=APIResponse)
async def get_batch_logs(
    batch_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    query = db.query(FermentationLog).filter(FermentationLog.batch_id == batch_id)
    total = query.count()
    logs = query.order_by(FermentationLog.log_date.desc()).limit(limit).offset(offset).all()
    
    logs_data = []
    for log in logs:
        logs_data.append({
            "id": log.id,
            "log_date": log.log_date.isoformat(),
            "aroma": log.aroma,
            "color": log.color,
            "gas_presence": log.gas_presence,
            "temperature_c": log.temperature_c,
            "ai_status": log.ai_status,
            "ai_confidence": log.ai_confidence,
            "ai_suggestion": log.ai_suggestion,
            "created_at": log.created_at.isoformat()
        })
    
    return APIResponse(
        status="success",
        data={
            "logs": logs_data,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(logs_data) < total
        }
    )

@app.post("/api/v1/batches/{batch_id}/daily-logs", response_model=APIResponse)
async def create_daily_log(
    batch_id: int,
    log_data: BatchDailyLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mencatat progres harian untuk batch eco-enzyme yang sedang aktif.
    """
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    try:
        new_daily_log = BatchDailyLog(
            batch_id=batch_id,
            log_date=log_data.log_date,
            action_taken=log_data.action_taken,
            condition=log_data.condition,
            notes=log_data.notes
        )
        db.add(new_daily_log)
        db.commit()
        db.refresh(new_daily_log)
        
        logger.info(f"Daily log created", extra={"user_id": current_user.id, "batch_id": batch_id, "daily_log_id": new_daily_log.id})
        
        return APIResponse(
            status="success",
            message="Progres harian berhasil dicatat!",
            data={
                "log_id": new_daily_log.id,
                "batch_id": batch_id,
                "log_date": new_daily_log.log_date.isoformat(),
                "action_taken": new_daily_log.action_taken,
                "condition": new_daily_log.condition,
                "notes": new_daily_log.notes
            }
        )
    except Exception as e:
        logger.error(f"Daily log creation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create daily log")


@app.get("/api/v1/batches/{batch_id}/daily-logs", response_model=APIResponse)
async def get_batch_daily_logs(
    batch_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mengambil riwayat progres harian dari batch tertentu.
    """
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    query = db.query(BatchDailyLog).filter(BatchDailyLog.batch_id == batch_id)
    total = query.count()
    daily_logs = query.order_by(BatchDailyLog.log_date.desc()).limit(limit).offset(offset).all()
    
    logs_data = []
    for log in daily_logs:
        logs_data.append({
            "id": log.id,
            "batch_id": log.batch_id,
            "log_date": log.log_date.isoformat(),
            "action_taken": log.action_taken,
            "condition": log.condition,
            "notes": log.notes,
            "created_at": log.created_at.isoformat()
        })
    
    return APIResponse(
        status="success",
        data={
            "daily_logs": logs_data,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(logs_data) < total
        }
    )


@app.put("/api/v1/batches/{batch_id}/status", response_model=APIResponse)
async def update_batch_status(
    batch_id: int,
    status_data: BatchStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch tidak ditemukan")
        
    old_status = batch.status
    new_status = status_data.new_status
    valid_statuses = ["pending_start", "in_progress", "completed", "harvested", "failed", "paused"]
    
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status '{new_status}' tidak valid")
        
    valid = True
    if old_status == "pending_start" and new_status != "in_progress":
        valid = False
    elif old_status == "in_progress" and new_status not in ["completed", "failed", "paused"]:
        valid = False
    elif old_status == "paused" and new_status not in ["in_progress", "failed"]:
        valid = False
    elif old_status == "completed" and new_status != "harvested":
        valid = False
    elif old_status in ["failed", "harvested"]:
        valid = False
        
    if not valid:
        raise HTTPException(status_code=400, detail=f"Transisi status dari '{old_status}' ke '{new_status}' tidak diizinkan")
        
    batch.status = new_status
    
    if new_status in ["completed", "harvested"] and old_status not in ["completed", "harvested"]:
        current_user.waste_diverted_kg += batch.waste_weight_kg
    elif old_status in ["completed", "harvested"] and new_status not in ["completed", "harvested"]:
        current_user.waste_diverted_kg = max(0.0, current_user.waste_diverted_kg - batch.waste_weight_kg)
        
    db.commit()
    db.refresh(batch)
    
    AuditService.log_from_request(
        db=db,
        request=request,
        user_id=current_user.id,
        action="UPDATE_STATUS",
        resource_type="batch",
        resource_id=batch_id,
        details={"old_status": old_status, "new_status": new_status, "notes": status_data.notes}
    )
    
    return APIResponse(status="success", message="Status batch berhasil diperbarui", data={"id": batch.id, "status": batch.status})

@app.delete("/api/v1/batches/{batch_id}", response_model=APIResponse)
async def delete_batch(
    batch_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch tidak ditemukan")
    
    batch_name = batch.name
    batch_status = batch.status
        
    db.query(FermentationLog).filter(FermentationLog.batch_id == batch_id).delete()
    db.query(BatchDailyLog).filter(BatchDailyLog.batch_id == batch_id).delete()
    db.query(RoadmapProgress).filter(RoadmapProgress.batch_id == batch_id).delete()
    db.query(ProductRecommendation).filter(ProductRecommendation.batch_id == batch_id).delete()
    
    if batch.status in ["completed", "harvested"]:
        current_user.waste_diverted_kg = max(0.0, current_user.waste_diverted_kg - batch.waste_weight_kg)
        
    db.delete(batch)
    db.commit()
    
    AuditService.log_from_request(
        db=db,
        request=request,
        user_id=current_user.id,
        action="DELETE",
        resource_type="batch",
        resource_id=batch_id,
        details={"batch_name": batch_name, "batch_status": batch_status}
    )
    
    return APIResponse(status="success", message="Batch berhasil dihapus")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

            templates = [
                ProductTemplate(id=1, name="Pembersih Rumah Tangga", description="Pembersih serbaguna berbasis eco-enzyme untuk perabot rumah tangga", processing_instructions="Encerkan 1:10 dengan air. Semprotkan ke permukaan lalu lap bersih.", ingredients=["eco-enzyme", "air"], equipment=["botol semprot", "kain lap"], time_estimate_hours=0.5, safety_warnings="Hindari kontak langsung dengan mata."),
                ProductTemplate(id=2, name="Disinfektan", description="Disinfektan berbasis eco-enzyme untuk sanitasi", processing_instructions="Encerkan 1:5 dengan air. Aplikasikan pada permukaan, diamkan 10 menit.", ingredients=["eco-enzyme", "air"], equipment=["botol semprot", "sarung tangan"], time_estimate_hours=0.5, safety_warnings="Gunakan sarung tangan saat menangani larutan pekat."),
                ProductTemplate(id=3, name="Pupuk Cair Organik", description="Pupuk cair organik dari eco-enzyme", processing_instructions="Encerkan 1:100 dengan air. Siramkan ke tanah sekitar tanaman.", ingredients=["eco-enzyme", "air"], equipment=["gembor/alat penyiram"], time_estimate_hours=0.25, safety_warnings="Jangan aplikasikan langsung pada bagian tanaman yang dikonsumsi."),
                ProductTemplate(id=4, name="Pengusir Hama Alami", description="Pengusir hama alami berbasis eco-enzyme", processing_instructions="Encerkan 1:10 dengan air. Semprotkan pada daun tanaman.", ingredients=["eco-enzyme", "air"], equipment=["botol semprot"], time_estimate_hours=0.25, safety_warnings="Uji coba pada area kecil terlebih dahulu."),
                ProductTemplate(id=5, name="Pembersih Saluran Air", description="Pembersih dan penetral bau saluran pembuangan", processing_instructions="Tuangkan tanpa diencerkan ke saluran air. Diamkan semalaman.", ingredients=["eco-enzyme"], equipment=["gelas ukur"], time_estimate_hours=0.1, safety_warnings="Jangan dicampur dengan pembersih kimia."),
                ProductTemplate(id=6, name="Penetral Bau", description="Penetral bau alami untuk ruangan dan kain", processing_instructions="Encerkan 1:20 dengan air. Semprotkan halus ke udara atau kain.", ingredients=["eco-enzyme", "air"], equipment=["botol semprot kabut"], time_estimate_hours=0.25, safety_warnings="Uji coba pada bagian kain yang tidak mencolok."),
                ProductTemplate(id=7, name="Bahan Dasar Kosmetik", description="Bahan dasar eco-enzyme untuk produk kosmetik alami", processing_instructions="Saring dengan baik. Campurkan dengan bahan sesuai resep.", ingredients=["eco-enzyme", "minyak pembawa", "minyak esensial"], equipment=["saringan", "mangkuk pencampur", "wadah"], time_estimate_hours=2.0, safety_warnings="Lakukan uji tempel kulit sebelum penggunaan. Tidak untuk dikonsumsi."),
                ProductTemplate(id=8, name="Suplemen Pakan Ternak", description="Suplemen aditif pakan ternak berbasis eco-enzyme", processing_instructions="Encerkan 1:200 dengan air. Campurkan ke pakan ternak.", ingredients=["eco-enzyme", "air"], equipment=["gelas ukur", "ember pencampur"], time_estimate_hours=0.25, safety_warnings="Konsultasikan takaran dengan dokter hewan. Mulai dari jumlah kecil."),
            ]
            db.add_all(templates)
            db.commit()
    finally:
        db.close()
    yield

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EcoFlow API", version="0.1.0", lifespan=lifespan)

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,*.up.railway.app,*.railway.app").split(",") if h.strip()]
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,https://ecoflow-hosting.vercel.app,https://ecofloww-hosting.vercel.app").split(",") if o.strip()]
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
REDIS_URL = os.getenv("REDIS_URL", "")

# TrustedHostMiddleware dengan wildcard support untuk Railway
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)


#app.add_middleware(
#    CORSMiddleware,
#    allow_origins=["*"],
#    allow_credentials=True,
#    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#    allow_headers=["*"],
#    expose_headers=["*"]
#)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # Skip security headers for OPTIONS preflight requests
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response
    
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Relaxed CSP for Swagger UI (/docs and /openapi.json)
    if request.url.path in ["/docs", "/openapi.json", "/redoc"] or request.url.path.startswith("/docs/"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "img-src 'self' https://fastapi.tiangolo.com data:; "
            "font-src 'self' https://cdn.jsdelivr.net data:; "
            "connect-src 'self';"
        )
    else:
        # Strict CSP for other endpoints
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "connect-src 'self' https://*.vercel.app https://ecofloww-hosting-production.up.railway.app;"
        )
    
    return response

rate_buckets: dict[str, deque[float]] = defaultdict(deque)

try:
    import redis as redis_client
    _redis = redis_client.from_url(REDIS_URL, socket_connect_timeout=1) if REDIS_URL else None
    if _redis:
        _redis.ping()
        logger.info("Rate limiter: Redis-backed")
except Exception as e:
    _redis = None
    logger.warning(f"Rate limiter: falling back to in-memory ({e})")

def _rate_limit_key(scope: str, identity: str) -> str:
    return f"ratelimit:{scope}:{identity}"

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for OPTIONS preflight requests
    if request.method == "OPTIONS":
        return await call_next(request)
    
    client_ip = request.client.host if request.client else "unknown"
    if client_ip in ("127.0.0.1", "::1", "localhost"):
        return await call_next(request)
    if _redis:
        key = _rate_limit_key("ip", client_ip)
        try:
            count = _redis.incr(key)
            if count == 1:
                _redis.expire(key, RATE_LIMIT_WINDOW)
            if count > RATE_LIMIT:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"},
                )
        except Exception as e:
            logger.warning(f"Redis rate limit failed, allowing request: {e}")
    else:
        now = time.time()
        bucket = rate_buckets[client_ip]
        while bucket and bucket[0] <= now - RATE_LIMIT_WINDOW:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
            )
        bucket.append(now)
    return await call_next(request)


app.include_router(rec_router)
app.include_router(impact_router)
app.include_router(roadmap_router)
app.include_router(admin_router)
app.include_router(users_router)
app.include_router(sensors_router)
app.include_router(community_router)


@app.post("/api/v1/upload", response_model=APIResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
        MAX_FILE_SIZE = 5 * 1024 * 1024
        ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
        
        if file.content_type not in ALLOWED_MIME_TYPES:
            logger.warning(f"Rejected upload: invalid MIME type {file.content_type} from user {current_user.id}")
            raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP images allowed")
        
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 5MB)")
        
        file_ext = file.filename.split('.')[-1].lower() if file.filename else ""
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid file extension")
            
        url = await upload_file_to_storage(file, folder=f"users/{current_user.id}/logs")
        logger.info(f"Image uploaded successfully", extra={"user_id": current_user.id, "file_name": file.filename})
        
        return APIResponse(
            status="success",
            message="Image uploaded successfully",
            data={"url": url}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="File upload failed")

@app.post("/api/v1/batches", response_model=APIResponse)
async def create_batch(
    batch_data: FermentationBatchCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        calc = EcoEnzymeService.calculate_ingredients(batch_data.waste_weight_kg, batch_data.start_date)
        
        new_batch = FermentationBatch(
            user_id=current_user.id,
            name=batch_data.name,
            waste_weight_kg=batch_data.waste_weight_kg,
            water_liters=calc["ideal_water_liters"],
            sugar_kg=calc["ideal_sugar_kg"],
            start_date=batch_data.start_date,
            harvest_date=calc["expected_harvest_date"],
            status="pending_start"
        )
        db.add(new_batch)
        db.commit()
        db.refresh(new_batch)
        
        AuditService.log_from_request(
            db=db,
            request=request,
            user_id=current_user.id,
            action="CREATE",
            resource_type="batch",
            resource_id=new_batch.id,
            details={"batch_name": new_batch.name, "waste_kg": new_batch.waste_weight_kg}
        )
        
        logger.info(f"Batch created", extra={"user_id": current_user.id, "batch_id": new_batch.id})
        
        return APIResponse(
            status="success",
            message="Batch created successfully",
            data={
                "batch_id": new_batch.id,
                "waste_weight_kg": new_batch.waste_weight_kg,
                "calculated_water_liters": new_batch.water_liters,
                "calculated_sugar_kg": new_batch.sugar_kg,
                "expected_harvest_date": new_batch.harvest_date.isoformat()
            }
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input parameters")
    except Exception as e:
        logger.error(f"Batch creation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create batch")

@app.get("/api/v1/batches", response_model=APIResponse)
async def list_batches(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(FermentationBatch).filter(FermentationBatch.user_id == current_user.id)
        total = query.count()
        batches = query.order_by(FermentationBatch.created_at.desc()).limit(limit).offset(offset).all()
        
        batch_data = []
        for batch in batches:
            batch_data.append({
                "id": batch.id,
                "name": batch.name,
                "status": batch.status,
                "waste_weight_kg": batch.waste_weight_kg,
                "water_liters": batch.water_liters,
                "sugar_kg": batch.sugar_kg,
                "selected_product_id": batch.selected_product_id,
                "start_date": batch.start_date.isoformat(),
                "harvest_date": batch.harvest_date.isoformat() if batch.harvest_date else None,
                "created_at": batch.created_at.isoformat()
            })
        
        return APIResponse(
            status="success",
            data={
                "batches": batch_data,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        )
    except Exception as e:
        logger.error(f"Error fetching batches: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch batches"
        )

@app.get("/api/v1/batches/{batch_id}", response_model=APIResponse)
async def get_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    return APIResponse(
        status="success",
        data={
            "id": batch.id,
            "name": batch.name,
            "status": batch.status,
            "waste_weight_kg": batch.waste_weight_kg,
            "water_liters": batch.water_liters,
            "sugar_kg": batch.sugar_kg,
            "selected_product_id": batch.selected_product_id,
            "start_date": batch.start_date.isoformat(),
            "harvest_date": batch.harvest_date.isoformat() if batch.harvest_date else None,
            "created_at": batch.created_at.isoformat()
        }
    )

@app.post("/api/v1/batches/{batch_id}/logs", response_model=APIResponse)
async def create_fermentation_log(
    batch_id: int,
    log_data: FermentationLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    try:
        # PERBAIKAN: Validasi tanggal log tidak boleh sebelum tanggal mulai batch
        incubation_day = (log_data.log_date.date() - batch.start_date.date()).days
        if incubation_day < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tanggal log ({log_data.log_date.date()}) tidak boleh sebelum "
                       f"tanggal mulai batch ({batch.start_date.date()})"
            )
        
        # PERBAIKAN: Cek apakah sudah ada log untuk hari fermentasi yang sama
        existing_log = db.query(FermentationLog).filter(
            FermentationLog.batch_id == batch_id,
        ).all()
        for el in existing_log:
            existing_day = (el.log_date.date() - batch.start_date.date()).days
            if existing_day == incubation_day:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sudah ada catatan untuk hari fermentasi ke-{incubation_day}. "
                           f"Hapus catatan lama terlebih dahulu jika ingin mengganti."
                )
        
        # PERBAIKAN: Validasi suhu dan pH (jika ada)
        if log_data.temperature_c is not None:
            if log_data.temperature_c < -10 or log_data.temperature_c > 60:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Suhu harus antara -10°C dan 60°C"
                )
        
        status_pred, confidence, suggestion = FermentationAssistantService.classify_fermentation(
            aroma=log_data.aroma,
            color=log_data.color,
            gas_presence=log_data.gas_presence,
            temperature_c=log_data.temperature_c,
            incubation_day=incubation_day,
            ph=getattr(log_data, 'ph', None)
        )
        
        health_score = FermentationAssistantService.calculate_health_score(status_pred, confidence, incubation_day)
        
        harvest_alert = FermentationAssistantService.should_trigger_harvest_alert(
            status_pred, incubation_day, log_data.gas_presence, log_data.aroma
        )
        
        new_log = FermentationLog(
            batch_id=batch_id,
            log_date=log_data.log_date,
            aroma=log_data.aroma,
            color=log_data.color,
            gas_presence=log_data.gas_presence,
            temperature_c=log_data.temperature_c,
            notes=log_data.notes,
            image_url=log_data.image_url,
            ai_status=status_pred,
            ai_confidence=confidence,
            ai_suggestion=suggestion
        )
        db.add(new_log)
        
        if batch.status == "pending_start":
            batch.status = "in_progress"
        
        db.commit()
        db.refresh(new_log)
        
        logger.info(f"Fermentation log created", extra={"user_id": current_user.id, "batch_id": batch_id, "log_id": new_log.id})
        
        return APIResponse(
            status="success",
            message="Log recorded successfully",
            data={
                "log_id": new_log.id,
                "image_url": new_log.image_url,
                "ai_status_prediction": status_pred,
                "ai_confidence_score": confidence,
                "health_score": round(health_score, 2),
                "corrective_action_suggestion": suggestion,
                "harvest_alert_triggered": harvest_alert,
                "incubation_day": incubation_day
            }
        )
    except ValueError as e:
        logger.warning(f"Validation error in log: {str(e)}", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid log parameters")
    except Exception as e:
        logger.error(f"Log creation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create log")

@app.get("/api/v1/batches/{batch_id}/logs", response_model=APIResponse)
async def get_batch_logs(
    batch_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    query = db.query(FermentationLog).filter(FermentationLog.batch_id == batch_id)
    total = query.count()
    logs = query.order_by(FermentationLog.log_date.desc()).limit(limit).offset(offset).all()
    
    logs_data = []
    for log in logs:
        logs_data.append({
            "id": log.id,
            "log_date": log.log_date.isoformat(),
            "aroma": log.aroma,
            "color": log.color,
            "gas_presence": log.gas_presence,
            "temperature_c": log.temperature_c,
            "ai_status": log.ai_status,
            "ai_confidence": log.ai_confidence,
            "ai_suggestion": log.ai_suggestion,
            "created_at": log.created_at.isoformat()
        })
    
    return APIResponse(
        status="success",
        data={
            "logs": logs_data,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(logs_data) < total
        }
    )

@app.post("/api/v1/batches/{batch_id}/daily-logs", response_model=APIResponse)
async def create_daily_log(
    batch_id: int,
    log_data: BatchDailyLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mencatat progres harian untuk batch eco-enzyme yang sedang aktif.
    """
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    try:
        new_daily_log = BatchDailyLog(
            batch_id=batch_id,
            log_date=log_data.log_date,
            action_taken=log_data.action_taken,
            condition=log_data.condition,
            notes=log_data.notes
        )
        db.add(new_daily_log)
        db.commit()
        db.refresh(new_daily_log)
        
        logger.info(f"Daily log created", extra={"user_id": current_user.id, "batch_id": batch_id, "daily_log_id": new_daily_log.id})
        
        return APIResponse(
            status="success",
            message="Progres harian berhasil dicatat!",
            data={
                "log_id": new_daily_log.id,
                "batch_id": batch_id,
                "log_date": new_daily_log.log_date.isoformat(),
                "action_taken": new_daily_log.action_taken,
                "condition": new_daily_log.condition,
                "notes": new_daily_log.notes
            }
        )
    except Exception as e:
        logger.error(f"Daily log creation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create daily log")


@app.get("/api/v1/batches/{batch_id}/daily-logs", response_model=APIResponse)
async def get_batch_daily_logs(
    batch_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mengambil riwayat progres harian dari batch tertentu.
    """
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    query = db.query(BatchDailyLog).filter(BatchDailyLog.batch_id == batch_id)
    total = query.count()
    daily_logs = query.order_by(BatchDailyLog.log_date.desc()).limit(limit).offset(offset).all()
    
    logs_data = []
    for log in daily_logs:
        logs_data.append({
            "id": log.id,
            "batch_id": log.batch_id,
            "log_date": log.log_date.isoformat(),
            "action_taken": log.action_taken,
            "condition": log.condition,
            "notes": log.notes,
            "created_at": log.created_at.isoformat()
        })
    
    return APIResponse(
        status="success",
        data={
            "daily_logs": logs_data,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(logs_data) < total
        }
    )


@app.put("/api/v1/batches/{batch_id}/status", response_model=APIResponse)
async def update_batch_status(
    batch_id: int,
    status_data: BatchStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch tidak ditemukan")
        
    old_status = batch.status
    new_status = status_data.new_status
    valid_statuses = ["pending_start", "in_progress", "completed", "harvested", "failed", "paused"]
    
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status '{new_status}' tidak valid")
        
    valid = True
    if old_status == "pending_start" and new_status != "in_progress":
        valid = False
    elif old_status == "in_progress" and new_status not in ["completed", "failed", "paused"]:
        valid = False
    elif old_status == "paused" and new_status not in ["in_progress", "failed"]:
        valid = False
    elif old_status == "completed" and new_status != "harvested":
        valid = False
    elif old_status in ["failed", "harvested"]:
        valid = False
        
    if not valid:
        raise HTTPException(status_code=400, detail=f"Transisi status dari '{old_status}' ke '{new_status}' tidak diizinkan")
        
    batch.status = new_status
    
    if new_status in ["completed", "harvested"] and old_status not in ["completed", "harvested"]:
        current_user.waste_diverted_kg += batch.waste_weight_kg
    elif old_status in ["completed", "harvested"] and new_status not in ["completed", "harvested"]:
        current_user.waste_diverted_kg = max(0.0, current_user.waste_diverted_kg - batch.waste_weight_kg)
        
    db.commit()
    db.refresh(batch)
    
    AuditService.log_from_request(
        db=db,
        request=request,
        user_id=current_user.id,
        action="UPDATE_STATUS",
        resource_type="batch",
        resource_id=batch_id,
        details={"old_status": old_status, "new_status": new_status, "notes": status_data.notes}
    )
    
    return APIResponse(status="success", message="Status batch berhasil diperbarui", data={"id": batch.id, "status": batch.status})

@app.delete("/api/v1/batches/{batch_id}", response_model=APIResponse)
async def delete_batch(
    batch_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch tidak ditemukan")
    
    batch_name = batch.name
    batch_status = batch.status
        
    db.query(FermentationLog).filter(FermentationLog.batch_id == batch_id).delete()
    db.query(BatchDailyLog).filter(BatchDailyLog.batch_id == batch_id).delete()
    db.query(RoadmapProgress).filter(RoadmapProgress.batch_id == batch_id).delete()
    db.query(ProductRecommendation).filter(ProductRecommendation.batch_id == batch_id).delete()
    
    if batch.status in ["completed", "harvested"]:
        current_user.waste_diverted_kg = max(0.0, current_user.waste_diverted_kg - batch.waste_weight_kg)
        
    db.delete(batch)
    db.commit()
    
    AuditService.log_from_request(
        db=db,
        request=request,
        user_id=current_user.id,
        action="DELETE",
        resource_type="batch",
        resource_id=batch_id,
        details={"batch_name": batch_name, "batch_status": batch_status}
    )
    
    return APIResponse(status="success", message="Batch berhasil dihapus")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}




