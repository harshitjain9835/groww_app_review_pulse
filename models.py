from pydantic import BaseModel
from typing import Optional, List

class DeliveryRecord(BaseModel):
    channel: str
    external_id: str
    url: Optional[str] = None
    idempotency_key: Optional[str] = None

class RunRecord(BaseModel):
    run_id: str
    product: str
    iso_week: str
    status: str
    review_count: int
    window_weeks: int
    started_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    deliveries: List[DeliveryRecord] = []