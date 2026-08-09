import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai import AICallLog

@dataclass
class LLMResult:
    data: dict
    input_tokens: int | None = None
    output_tokens: int | None = None

class LLMProvider(ABC):
    enabled: bool
    model: str
    @abstractmethod
    def generate_json(self, system_prompt: str, user_payload: dict, timeout: float) -> LLMResult: ...

class DisabledProvider(LLMProvider):
    enabled=False; model=""
    def generate_json(self, system_prompt: str, user_payload: dict, timeout: float) -> LLMResult:
        raise RuntimeError("ai_disabled")

class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key=api_key; self.base_url=base_url.rstrip('/'); self.model=model; self.enabled=bool(api_key and model)
    def generate_json(self, system_prompt: str, user_payload: dict, timeout: float) -> LLMResult:
        response=httpx.post(f"{self.base_url}/chat/completions",headers={"Authorization":f"Bearer {self.api_key}"},json={"model":self.model,"response_format":{"type":"json_object"},"messages":[{"role":"system","content":system_prompt},{"role":"user","content":json.dumps(user_payload,ensure_ascii=False,default=str)}]},timeout=timeout)
        response.raise_for_status(); body=response.json(); content=body["choices"][0]["message"]["content"]; usage=body.get("usage",{})
        return LLMResult(json.loads(content),usage.get("prompt_tokens"),usage.get("completion_tokens"))

class AIService:
    def __init__(self, provider: LLMProvider | None = None):
        settings=get_settings(); self.settings=settings
        self.provider=provider or (OpenAICompatibleProvider(settings.ai_api_key,settings.ai_base_url,settings.ai_model) if settings.ai_api_key else DisabledProvider())
    @property
    def enabled(self): return self.provider.enabled
    @property
    def model(self): return self.provider.model
    def structured(self, db: Session, user_id: str, feature: str, system_prompt: str, payload: dict, schema: Any) -> tuple[dict|None,str|None]:
        started=time.perf_counter(); error=None; result=None; attempts=max(1,self.settings.ai_max_retries+1)
        prompt_chars = len(json.dumps(payload, ensure_ascii=False, default=str))
        if not self.enabled: attempts=1
        for attempt in range(attempts):
            try:
                raw=self.provider.generate_json(system_prompt,payload,self.settings.ai_timeout_seconds)
                result=TypeAdapter(schema).validate_python(raw.data).model_dump(mode="json")
                db.add(AICallLog(user_id=user_id,feature=feature,model=self.model,status="success",prompt_chars=prompt_chars,input_tokens=raw.input_tokens,output_tokens=raw.output_tokens,latency_ms=int((time.perf_counter()-started)*1000)));db.commit();return result,None
            except (ValidationError, json.JSONDecodeError, TypeError, KeyError):
                error = "invalid_json"
                break
            except Exception as exc:
                error="disabled" if str(exc)=="ai_disabled" else "provider_error"
                if attempt+1<attempts: continue
        db.add(AICallLog(user_id=user_id,feature=feature,model=self.model,status="failed",prompt_chars=prompt_chars,latency_ms=int((time.perf_counter()-started)*1000),error_code=error));db.commit();return None,error

def get_ai_service() -> AIService:
    return AIService()
