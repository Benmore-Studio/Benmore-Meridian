---
name: pcs-add-endpoint
description: Use when adding a new CRUD endpoint to any PCS microservice - generates router, schema, service method, audit event, Kafka emission, and test following PCS conventions
---

# PCS: Add Endpoint

Add a complete CRUD endpoint to an existing PCS microservice.

## Files Touched

| File | What to add |
|------|-------------|
| `app/routers/{resource}.py` | Route handlers with `Depends(get_tenant_context)` |
| `app/schemas/{resource}.py` | Create, Update, Response Pydantic models |
| `app/services/{resource}_service.py` | Business logic (always filter by org_id) |
| `app/events/emitters.py` | Topic constant + emit function |
| `app/main.py` | Register router |
| `tests/test_{resource}.py` | CRUD + tenant isolation tests |

## Router Template

```python
router = APIRouter(prefix="/api/v1/{resources}", tags=["{Resources}"])

@router.post("", status_code=201, response_model=DataResponse[{Resource}Response])
async def create_{resource}(
    data: {Resource}Create,
    context: Annotated[TenantContext, Depends(get_tenant_context)],
    service=Depends(get_{resource}_service),
):
    result = await service.create(data, context.org_id, context.user_id)
    return DataResponse(success=True, data=result, message="{Resource} created")

@router.get("", response_model=PaginatedResponse[{Resource}Response])
async def list_{resources}(
    context: Annotated[TenantContext, Depends(get_tenant_context)],
    service=Depends(get_{resource}_service),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
):
    items, total = await service.list(context.org_id, page, page_size)
    return PaginatedResponse(success=True, data=items, total=total, page=page, page_size=page_size)

@router.get("/{id}", response_model=DataResponse[{Resource}Response])
async def get_{resource}(id: UUID, context=Depends(get_tenant_context), service=Depends(get_{resource}_service)):
    return DataResponse(success=True, data=await service.get(id, context.org_id))

@router.put("/{id}", response_model=DataResponse[{Resource}Response])
async def update_{resource}(id: UUID, data: {Resource}Update, context=Depends(get_tenant_context), service=Depends(get_{resource}_service)):
    return DataResponse(success=True, data=await service.update(id, data, context.org_id, context.user_id))

@router.delete("/{id}", status_code=204)
async def delete_{resource}(id: UUID, context=Depends(get_tenant_context), service=Depends(get_{resource}_service)):
    await service.delete(id, context.org_id)
```

## Service Template

```python
class {Resource}Service:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, id: UUID, org_id: UUID):
        result = await self.db.scalar(select({Resource}).where({Resource}.id == id, {Resource}.org_id == org_id))
        if not result:
            raise NotFoundException(f"{Resource} {id} not found")
        return result

    async def list(self, org_id: UUID, page: int, page_size: int):
        query = select({Resource}).where({Resource}.org_id == org_id)
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        items = await self.db.scalars(query.offset((page - 1) * page_size).limit(page_size))
        return list(items.all()), total or 0

    async def create(self, data, org_id: UUID, user_id: UUID | None = None):
        instance = {Resource}(org_id=org_id, created_by=user_id, **data.model_dump())
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: UUID, data, org_id: UUID, user_id=None):
        instance = await self.get(id, org_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(instance, k, v)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: UUID, org_id: UUID):
        instance = await self.get(id, org_id)
        await self.db.delete(instance)
        await self.db.commit()
```

## Checklist

1. [ ] Every endpoint uses `Depends(get_tenant_context)`
2. [ ] Service queries always filter by `org_id`
3. [ ] Response has `model_config = {"from_attributes": True}`
4. [ ] Router registered in `main.py`
5. [ ] Kafka event emitted for create/update/delete
6. [ ] Tests: CRUD + missing X-Org-Id + cross-tenant isolation
7. [ ] Alembic migration: `alembic revision --autogenerate -m "Add {resource}"`
