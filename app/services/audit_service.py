"""
Audit logging service for compliance and security tracking.

This service handles audit log creation, retrieval, and analysis
for HIPAA compliance and security monitoring.
"""

from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.user import AuditLog, User
from app.schemas.audit import AuditLogCreate, AuditLogFilter, AuditLogStats
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AuditService:
    """
    Audit logging service for compliance tracking.
    
    Handles creation, retrieval, and analysis of audit logs
    for security and compliance purposes.
    """
    
    def log_action(
        self,
        db: Session,
        log_data: AuditLogCreate
    ) -> AuditLog:
        """
        Create an audit log entry.
        
        Args:
            db: Database session
            log_data: Audit log data
            
        Returns:
            Created audit log object
        """
        audit_log = AuditLog(
            user_id=log_data.user_id,
            action=log_data.action,
            resource=log_data.resource,
            resource_id=log_data.resource_id,
            details=log_data.details,
            ip_address=log_data.ip_address,
            user_agent=log_data.user_agent,
            status=log_data.status
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        logger.debug(
            f"Audit log created: user_id={log_data.user_id}, "
            f"action={log_data.action}, resource={log_data.resource}, "
            f"status={log_data.status}"
        )
        
        return audit_log
    
    def get_logs(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        filter_params: Optional[AuditLogFilter] = None
    ) -> Tuple[List[AuditLog], int]:
        """
        Get audit logs with optional filtering and pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filter_params: Optional filter parameters
            
        Returns:
            Tuple of (audit logs list, total count)
        """
        query = db.query(AuditLog)
        
        # Apply filters if provided
        if filter_params:
            if filter_params.user_id is not None:
                query = query.filter(AuditLog.user_id == filter_params.user_id)
            
            if filter_params.action:
                query = query.filter(AuditLog.action == filter_params.action)
            
            if filter_params.resource:
                query = query.filter(AuditLog.resource == filter_params.resource)
            
            if filter_params.status:
                query = query.filter(AuditLog.status == filter_params.status)
            
            if filter_params.start_date:
                query = query.filter(AuditLog.timestamp >= filter_params.start_date)
            
            if filter_params.end_date:
                query = query.filter(AuditLog.timestamp <= filter_params.end_date)
        
        # Order by timestamp descending (newest first)
        query = query.order_by(AuditLog.timestamp.desc())
        
        total = query.count()
        logs = query.offset(skip).limit(limit).all()
        
        return logs, total
    
    def get_user_logs(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """
        Get audit logs for a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (audit logs list, total count)
        """
        query = db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.timestamp.desc())
        
        total = query.count()
        logs = query.offset(skip).limit(limit).all()
        
        return logs, total
    
    def get_recent_failures(
        self,
        db: Session,
        limit: int = 10
    ) -> List[AuditLog]:
        """
        Get recent failed actions.
        
        Args:
            db: Database session
            limit: Maximum number of records to return
            
        Returns:
            List of recent failed audit logs
        """
        return db.query(AuditLog).filter(
            AuditLog.status == "failure"
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    def get_stats(self, db: Session) -> AuditLogStats:
        """
        Get audit log statistics.
        
        Args:
            db: Database session
            
        Returns:
            AuditLogStats object
        """
        # Total logs
        total_logs = db.query(AuditLog).count()
        
        # Successful/failed actions
        successful_actions = db.query(AuditLog).filter(
            AuditLog.status == "success"
        ).count()
        
        failed_actions = db.query(AuditLog).filter(
            AuditLog.status == "failure"
        ).count()
        
        # Unique users
        unique_users = db.query(func.count(func.distinct(AuditLog.user_id))).scalar()
        
        # Actions by type
        actions_by_type = {}
        action_counts = db.query(
            AuditLog.action,
            func.count(AuditLog.id)
        ).group_by(AuditLog.action).all()
        
        for action, count in action_counts:
            actions_by_type[action] = count
        
        # Recent failures
        recent_failures = self.get_recent_failures(db, limit=5)
        
        return AuditLogStats(
            total_logs=total_logs,
            successful_actions=successful_actions,
            failed_actions=failed_actions,
            unique_users=unique_users or 0,
            actions_by_type=actions_by_type,
            recent_failures=recent_failures
        )
    
    def get_user_activity(
        self,
        db: Session,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        Get user activity summary.
        
        Args:
            db: Database session
            user_id: User ID
            start_date: Start date for date range
            end_date: End date for date range
            
        Returns:
            Dict with activity counts by action type
        """
        query = db.query(
            AuditLog.action,
            func.count(AuditLog.id)
        ).filter(AuditLog.user_id == user_id)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        results = query.group_by(AuditLog.action).all()
        
        activity = {}
        for action, count in results:
            activity[action] = count
        
        return activity
    
    def get_failed_login_attempts(
        self,
        db: Session,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        hours: int = 24
    ) -> List[AuditLog]:
        """
        Get failed login attempts.
        
        Args:
            db: Database session
            username: Filter by username (optional)
            ip_address: Filter by IP address (optional)
            hours: Number of hours to look back (default: 24)
            
        Returns:
            List of failed login audit logs
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(AuditLog).filter(
            and_(
                AuditLog.action == "login",
                AuditLog.status == "failure",
                AuditLog.timestamp >= cutoff_time
            )
        )
        
        if username:
            # Join with User to filter by username
            query = query.join(User).filter(User.username == username)
        
        if ip_address:
            query = query.filter(AuditLog.ip_address == ip_address)
        
        return query.order_by(AuditLog.timestamp.desc()).all()
    
    def cleanup_old_logs(
        self,
        db: Session,
        days: int = 90
    ) -> int:
        """
        Delete audit logs older than specified days.
        
        Note: For compliance, consider archiving instead of deleting.
        
        Args:
            db: Database session
            days: Number of days to retain (default: 90)
            
        Returns:
            Number of logs deleted
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = db.query(AuditLog).filter(
            AuditLog.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} audit logs older than {days} days")
        return deleted_count
    
    def get_resource_access_log(
        self,
        db: Session,
        resource: str,
        resource_id: Optional[str] = None,
        limit: int = 50
    ) -> List[AuditLog]:
        """
        Get access logs for a specific resource.
        
        Args:
            db: Database session
            resource: Resource type
            resource_id: Specific resource ID (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of audit logs
        """
        query = db.query(AuditLog).filter(
            AuditLog.resource == resource
        )
        
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    def export_logs_csv(
        self,
        db: Session,
        filter_params: Optional[AuditLogFilter] = None
    ) -> str:
        """
        Export audit logs to CSV format.
        
        Args:
            db: Database session
            filter_params: Optional filter parameters
            
        Returns:
            CSV string
        """
        import csv
        from io import StringIO
        
        logs, _ = self.get_logs(db, skip=0, limit=10000, filter_params=filter_params)
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'User ID', 'Username', 'Action', 'Resource', 'Resource ID',
            'Status', 'IP Address', 'Timestamp', 'Details'
        ])
        
        # Write data
        for log in logs:
            username = log.user.username if log.user else 'N/A'
            writer.writerow([
                log.id,
                log.user_id or 'N/A',
                username,
                log.action,
                log.resource,
                log.resource_id or 'N/A',
                log.status,
                log.ip_address or 'N/A',
                log.timestamp.isoformat(),
                log.details or 'N/A'
            ])
        
        return output.getvalue()
