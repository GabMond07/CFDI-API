from fastapi import Depends, HTTPException
from src.auth import get_current_user
from typing import List
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def require_permissions(required_permissions: List[str]):
    """
    Decorador para verificar si el usuario tiene los permisos necesarios.
    """
    async def check_permissions(user: dict = Depends(get_current_user)):
        start_time = datetime.now(timezone.utc)
        
        # Obtener permisos del usuario
        user_scopes = user.get("role", {}).get("permissions", {}).get("scopes", [])
        
        # Verificar si el usuario tiene todos los permisos requeridos
        missing_permissions = [perm for perm in required_permissions if perm not in user_scopes]
        if missing_permissions:
            logger.error(f"Usuario {user['rfc']} no tiene permisos: {missing_permissions}")
            raise HTTPException(status_code=403, detail=f"Missing required permissions: {missing_permissions}")
        
        logger.info(f"Verificación de permisos tomó {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
        return user
    
    return check_permissions