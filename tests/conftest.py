import pytest
from datetime import date,datetime,timezone
from app.schemas import FarmerState,Observation,CostAssumptions

@pytest.fixture
def farmer(): return FarmerState(crop='tomato',quantity=40,trader_offer=900,location='Ludhiana',crop_variety='Local',baseline_confirmed=True)
@pytest.fixture
def observation(): return Observation(id='khanna',source='Test illustrative fixture',source_url='local:test',kind='demonstration_fixture',commodity='tomato',variety='Local',market='Khanna',district='Ludhiana',state='Punjab',observation_date=date(2026,11,8),min_price=1000,modal_price=1200,max_price=1300,retrieved_at=datetime(2026,11,9,tzinfo=timezone.utc))
@pytest.fixture
def costs(): return {'khanna':CostAssumptions(transport=5500,loading=1000,other=500,confirmed=True)}
