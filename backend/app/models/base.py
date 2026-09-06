from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Community(Base):
    __tablename__ = "communities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    region = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    users = relationship("User", back_populates="community")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    phone = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    role = Column(String, default="user")
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=True, index=True)
    waste_diverted_kg = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    community = relationship("Community", back_populates="users")
    batches = relationship("FermentationBatch", back_populates="user")


class FermentationBatch(Base):
    __tablename__ = "fermentation_batches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String)
    status = Column(String, default="pending", index=True)
    waste_weight_kg = Column(Float)
    water_liters = Column(Float)
    sugar_kg = Column(Float)
    start_date = Column(DateTime)
    harvest_date = Column(DateTime, nullable=True)
    final_volume_liters = Column(Float, nullable=True)
    final_color = Column(String, nullable=True)
    final_aroma_intensity = Column(String, nullable=True)
    selected_product_id = Column(Integer, ForeignKey("product_templates.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="batches")
    logs = relationship("FermentationLog", back_populates="batch")
    recommendation = relationship("ProductRecommendation", back_populates="batch", uselist=False)


class FermentationLog(Base):
    __tablename__ = "fermentation_logs"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("fermentation_batches.id"), nullable=False, index=True)
    log_date = Column(DateTime)
    aroma = Column(String)
    color = Column(String)
    gas_presence = Column(Boolean)
    temperature_c = Column(Float)
    notes = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    ai_status = Column(String, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    batch = relationship("FermentationBatch", back_populates="logs")


class ProductTemplate(Base):
    __tablename__ = "product_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    processing_instructions = Column(Text)
    ingredients = Column(JSON)
    equipment = Column(JSON)
    time_estimate_hours = Column(Float)
    safety_warnings = Column(Text)
    base_compatibility_score = Column(Float, default=0.5)
    ideal_ph_min = Column(Float, nullable=True)
    ideal_ph_max = Column(Float, nullable=True)
    ideal_aroma = Column(String, nullable=True)
    ideal_color = Column(String, nullable=True)
    tutorial_url = Column(String, nullable=True)
    regional_average_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class ProductRecommendation(Base):
    __tablename__ = "product_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("fermentation_batches.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    recommended_products_json = Column(JSON)
    selected_product_id = Column(Integer, ForeignKey("product_templates.id"), nullable=True)
    selection_date = Column(DateTime, nullable=True)
    is_commercial_orientation = Column(Boolean, default=False)
    business_analysis_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    batch = relationship("FermentationBatch", back_populates="recommendation")


class RoadmapProgress(Base):
    __tablename__ = "roadmap_progress"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("fermentation_batches.id"), nullable=False, index=True)
    product_template_id = Column(Integer, ForeignKey("product_templates.id"), index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    steps_json = Column(JSON, default=list)
    current_step = Column(Integer, default=0)
    status = Column(String, default="not_started")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", backref="roadmaps")
    batch = relationship("FermentationBatch", backref="roadmap")
    template = relationship("ProductTemplate")


class BatchDailyLog(Base):
    __tablename__ = "batch_daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("fermentation_batches.id"), nullable=False, index=True)
    log_date = Column(DateTime, nullable=False)
    action_taken = Column(String, nullable=False)
    condition = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    batch = relationship("FermentationBatch", backref="daily_logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=False, index=True)
    resource_id = Column(String, nullable=True, index=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    status = Column(String, default="success")
    created_at = Column(DateTime, default=utcnow, index=True)

    user = relationship("User", backref="audit_logs")
