from fastapi import Request

def get_tenant_id(request: Request) -> str:
    return request.headers.get("X-Tenant-ID", "default")