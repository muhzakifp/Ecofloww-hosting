from datetime import date
import csv
import io
from typing import List as TList, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.base import Community, ProductTemplate, User
from app.schemas.base import APIResponse, CommunityCreate, ProductTemplateCreate, ProductTemplateUpdate
from app.services.admin import AdminService
from app.services.audit import AuditService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

class UserRoleUpdate(BaseModel):
    role: str


class PricingImportItem(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    regional_average_price: float = Field(ge=0)


class PricingImportRequest(BaseModel):
    items: TList[PricingImportItem]


def scope_community_id(current_user: User, role: str, community_id: int | None) -> int | None:
    if role == "community_admin":
        return current_user.community_id
    return community_id

@router.get("/communities", response_model=APIResponse)
async def list_communities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    role: str = Depends(require_role("admin", "community_admin", "platform_admin")),
):
    query = db.query(Community).order_by(Community.name)
    if role == "community_admin":
        query = query.filter(Community.id == current_user.community_id)
    communities = query.all()
    return APIResponse(
        status="success",
        data={"communities": [{"id": item.id, "name": item.name, "region": item.region} for item in communities]},
    )

@router.post("/communities", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_community(
    community_data: CommunityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    role: str = Depends(require_role("admin", "platform_admin")),
):
    existing = db.query(Community).filter(Community.name == community_data.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Community already exists")
    community = Community(**community_data.model_dump())
    db.add(community)
    db.commit()
    db.refresh(community)
    return APIResponse(status="success", message="Community created", data={"id": community.id})

@router.get("/community-stats", response_model=APIResponse)
async def get_community_stats(
    community_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    role: str = Depends(require_role("admin", "community_admin", "platform_admin"))
):
    try:
        stats = AdminService.get_community_stats(db, scope_community_id(current_user, role, community_id), start_date, end_date)
        return APIResponse(
            status="success",
            data=stats
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/community-trends", response_model=APIResponse)
async def get_community_trends(
    days: int = 30,
    community_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    role: str = Depends(require_role("admin", "community_admin", "platform_admin")),
):
    try:
        return APIResponse(
            status="success",
            data=AdminService.get_community_trends(db, days, scope_community_id(current_user, role, community_id)),
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load community trends")

@router.get("/community-compliance-report")
async def download_community_compliance_report(
    community_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    role: str = Depends(require_role("admin", "community_admin", "platform_admin")),
):
    scoped_id = scope_community_id(current_user, role, community_id)
    stats = AdminService.get_community_stats(db, scoped_id, start_date, end_date)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["metric", "value"])
    writer.writerow(["community_id", scoped_id or "all"])
    writer.writerow(["start_date", start_date.isoformat() if start_date else ""])
    writer.writerow(["end_date", end_date.isoformat() if end_date else ""])
    writer.writerow(["total_users", stats["total_users"]])
    writer.writerow(["total_batches", stats["total_batches"]])
    writer.writerow(["total_waste_processed_kg", stats["total_waste_processed_kg"]])
    writer.writerow(["success_rate_percentage", stats["success_rate_percentage"]])
    writer.writerow(["total_logs", stats["total_logs"]])
    writer.writerow(["normal_logs", stats["normal_logs"]])
    writer.writerow(["caution_logs", stats["caution_logs"]])
    writer.writerow(["failed_logs", stats["failed_logs"]])
    writer.writerow(["log_adoption_percentage", stats["engagement"]["log_adoption_percentage"]])
    writer.writerow(["recommendation_adoption_percentage", stats["engagement"]["recommendation_adoption_percentage"]])
    writer.writerow(["roadmap_adoption_percentage", stats["engagement"]["roadmap_adoption_percentage"]])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=community-compliance-report.csv"},
    )

@router.get("/product-templates", response_model=APIResponse)
async def list_product_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    role: str = Depends(require_role("admin", "platform_admin")),
):
    templates = db.query(ProductTemplate).order_by(ProductTemplate.id).all()
    return APIResponse(
        status="success",
        data={"templates": [
            {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "processing_instructions": template.processing_instructions,
                "ingredients": template.ingredients,
                "equipment": template.equipment,
                "time_estimate_hours": template.time_estimate_hours,
                "safety_warnings": template.safety_warnings,
                "base_compatibility_score": template.base_compatibility_score,
                "tutorial_url": template.tutorial_url,
                "regional_average_price": template.regional_average_price,
            }
            for template in templates
        ]},
    )

@router.post("/product-templates", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_product_template(
    template_data: ProductTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    role: str = Depends(require_role("admin", "platform_admin")),
):
    existing = db.query(ProductTemplate).filter(ProductTemplate.name == template_data.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product template already exists")
    template = ProductTemplate(**template_data.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return APIResponse(status="success", message="Product template created", data={"id": template.id})

@router.patch("/product-templates/{template_id}", response_model=APIResponse)
async def update_product_template(
    template_id: int,
    template_data: ProductTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    role: str = Depends(require_role("admin", "platform_admin")),
):
    template = db.query(ProductTemplate).filter(ProductTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product template not found")
    for field, value in template_data.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    db.commit()
    return APIResponse(status="success", message="Product template updated", data={"id": template.id})

@router.delete("/product-templates/{template_id}", response_model=APIResponse)
async def delete_product_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    role: str = Depends(require_role("admin", "platform_admin")),
):
    template = db.query(ProductTemplate).filter(ProductTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product template not found")
    db.delete(template)
    db.commit()
    return APIResponse(status="success", message="Product template deleted", data={"id": template_id})

@router.post("/product-templates/import-pricing", response_model=APIResponse)
async def import_product_pricing(
    req: PricingImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    role: str = Depends(require_role("admin", "platform_admin")),
):
    updated = []
    not_found = []
    for item in req.items:
        template = db.query(ProductTemplate).filter(ProductTemplate.name == item.name).first()
        if template:
            template.regional_average_price = item.regional_average_price
            updated.append(item.name)
        else:
            not_found.append(item.name)
    db.commit()
    return APIResponse(
        status="success",
        message=f"Updated {len(updated)} template(s)",
        data={"updated": updated, "not_found": not_found},
    )

@router.get("/model-metrics", response_model=APIResponse)
async def get_model_metrics(
    current_user: User = Depends(get_current_user),
    role: str = Depends(require_role("admin", "community_admin", "platform_admin"))
):
    try:
        metrics = AdminService.get_model_metrics()
        return APIResponse(
            status="success",
            data=metrics
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.patch("/users/{user_id}/role", response_model=APIResponse)
async def update_user_role(
    user_id: str,
    req: UserRoleUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    role: str = Depends(require_role("admin", "platform_admin")),
    db: Session = Depends(get_db)
):
    valid_roles = ("user", "admin", "community_admin", "platform_admin")
    if req.role not in valid_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role. Must be one of {valid_roles}")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    old_role = user.role
    user.role = req.role
    db.commit()
    db.refresh(user)
    
    AuditService.log_from_request(
        db=db,
        request=request,
        user_id=current_user.id,
        action="UPDATE_ROLE",
        resource_type="user",
        resource_id=user_id,
        details={
            "target_user_email": user.email,
            "old_role": old_role,
            "new_role": req.role,
            "changed_by": current_user.email
        }
    )
    
    return APIResponse(
        status="success",
        message=f"User role updated to {req.role}",
        data={"user_id": user_id, "role": user.role}
    )
