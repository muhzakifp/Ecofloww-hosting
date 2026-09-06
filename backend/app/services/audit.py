from sqlalchemy.orm import Session
from app.models.base import AuditLog
from typing import Optional, Dict, Any
from fastapi import Request


class AuditService:
    """Service untuk mencatat audit trail aktivitas user."""

    @staticmethod
    def log_action(
        db: Session,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success"
    ) -> AuditLog:
        """
        Catat aktivitas user ke audit log.
        
        Args:
            db: SQLAlchemy session
            user_id: UID user yang melakukan aksi (None jika anonymous/system)
            action: Jenis aksi (CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, dll)
            resource_type: Tipe resource (batch, user, roadmap, recommendation, dll)
            resource_id: ID resource yang diakses (opsional)
            details: Detail tambahan dalam format dict (akan disimpan sebagai JSON)
            ip_address: IP address client
            user_agent: User agent string
            status: Status aksi (success, failed, unauthorized)
        
        Returns:
            AuditLog object yang sudah disimpan
        """
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    @staticmethod
    def log_from_request(
        db: Session,
        request: Request,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ) -> AuditLog:
        """
        Helper untuk log audit dari FastAPI Request object.
        
        Otomatis extract IP address dan user agent dari request.
        """
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", None)
        
        return AuditService.log_action(
            db=db,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
