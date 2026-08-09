from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.ai import AIAnalysis, AIFollowup, AIUserSetting
from app.models.goal import StudyGoal
from app.models.growth import GoalRequirement, Material, WeeklyPlan, WeeklyPlanItem
from app.models.task import Evidence, Task, TaskEvaluation
from app.models.user import User
from app.schemas.ai import AISettingInput, DiagnosisAIResult, FeedbackAIResult, FollowupAIResult, FollowupAnswerInput, FollowupEvaluationResult, GoalAIInput, GoalAIResult, MaterialAIResult, PlanAIResult
from app.schemas.growth import MaterialConfirmation
from app.services.ai_service import AIService, get_ai_service
from app.services.growth_diagnosis_service import GrowthDiagnosisService
from app.services.material_service import MaterialService

router=APIRouter(tags=["ai"])
def dump(row): return {c.name:getattr(row,c.name) for c in row.__table__.columns}
def draft(db,user_id,kind,source_type,source_id,result):
    row=AIAnalysis(user_id=user_id,analysis_type=kind,source_type=source_type,source_id=source_id,result_json=result,status="pending_confirmation");db.add(row);db.commit();db.refresh(row);return row
def owned_analysis(db,user_id,analysis_id):
    row=db.execute(select(AIAnalysis).where(AIAnalysis.id==analysis_id,AIAnalysis.user_id==user_id)).scalar_one_or_none()
    if not row: raise HTTPException(404,"AI 分析不存在")
    return row

@router.get("/ai/settings")
def settings(user:User=Depends(get_current_user),db:Session=Depends(get_db),ai:AIService=Depends(get_ai_service)):
    row=db.get(AIUserSetting,user.id);return {"enabled":ai.enabled,"model":ai.model or None,"allow_material_analysis":row.allow_material_analysis if row else False,"description":"AI 仅增强解释和草稿，规则服务仍是状态与数值的唯一依据。","privacy_notice":"只有明确授权后，材料提取文本才会发送给配置的模型服务。"}
@router.patch("/ai/settings")
def update_settings(payload:AISettingInput,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    row=db.get(AIUserSetting,user.id) or AIUserSetting(user_id=user.id);db.add(row);row.allow_material_analysis=payload.allow_material_analysis;db.commit();return dump(row)

def run(db,user,ai,feature,prompt,payload,schema,source_type,source_id):
    result,error=ai.structured(db,user.id,feature,prompt,payload,schema)
    if result is None:return {"status":"unavailable","error_code":error,"analysis":None}
    return {"status":"pending_confirmation","error_code":None,"analysis":dump(draft(db,user.id,feature,source_type,source_id,result))}

@router.post("/materials/{material_id}/ai-parse")
def material_ai(material_id:str,user:User=Depends(get_current_user),db:Session=Depends(get_db),ai:AIService=Depends(get_ai_service)):
    material=db.execute(select(Material).where(Material.id==material_id,Material.user_id==user.id)).scalar_one_or_none()
    if not material:raise HTTPException(404,"材料不存在")
    consent=db.get(AIUserSetting,user.id)
    if not consent or not consent.allow_material_analysis:raise HTTPException(403,"尚未授权发送材料内容给 AI")
    text=(material.parsed_content or {}).get("extracted_text")
    if not text:raise HTTPException(409,"当前材料没有可发送的提取文本，图片仍需人工录入")
    return run(db,user,ai,"material_parse","只从用户提供文本提取结构化事实。不得补充文本外信息。输出 JSON。",{"material_type":material.material_type,"text":text[:50000]},MaterialAIResult,"material",material.id)
@router.post("/ai/analyses/{analysis_id}/confirm-material")
def confirm_material_ai(analysis_id:str,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    row=owned_analysis(db,user.id,analysis_id)
    if row.analysis_type!="material_parse" or row.status!="pending_confirmation":raise HTTPException(409,"分析不可确认")
    try:payload=MaterialConfirmation.model_validate(row.result_json);evidences=MaterialService().confirm(db,user.id,row.source_id,payload)
    except Exception as exc:raise HTTPException(422,"AI 草稿仍需人工修正后确认") from exc
    row.status="confirmed";row.confirmed_at=datetime.now(timezone.utc);db.commit();return [dump(x) for x in evidences]

@router.post("/goals/{goal_id}/ai-organize")
def goal_ai(goal_id:str,payload:GoalAIInput,user:User=Depends(get_current_user),db:Session=Depends(get_db),ai:AIService=Depends(get_ai_service)):
    goal=db.execute(select(StudyGoal).where(StudyGoal.id==goal_id,StudyGoal.user_id==user.id)).scalar_one_or_none()
    if not goal:raise HTTPException(404,"目标不存在")
    existing=[dump(x) for x in db.execute(select(GoalRequirement).where(GoalRequirement.goal_id==goal_id)).scalars().all()]
    return run(db,user,ai,"goal_organize","仅整理用户提供文本，不搜索、不使用模型记忆补充学校信息。输出 JSON。",{"supplied_text":payload.supplied_text,"source_type":payload.source_type,"existing_requirements":existing},GoalAIResult,payload.source_type,goal_id)
@router.post("/ai/analyses/{analysis_id}/confirm-goal")
def confirm_goal_ai(analysis_id:str,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    row=owned_analysis(db,user.id,analysis_id);goal=db.execute(select(StudyGoal).where(StudyGoal.id==row.source_id,StudyGoal.user_id==user.id)).scalar_one_or_none()
    if not goal or row.analysis_type!="goal_organize" or row.status!="pending_confirmation":raise HTTPException(409,"分析不可确认")
    parsed=GoalAIResult.model_validate(row.result_json);created=[]
    for value in parsed.requirements:
        data=value.model_dump(mode="json");data["verification_status"]="confirmed";data["source_type"]=row.source_type
        item=GoalRequirement(goal_id=goal.id,**data);db.add(item);created.append(item)
    row.status="confirmed";row.confirmed_at=datetime.now(timezone.utc);db.commit();return [dump(x) for x in created]

@router.post("/growth-attributes/{attribute_key}/ai-explain")
def diagnosis_ai(attribute_key:str,user:User=Depends(get_current_user),db:Session=Depends(get_db),ai:AIService=Depends(get_ai_service)):
    rule=next((x for x in GrowthDiagnosisService().diagnose(db,user.id) if x["attribute_key"]==attribute_key),None)
    if not rule:raise HTTPException(404,"能力维度不存在")
    return run(db,user,ai,"diagnosis_explain","只能解释给定规则诊断，不得改变 status、score 或 confidence。输出 JSON。",{"rule_diagnosis":rule},DiagnosisAIResult,"growth_attribute",attribute_key)

@router.post("/weekly-plans/{plan_id}/ai-optimize")
def plan_ai(plan_id:str,user:User=Depends(get_current_user),db:Session=Depends(get_db),ai:AIService=Depends(get_ai_service)):
    plan=db.execute(select(WeeklyPlan).where(WeeklyPlan.id==plan_id,WeeklyPlan.user_id==user.id,WeeklyPlan.status=="draft")).scalar_one_or_none()
    if not plan:raise HTTPException(404,"待确认计划不存在")
    items=[dump(x) for x in db.execute(select(WeeklyPlanItem).where(WeeklyPlanItem.plan_id==plan.id)).scalars().all()]
    response=run(db,user,ai,"plan_optimize","只优化文案、完成标准、证据要求和原因；必须保留每个输入 id，不得增加任务。输出 JSON。",{"items":items},PlanAIResult,"weekly_plan",plan.id)
    analysis=response.get("analysis")
    if analysis:
        output=analysis["result_json"]["items"]
        if {x["id"] for x in output}!={x["id"] for x in items}:
            db.delete(db.get(AIAnalysis,analysis["id"]));db.commit();return {"status":"unavailable","error_code":"constraint_violation","analysis":None}
    return response
@router.post("/ai/analyses/{analysis_id}/confirm-plan")
def confirm_plan_ai(analysis_id:str,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    row=owned_analysis(db,user.id,analysis_id);plan=db.execute(select(WeeklyPlan).where(WeeklyPlan.id==row.source_id,WeeklyPlan.user_id==user.id,WeeklyPlan.status=="draft")).scalar_one_or_none()
    if not plan or row.analysis_type!="plan_optimize" or row.status!="pending_confirmation":raise HTTPException(409,"分析不可确认")
    parsed=PlanAIResult.model_validate(row.result_json)
    for value in parsed.items:
        item=db.execute(select(WeeklyPlanItem).where(WeeklyPlanItem.id==value.id,WeeklyPlanItem.plan_id==plan.id)).scalar_one_or_none()
        if not item:raise HTTPException(422,"AI 任务不满足原计划约束")
        item.title=value.title;item.completion_standard=value.completion_standard;item.evidence_requirements=value.evidence_requirements;item.generation_reason=value.generation_reason
    row.status="confirmed";row.confirmed_at=datetime.now(timezone.utc);db.commit();return {"status":"confirmed"}

@router.post("/tasks/{task_id}/ai-feedback")
def feedback_ai(task_id:str,user:User=Depends(get_current_user),db:Session=Depends(get_db),ai:AIService=Depends(get_ai_service)):
    task=db.execute(select(Task).where(Task.id==task_id,Task.user_id==user.id)).scalar_one_or_none();evaluation=db.execute(select(TaskEvaluation).where(TaskEvaluation.task_id==task_id,TaskEvaluation.user_id==user.id).order_by(TaskEvaluation.created_at.desc())).scalars().first()
    if not task or not evaluation:raise HTTPException(404,"任务或规则评测不存在")
    evidences=[{"type":x.evidence_type,"description":x.description,"file_name":x.file_name} for x in db.execute(select(Evidence).where(Evidence.task_id==task_id,Evidence.user_id==user.id)).scalars().all()]
    response=run(db,user,ai,"task_feedback","规则评测状态不可更改。只输出摘要、优点、未完成部分、建议和可选追问。输出 JSON。",{"task":{"title":task.title,"completion_standard":task.completion_standard},"rule_evaluation":{"status":evaluation.status,"reason":evaluation.reason},"evidences":evidences},FeedbackAIResult,"task_evaluation",evaluation.id)
    if response.get("analysis"):response["rule_status"]=evaluation.status
    return response

@router.post("/tasks/{task_id}/ai-followups")
def followups(task_id:str,user:User=Depends(get_current_user),db:Session=Depends(get_db),ai:AIService=Depends(get_ai_service)):
    task=db.execute(select(Task).where(Task.id==task_id,Task.user_id==user.id)).scalar_one_or_none()
    if not task:raise HTTPException(404,"任务不存在")
    result,error=ai.structured(db,user.id,"followups","基于任务内容生成 1-5 个理解验证问题，不判断真实性。输出 JSON。",{"title":task.title,"completion_standard":task.completion_standard},FollowupAIResult)
    if not result:return {"status":"unavailable","error_code":error,"items":[]}
    items=[]
    for question in result["questions"]:
        row=db.execute(select(AIFollowup).where(AIFollowup.task_id==task.id,AIFollowup.question==question)).scalar_one_or_none() or AIFollowup(user_id=user.id,task_id=task.id,question=question);db.add(row);items.append(row)
    db.commit();return {"status":"ready","items":[dump(x) for x in items]}
@router.post("/ai-followups/{followup_id}/answer")
def answer_followup(followup_id:str,payload:FollowupAnswerInput,user:User=Depends(get_current_user),db:Session=Depends(get_db),ai:AIService=Depends(get_ai_service)):
    row=db.execute(select(AIFollowup).where(AIFollowup.id==followup_id,AIFollowup.user_id==user.id)).scalar_one_or_none()
    if not row:raise HTTPException(404,"追问不存在")
    result,error=ai.structured(db,user.id,"followup_evaluation","只评价回答覆盖度并给出保守反馈，不改变能力值。输出 JSON。",{"question":row.question,"answer":payload.answer},FollowupEvaluationResult)
    row.answer=payload.answer;row.evaluation=result["evaluation"] if result else None;db.commit();return {"status":"evaluated" if result else "saved_without_ai","error_code":error,**dump(row)}
