"""
Tareas de limpieza y mantenimiento del sistema.

Implementa retencion de datos segun ISO 27001 y Ley 21.719.
"""

import logging
from datetime import timedelta
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="core.cleanup_task_results")
def cleanup_task_results(self, retention_days=None):
    """
    Limpia resultados de tareas Celery antiguos.
    
    Mantiene conformidad con politicas de retencion para auditoria.
    Los resultados mas antiguos que retention_days se eliminan.
    
    Args:
        retention_days: Dias de retencion. Si no se especifica,
                       usa CELERY_RESULT_EXPIRES_DAYS (default 90).
    
    Returns:
        dict con:
            - deleted_count: cantidad de registros eliminados
            - retention_days: dias de retencion aplicados
            - cutoff_date: fecha de corte usada
    
    Compliance:
        - ISO 27001: A.8.10 - Eliminacion de informacion
        - Ley 21.719: Art. 25 - Supresion de datos
    """
    from django_celery_results.models import TaskResult
    
    # Obtener dias de retencion
    if retention_days is None:
        # CELERY_RESULT_EXPIRES esta en segundos
        result_expires = getattr(settings, "CELERY_RESULT_EXPIRES", 90 * 24 * 60 * 60)
        retention_days = result_expires // (24 * 60 * 60)
    
    cutoff_date = timezone.now() - timedelta(days=retention_days)
    
    logger.info(
        f"[Task {self.request.id}] Iniciando limpieza de TaskResults. "
        f"Retencion: {retention_days} dias, Fecha corte: {cutoff_date}"
    )
    
    try:
        # Contar antes de eliminar
        old_results = TaskResult.objects.filter(date_done__lt=cutoff_date)
        count = old_results.count()
        
        if count > 0:
            # Eliminar en batches para evitar locks largos
            deleted_total = 0
            batch_size = 1000
            
            while True:
                # Obtener IDs a eliminar
                ids_to_delete = list(
                    TaskResult.objects.filter(date_done__lt=cutoff_date)
                    .values_list("id", flat=True)[:batch_size]
                )
                
                if not ids_to_delete:
                    break
                
                deleted, _ = TaskResult.objects.filter(id__in=ids_to_delete).delete()
                deleted_total += deleted
                
                logger.debug(f"[Task {self.request.id}] Eliminados {deleted} registros (batch)")
            
            logger.info(
                f"[Task {self.request.id}] Limpieza completada. "
                f"Eliminados: {deleted_total} registros"
            )
            
            return {
                "success": True,
                "deleted_count": deleted_total,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
            }
        else:
            logger.info(f"[Task {self.request.id}] No hay registros para eliminar")
            return {
                "success": True,
                "deleted_count": 0,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
            }
            
    except Exception as e:
        logger.error(f"[Task {self.request.id}] Error en limpieza: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat(),
        }


@shared_task(bind=True, name="core.cleanup_audit_logs")
def cleanup_audit_logs(self, retention_days=365):
    """
    Limpia logs de auditoría antiguos.
    
    Retención default: 365 días (requisito legal).
    
    Args:
        retention_days: Días de retención (default 365 para cumplimiento legal)
    
    Returns:
        dict con resultados de la limpieza
    
    Compliance:
        - ISO 27001: A.8.10 - Eliminación de información
        - Ley 21.719: Art. 25 - Supresión de datos (mínimo 1 año)
    """
    from apps.core.models import AuditLog
    
    cutoff_date = timezone.now() - timedelta(days=retention_days)
    
    logger.info(
        f"[Task {self.request.id}] Iniciando limpieza de AuditLogs. "
        f"Retención: {retention_days} días, Fecha corte: {cutoff_date}"
    )
    
    try:
        # Eliminar en batches
        deleted_total = 0
        batch_size = 1000
        
        while True:
            ids_to_delete = list(
                AuditLog.objects.filter(timestamp__lt=cutoff_date)
                .values_list("id", flat=True)[:batch_size]
            )
            
            if not ids_to_delete:
                break
            
            deleted, _ = AuditLog.objects.filter(id__in=ids_to_delete).delete()
            deleted_total += deleted
            
            logger.debug(f"[Task {self.request.id}] Eliminados {deleted} AuditLogs (batch)")
        
        logger.info(
            f"[Task {self.request.id}] Limpieza de AuditLogs completada. "
            f"Eliminados: {deleted_total} registros"
        )
        
        return {
            "success": True,
            "deleted_count": deleted_total,
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat(),
        }
        
    except Exception as e:
        logger.error(f"[Task {self.request.id}] Error en limpieza de AuditLogs: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat(),
        }
