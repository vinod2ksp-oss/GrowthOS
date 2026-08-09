from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goal import StudyGoal
from app.models.profile import UserProfile
from app.models.resource import ResourceAlternativeLink, ResourceAttributeLink, ResourceFavorite, ResourceGoalTypeLink, ResourceInteraction, ResourceProduct, ResourceTaskTag, UserOwnedResource
from app.models.task import Task
from app.services.goal_gap_analysis_service import GoalGapAnalysisService


class ResourceRecommendationService:
    def recommend(self, db: Session, user_id: str, task_id: str | None = None, limit: int = 30) -> list[dict]:
        products = db.execute(select(ResourceProduct).where(ResourceProduct.status == "active")).scalars().all()
        dismissed = set(db.execute(select(ResourceInteraction.resource_id).where(ResourceInteraction.user_id == user_id, ResourceInteraction.interaction_type == "dismissed")).scalars())
        owned = db.execute(select(UserOwnedResource).where(UserOwnedResource.user_id == user_id, UserOwnedResource.status == "owned")).scalars().all()
        favorites = set(db.execute(select(ResourceFavorite.resource_id).where(ResourceFavorite.user_id == user_id)).scalars())
        profile = db.execute(select(UserProfile).where(UserProfile.user_id == user_id)).scalar_one_or_none()
        goal = db.execute(select(StudyGoal).where(StudyGoal.user_id == user_id).order_by(StudyGoal.created_at.desc())).scalars().first()
        gaps = GoalGapAnalysisService().analyze(db, user_id, goal.id) if goal else []
        active_tasks = db.execute(select(Task).where(Task.user_id == user_id, Task.status.in_(["pending", "delayed"]))).scalars().all()
        if task_id:
            active_tasks = [task for task in active_tasks if task.id == task_id]
        results = []
        for product in products:
            if product.id in dismissed:
                continue
            attrs = set(db.execute(select(ResourceAttributeLink.attribute_key).where(ResourceAttributeLink.resource_id == product.id)).scalars())
            tags = set(db.execute(select(ResourceTaskTag.tag).where(ResourceTaskTag.resource_id == product.id)).scalars())
            goal_types = set(db.execute(select(ResourceGoalTypeLink.goal_type).where(ResourceGoalTypeLink.resource_id == product.id)).scalars())
            matching_task = next((task for task in active_tasks if any(tag.lower() in task.title.lower() for tag in tags)), None)
            matching_gap = next((gap for gap in gaps if gap.get("category") in attrs and gap.get("gap_level") in {"minor", "moderate", "major", "unknown"}), None)
            if task_id and matching_task is None:
                continue
            stage_match = bool(profile and profile.learning_stage and profile.learning_stage in (product.applicable_stages or []))
            goal_match = bool(goal and goal.current_stage and goal.current_stage in goal_types)
            score = (50 if matching_task else 0) + (30 if matching_gap else 0) + (10 if stage_match else 0) + (10 if goal_match else 0) + (3 if product.is_free else 0)
            if score < 20:
                continue
            owned_similar = any(row.resource_product_id == product.id or row.resource_type == product.product_type for row in owned)
            budget = profile.resource_budget if profile else None
            budget_fit = product.is_free or budget is None or product.price is None or float(product.price) <= budget
            if owned_similar: score -= 15
            if not budget_fit: score -= 10
            alternatives = list(db.execute(select(ResourceAlternativeLink.alternative_id).join(ResourceProduct, ResourceProduct.id == ResourceAlternativeLink.alternative_id).where(ResourceAlternativeLink.resource_id == product.id, ResourceProduct.status == "active", ResourceProduct.is_free.is_(True))).scalars())
            reasons = []
            if matching_task: reasons.append(f"与当前任务“{matching_task.title}”直接相关")
            if matching_gap: reasons.append(f"与已识别的“{matching_gap['category']}”差距相关")
            if stage_match: reasons.append("适用于用户填写的当前阶段")
            warnings = []
            if owned_similar: warnings.append("你已记录拥有同类资源，请先评估是否需要新增")
            if not budget_fit: warnings.append("超出当前资源预算")
            if product.content_year and product.content_year < datetime.now(timezone.utc).year - 2: warnings.append("内容年份较早，请确认仍然适用")
            results.append({"resource_id": product.id, "name": product.name, "product_type": product.product_type, "price": float(product.price) if product.price is not None else None, "currency": product.currency, "is_free": product.is_free, "relevance_score": max(0, score), "recommendation_reason": "；".join(reasons), "related_attribute": matching_gap["category"] if matching_gap else (next(iter(attrs), None)), "related_gap": matching_gap["title"] if matching_gap else None, "related_task": matching_task.title if matching_task else None, "related_task_id": matching_task.id if matching_task else None, "budget_fit": budget_fit, "already_owned_similar": owned_similar, "free_alternative_ids": alternatives, "sponsored": product.is_sponsored, "sponsorship_label": product.sponsorship_label, "is_required": product.is_required, "applicable_stages": product.applicable_stages, "favorited": product.id in favorites, "warnings": warnings})
        return sorted(results, key=lambda item: (-item["relevance_score"], not item["is_free"], item["name"]))[:limit]
