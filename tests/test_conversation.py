import json
from pathlib import Path
import pytest
from app.schemas import FarmerState
from app.conversation import offline_extract,apply_extraction,reply,say

CASES=json.loads((Path(__file__).resolve().parents[1]/'data/samples/evaluation.json').read_text(encoding='utf-8'))
@pytest.mark.parametrize('case',CASES,ids=[c['text'][:38] for c in CASES])
def test_multilingual_demo_evaluation(case):
    parsed=offline_extract(case['text'],FarmerState(**case.get('state',{})))
    for key,value in case['expected'].items(): assert getattr(parsed,key)==value
    if case.get('clarification'): assert parsed.clarification
def test_followup_preserves_state(farmer):
    parsed=offline_extract('Chali nahi, chaudah quintal.',farmer)
    updated=apply_extraction(farmer,parsed)
    assert updated.quantity==14 and updated.trader_offer==900 and updated.crop=='tomato'
def test_negative_correction_rejected(farmer):
    with pytest.raises(ValueError): apply_extraction(farmer,offline_extract('-1 quintal',farmer))
def test_missing_price_prompt():
    f=FarmerState(crop='tomato',quantity=40,preferred_language='pa')
    assert reply(f,None,True)==say('trader_offer','pa')
def test_no_invented_prices(farmer):
    assert '₹' not in reply(farmer,None,False)
