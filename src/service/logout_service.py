from fastapi import Request, HTTPException
from prisma import Prisma
import jwt
from datetime import datetime
from src.auth import SECRET_KEY, ALGORITHM


async def logout_service(request: Request):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")

    if not token.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid token format")

    token = token.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_rfc = payload.get("sub")
        if not user_rfc:
            raise HTTPException(status_code=400, detail="Invalid token payload")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = Prisma()
    await db.connect()
    try:
        await db.authtoken.update_many(
            where={"token": token, "user_id": user_rfc, "revoked_at": None},
            data={"revoked_at": datetime.now()}
        )
        return {"message": "Successfully logged out"}
    # Esto elimina el token
    # try:
    #     await db.authtoken.delete_many(
    #         where={"user_id": user_rfc}
    #     )
    #     return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging out: {str(e)}")
    finally:
        await db.disconnect()
