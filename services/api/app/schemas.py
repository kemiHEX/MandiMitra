from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Money = Annotated[Decimal, Field(ge=0, le=100000000, allow_inf_nan=False, max_digits=12, decimal_places=2)]
Quantity = Annotated[Decimal, Field(gt=0, le=1000000, allow_inf_nan=False, max_digits=12, decimal_places=3)]
Language = Literal['en', 'pa', 'hi']

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True, str_strip_whitespace=True)

class FarmerState(StrictModel):
    crop: Literal['tomato', 'wheat', 'potato'] | None = None
    crop_term: str | None = Field(default=None, max_length=80)
    crop_variety: str | None = Field(default=None, max_length=80)
    grade: str | None = Field(default=None, max_length=40)
    quantity: Quantity | None = None
    quantity_unit: Literal['quintal', 'kg', 'tonne'] = 'quintal'
    trader_offer: Money | None = None
    offer_unit: Literal['quintal', 'kg', 'tonne'] = 'quintal'
    location: str | None = Field(default=None, max_length=80)
    preferred_language: Language = 'en'
    trader_costs: Money = Decimal(0)
    trader_loss_percent: Decimal = Field(default=Decimal(0), ge=0, lt=100, allow_inf_nan=False)
    baseline_confirmed: bool = False

    @property
    def missing(self):
        return [k for k in ('crop', 'quantity', 'trader_offer', 'location') if getattr(self, k) is None]

class CostAssumptions(StrictModel):
    transport: Money = Decimal(0)
    loading: Money = Decimal(0)
    market_fee_percent: Decimal = Field(default=Decimal(0), ge=0, le=30, decimal_places=2, allow_inf_nan=False)
    other: Money = Decimal(0)
    loss_percent: Decimal = Field(default=Decimal(0), ge=0, lt=100, decimal_places=2, allow_inf_nan=False)
    confirmed: bool = False

class Observation(StrictModel):
    id: str
    source: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    kind: Literal['official_observation', 'demonstration_fixture']
    commodity: Literal['tomato', 'wheat', 'potato']
    variety: str = Field(min_length=1)
    grade: str | None = None
    market: str = Field(min_length=1)
    district: str = Field(min_length=1)
    state: str = Field(min_length=1)
    observation_date: date
    min_price: Money
    max_price: Money
    modal_price: Money
    price_unit: Literal['INR/quintal'] = 'INR/quintal'
    retrieved_at: datetime

    @model_validator(mode='after')
    def coherent(self):
        if not (0 < self.min_price <= self.modal_price <= self.max_price):
            raise ValueError('Require 0 < minimum <= modal <= maximum')
        if self.observation_date > datetime.now(timezone.utc).date():
            raise ValueError('Observation date cannot be in the future')
        if self.retrieved_at.tzinfo is None:
            raise ValueError('Retrieval timestamp must have a timezone')
        if self.kind == 'official_observation' and not self.source_url.startswith('https://'):
            raise ValueError('Official observations require a source URL')
        return self

class ChatRequest(StrictModel):
    text: str = Field(min_length=1, max_length=2000)
    language: Language = 'en'
    transcript_id: str | None = Field(default=None,pattern=r'^[a-f0-9]{32}$')

class CostRequest(StrictModel):
    market_id: str = Field(max_length=200)
    costs: CostAssumptions

class SpeechRequest(StrictModel):
    message_id: str = Field(min_length=1, max_length=50)

class Extraction(StrictModel):
    intent: Literal['compare', 'correct', 'explain', 'unsupported', 'unknown']
    crop: Literal['tomato', 'wheat', 'potato'] | None
    crop_term: str | None
    crop_variety: str | None
    quantity: float | None
    quantity_unit: Literal['quintal', 'kg', 'tonne'] | None
    trader_offer: float | None
    offer_unit: Literal['quintal', 'kg', 'tonne'] | None
    location: str | None
    transport: float | None
    market_name: str | None
    clarification: str | None
