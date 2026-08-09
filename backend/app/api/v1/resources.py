from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_admin_user, get_current_user
from app.db.session import get_db
from app.models.resource import ResourceAlternativeLink, ResourceAttributeLink, ResourceFavorite, ResourceGoalTypeLink, ResourceInteraction, ResourceProduct, ResourceTaskTag, UserOwnedResource
from app.models.task import Task
from app.models.user import User
from app.schemas.resource import AIRecommendationResult, InteractionInput, OwnedResourceInput, ResourceInput, ResourceUpdate
from app.services.ai_service import AIService, get_ai_service
from app.services.resource_recommendation_service import ResourceRecommendationService

router = APIRouter(tags=["resources"])


def columns(row) -> dict:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def product_response(db: Session, row: ResourceProduct) -> dict:
    return {**columns(row),
        "related_attributes": list(db.execute(select(ResourceAttributeLink.attribute_key).where(ResourceAttributeLink.resource_id == row.id)).scalars()),
        "related_task_tags": list(db.execute(select(ResourceTaskTag.tag).where(ResourceTaskTag.resource_id == row.id)).scalars()),
        "applicable_goal_types": list(db.execute(select(ResourceGoalTypeLink.goal_type).where(ResourceGoalTypeLink.resource_id == row.id)).scalars()),
        "free_alternative_ids": list(db.execute(select(ResourceAlternativeLink.alternative_id).where(ResourceAlternativeLink.resource_id == row.id)).scalars())}


def validate_activation(row: ResourceProduct) -> None:
    if row.status == "active" and row.product_type == "digital_material" and row.copyright_status not in {"verified", "provider_owned", "licensed", "public"}:
        raise HTTPException(422, "数字资料版权状态未确认，不能上架")
    if row.status == "active" and row.external_url is None:
        raise HTTPException(422, "上架资源必须提供原始外部链接")


def replace_links(db: Session, resource_id: str, payload: dict) -> None:
    mapping = [("related_attributes", ResourceAttributeLink, "attribute_key"), ("related_task_tags", ResourceTaskTag, "tag"), ("applicable_goal_types", ResourceGoalTypeLink, "goal_type")]
    for key, model, field in mapping:
        if key not in payload: continue
        db.execute(delete(model).where(model.resource_id == resource_id))
        for value in dict.fromkeys(payload[key] or []): db.add(model(resource_id=resource_id, **{field: value}))
    if "free_alternative_ids" in payload:
        db.execute(delete(ResourceAlternativeLink).where(ResourceAlternativeLink.resource_id == resource_id))
        for alternative_id in dict.fromkeys(payload["free_alternative_ids"] or []):
            alternative = db.get(ResourceProduct, alternative_id)
            if alternative is None or not alternative.is_free: raise HTTPException(422, "免费替代必须引用已存在的免费资源")
            if alternative_id == resource_id: raise HTTPException(422, "资源不能替代自身")
            db.add(ResourceAlternativeLink(resource_id=resource_id, alternative_id=alternative_id))


@router.get("/resources")
def list_resources(search: str | None = None, product_type: str | None = None, free_only: bool | None = None, attribute: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    query = select(ResourceProduct).where(ResourceProduct.status == "active")
    if search: query = query.where(or_(ResourceProduct.name.ilike(f"%{search}%"), ResourceProduct.description.ilike(f"%{search}%")))
    if product_type: query = query.where(ResourceProduct.product_type == product_type)
    if free_only is not None: query = query.where(ResourceProduct.is_free.is_(free_only))
    if attribute: query = query.join(ResourceAttributeLink).where(ResourceAttributeLink.attribute_key == attribute)
    rows = db.execute(query.order_by(ResourceProduct.is_free.desc(), ResourceProduct.created_at.desc())).scalars().all()
    return [product_response(db, row) for row in rows]


@router.get("/resources/{resource_id}")
def get_resource(resource_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    row = db.execute(select(ResourceProduct).where(ResourceProduct.id == resource_id, ResourceProduct.status == "active")).scalar_one_or_none()
    if row is None: raise HTTPException(404, "资源不存在")
    db.add(ResourceInteraction(user_id=user.id, resource_id=row.id, interaction_type="viewed")); db.commit()
    return product_response(db, row)


@router.get("/admin/resources")
def admin_resources(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)) -> list[dict]:
    return [product_response(db, row) for row in db.execute(select(ResourceProduct).order_by(ResourceProduct.created_at.desc())).scalars().all()]


@router.post("/admin/resources", status_code=201)
def create_resource(payload: ResourceInput, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)) -> dict:
    data = payload.model_dump(mode="json", exclude={"related_attributes", "related_task_tags", "applicable_goal_types", "free_alternative_ids"})
    row = ResourceProduct(**data, has_free_alternative=bool(payload.free_alternative_ids)); validate_activation(row)
    db.add(row); db.flush(); replace_links(db, row.id, payload.model_dump(mode="json")); db.commit(); db.refresh(row)
    return product_response(db, row)


@router.patch("/admin/resources/{resource_id}")
def update_resource(resource_id: str, payload: ResourceUpdate, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)) -> dict:
    row = db.get(ResourceProduct, resource_id)
    if row is None: raise HTTPException(404, "资源不存在")
    values = payload.model_dump(mode="json", exclude_unset=True)
    link_keys = {"related_attributes", "related_task_tags", "applicable_goal_types", "free_alternative_ids"}
    for key, value in values.items():
        if key not in link_keys: setattr(row, key, value)
    replace_links(db, row.id, values)
    if "free_alternative_ids" in values: row.has_free_alternative = bool(values["free_alternative_ids"])
    validate_activation(row); db.commit(); db.refresh(row); return product_response(db, row)


@router.get("/resource-recommendations")
def recommendations(task_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    if task_id and db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id)).scalar_one_or_none() is None: raise HTTPException(404, "任务不存在")
    return ResourceRecommendationService().recommend(db, user.id, task_id)


@router.post("/resource-recommendations/ai-explain")
def ai_recommendations(user: User = Depends(get_current_user), db: Session = Depends(get_db), ai: AIService = Depends(get_ai_service)) -> dict:
    rules = ResourceRecommendationService().recommend(db, user.id)
    result, error = ai.structured(db, user.id, "resource_recommendation_explain", "仅改写给定规则推荐理由，不得修改分数、排序、商品事实或承诺效果。输出 resource_id 到理由的 JSON 映射。", {"recommendations": rules}, AIRecommendationResult)
    if result:
        for item in rules: item["recommendation_reason"] = result["reasons"].get(item["resource_id"], item["recommendation_reason"])
    return {"status": "enhanced" if result else "rules_only", "error_code": error, "items": rules}


@router.get("/tasks/{task_id}/resources")
def task_resources(task_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    if db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id)).scalar_one_or_none() is None: raise HTTPException(404, "任务不存在")
    return ResourceRecommendationService().recommend(db, user.id, task_id, 3)


@router.get("/resource-favorites")
def favorites(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(ResourceProduct).join(ResourceFavorite, ResourceFavorite.resource_id == ResourceProduct.id).where(ResourceFavorite.user_id == user.id, ResourceProduct.status == "active")).scalars().all()
    return [product_response(db, row) for row in rows]


@router.put("/resources/{resource_id}/favorite", status_code=204)
def favorite(resource_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    if db.get(ResourceProduct, resource_id) is None: raise HTTPException(404, "资源不存在")
    if db.get(ResourceFavorite, (user.id, resource_id)) is None: db.add(ResourceFavorite(user_id=user.id, resource_id=resource_id))
    db.add(ResourceInteraction(user_id=user.id, resource_id=resource_id, interaction_type="favorited")); db.commit()


@router.delete("/resources/{resource_id}/favorite", status_code=204)
def unfavorite(resource_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    row = db.get(ResourceFavorite, (user.id, resource_id))
    if row: db.delete(row); db.commit()


@router.get("/owned-resources")
def owned_resources(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return [columns(row) for row in db.execute(select(UserOwnedResource).where(UserOwnedResource.user_id == user.id).order_by(UserOwnedResource.created_at.desc())).scalars().all()]


@router.post("/owned-resources", status_code=201)
def create_owned(payload: OwnedResourceInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    if not payload.resource_product_id and not payload.custom_name: raise HTTPException(422, "自定义资源必须填写名称")
    if payload.resource_product_id and db.get(ResourceProduct, payload.resource_product_id) is None: raise HTTPException(404, "资源不存在")
    existing = db.execute(select(UserOwnedResource).where(UserOwnedResource.user_id == user.id, UserOwnedResource.resource_product_id == payload.resource_product_id)).scalar_one_or_none() if payload.resource_product_id else None
    row = existing or UserOwnedResource(user_id=user.id, **payload.model_dump(mode="json")); db.add(row)
    if payload.resource_product_id: db.add(ResourceInteraction(user_id=user.id, resource_id=payload.resource_product_id, interaction_type="marked_owned"))
    db.commit(); db.refresh(row); return columns(row)


@router.delete("/owned-resources/{owned_id}", status_code=204)
def delete_owned(owned_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    row = db.execute(select(UserOwnedResource).where(UserOwnedResource.id == owned_id, UserOwnedResource.user_id == user.id)).scalar_one_or_none()
    if row is None: raise HTTPException(404, "已有资源不存在")
    db.delete(row); db.commit()


@router.post("/resources/{resource_id}/interactions", status_code=201)
def interact(resource_id: str, payload: InteractionInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    resource = db.execute(select(ResourceProduct).where(ResourceProduct.id == resource_id, ResourceProduct.status == "active")).scalar_one_or_none()
    if resource is None: raise HTTPException(404, "资源不存在")
    task = None
    if payload.task_id:
        task = db.execute(select(Task).where(Task.id == payload.task_id, Task.user_id == user.id)).scalar_one_or_none()
        if task is None: raise HTTPException(404, "任务不存在")
    row = ResourceInteraction(user_id=user.id, resource_id=resource_id, interaction_type=payload.interaction_type, task_id=payload.task_id, task_completed_at_interaction=(task.status == "done") if task else None)
    db.add(row); db.commit(); db.refresh(row)
    response = columns(row)
    if payload.interaction_type == "external_clicked": response["external_url"] = resource.external_url
    return response
