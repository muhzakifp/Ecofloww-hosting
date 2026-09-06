from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.base import User, FermentationBatch, FermentationLog, ProductRecommendation, ProductTemplate
from app.schemas.base import APIResponse
from app.services.product_recommendation import ProductRecommendationService
from app.services.business_analysis import BusinessAnalysisService
from app.services.report import ReportService
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["recommendations"])

class RecommendationRequest(BaseModel):
    harvest_date: datetime
    harvest_volume_liters: float
    final_color: str
    aroma_intensity: str
    user_intent: str = "household"

class SelectProductRequest(BaseModel):
    product_template_id: int

class CheckRatioRequest(BaseModel):
    waste_kg: float
    water_liters: float
    sugar_kg: float

class BusinessAnalysisRequest(BaseModel):
    product_name: str
    production_volume_liters: float
    target_market: str
    packaging_type: str
    distribution_channel: str
    raw_material_cost: float
    packaging_cost: float
    labor_cost: float
    overhead_cost: float
    monthly_fixed_costs: float
    regional_average_price: float = None

@router.post("/batches/{batch_id}/recommendation", response_model=APIResponse)
async def get_product_recommendation(
    batch_id: int,
    rec_request: RecommendationRequest,
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
        recommendations = ProductRecommendationService.get_ranked_recommendations(
            final_color=rec_request.final_color,
            aroma_intensity=rec_request.aroma_intensity,
            final_volume_liters=rec_request.harvest_volume_liters,
            user_intent=rec_request.user_intent,
            db=db
        )
        
        batch.final_volume_liters = rec_request.harvest_volume_liters
        batch.final_color = rec_request.final_color
        batch.final_aroma_intensity = rec_request.aroma_intensity
        batch.status = "harvested"
        
        prod_rec = db.query(ProductRecommendation).filter(
            ProductRecommendation.batch_id == batch_id
        ).first()
        
        if prod_rec:
            prod_rec.recommended_products_json = recommendations
            prod_rec.is_commercial_orientation = (rec_request.user_intent == "commercial")
        else:
            prod_rec = ProductRecommendation(
                batch_id=batch_id,
                user_id=current_user.id,
                recommended_products_json=recommendations,
                is_commercial_orientation=(rec_request.user_intent == "commercial")
            )
            db.add(prod_rec)
        
        db.commit()
        
        return APIResponse(
            status="success",
            message="Product recommendations generated",
            data={"recommendations": recommendations}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/batches/{batch_id}/select-product", response_model=APIResponse)
async def select_product_for_batch(
    batch_id: int,
    req: SelectProductRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    template = db.query(ProductTemplate).filter(ProductTemplate.id == req.product_template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product template not found")
    
    prod_rec = db.query(ProductRecommendation).filter(
        ProductRecommendation.batch_id == batch_id
    ).first()
    
    if not prod_rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recommendations found for this batch")
    
    prod_rec.selected_product_id = req.product_template_id
    prod_rec.selection_date = datetime.now(timezone.utc)
    batch.selected_product_id = req.product_template_id
    db.commit()
    
    return APIResponse(
        status="success",
        message="Product selected successfully",
        data={"selected_product_id": req.product_template_id}
    )

@router.post("/check-ingredient-ratio", response_model=APIResponse)
async def check_ingredient_ratio(
    req: CheckRatioRequest,
    current_user: User = Depends(get_current_user),
):
    from app.services.eco_enzyme import EcoEnzymeService
    ideal = EcoEnzymeService.calculate_ingredients(req.waste_kg)
    warning = EcoEnzymeService.check_ingredient_deviation(
        waste_kg=req.waste_kg,
        user_water=req.water_liters,
        user_sugar=req.sugar_kg,
        threshold=0.1
    )
    
    return APIResponse(
        status="success",
        message="Ratio check complete",
        data={
            "ideal_water_liters": ideal["ideal_water_liters"],
            "ideal_sugar_kg": ideal["ideal_sugar_kg"],
            "deviation_warning": warning
        }
    )

@router.post("/batches/{batch_id}/business-analysis", response_model=APIResponse)
async def run_business_analysis(
    batch_id: int,
    analysis_request: BusinessAnalysisRequest,
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
        analysis = BusinessAnalysisService.run_analysis(
            production_volume_liters=analysis_request.production_volume_liters,
            raw_material_cost=analysis_request.raw_material_cost,
            packaging_cost=analysis_request.packaging_cost,
            labor_cost=analysis_request.labor_cost,
            overhead_cost=analysis_request.overhead_cost,
            monthly_fixed_costs=analysis_request.monthly_fixed_costs,
            regional_average_price=analysis_request.regional_average_price
        )
        
        prod_rec = db.query(ProductRecommendation).filter(
            ProductRecommendation.batch_id == batch_id
        ).first()
        
        if prod_rec:
            prod_rec.business_analysis_json = analysis
        else:
            prod_rec = ProductRecommendation(
                batch_id=batch_id,
                user_id=current_user.id,
                recommended_products_json=[],
                business_analysis_json=analysis
            )
            db.add(prod_rec)
        
        db.commit()
        
        return APIResponse(
            status="success",
            message="Business analysis completed",
            data=analysis
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/batches/{batch_id}/business-analysis/report")
async def get_business_analysis_report(
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

    prod_rec = db.query(ProductRecommendation).filter(
        ProductRecommendation.batch_id == batch_id
    ).first()

    if not prod_rec or not prod_rec.business_analysis_json:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business analysis not found")

    report_data = ReportService.generate_business_report(batch_id, prod_rec.business_analysis_json)

    return Response(
        content=report_data["content"],
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="business-analysis-batch-{batch_id}.pdf"'}
    )

@router.get("/batches/{batch_id}/dashboard", response_model=APIResponse)
async def get_user_dashboard(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.fermentation_assistant import FermentationAssistantService
    
    batch = db.query(FermentationBatch).filter(
        FermentationBatch.id == batch_id,
        FermentationBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    logs = db.query(FermentationLog).filter(FermentationLog.batch_id == batch_id).order_by(FermentationLog.log_date.desc()).all()
    
    latest_log = logs[0] if logs else None
    incubation_days = (datetime.now(timezone.utc).date() - batch.start_date.date()).days if batch.start_date else 0
    
    latest_health_score = None
    if latest_log:
        latest_health_score = round(FermentationAssistantService.calculate_health_score(
            latest_log.ai_status, latest_log.ai_confidence, incubation_days
        ), 2)
    
    return APIResponse(
        status="success",
        data={
            "batch_id": batch.id,
            "batch_name": batch.name,
            "status": batch.status,
            "waste_diverted_kg": batch.waste_weight_kg,
            "incubation_days": incubation_days,
            "expected_harvest_date": batch.harvest_date.isoformat() if batch.harvest_date else None,
            "latest_status": latest_log.ai_status if latest_log else None,
            "latest_health_score": latest_health_score,
            "total_logs": len(logs),
            "upcoming_milestones": [
                {"day": 30, "description": "Mid-fermentation check"},
                {"day": 60, "description": "Color development check"},
                {"day": 90, "description": "Expected harvest readiness"}
            ]
        }
    )
