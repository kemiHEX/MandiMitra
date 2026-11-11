from datetime import date
from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.schemas import FarmerState,CostAssumptions,Observation
from app.decision import compare

TODAY=date(2026,11,9)
def result(f,o,c): return compare(f,[o],c,TODAY)
def test_brief_calculation(farmer,observation,costs):
    r=result(farmer,observation,costs); row=r['options'][0]
    assert r['trader']['net']=='36000.00'
    assert (row['gross'],row['total_costs'],row['net'],row['incremental'],row['break_even'])==('48000.00','7000.00','41000.00','5000.00','1075.00')
    assert r['best_option_id']=='khanna'
@pytest.mark.parametrize('quantity',[0,-1,'NaN','Infinity',1000001])
def test_invalid_quantity(quantity):
    with pytest.raises(ValidationError): FarmerState(quantity=quantity)
@pytest.mark.parametrize('price',[-1,'NaN','Infinity',100000001])
def test_invalid_price(price):
    with pytest.raises(ValidationError): FarmerState(trader_offer=price)
def test_zero_offer_allowed(farmer,observation,costs):
    farmer.trader_offer=0
    assert result(farmer,observation,costs)['trader']['net']=='0.00'
def test_missing_quantity(farmer,observation,costs):
    farmer.quantity=None
    with pytest.raises(ValueError,match='quantity'): result(farmer,observation,costs)
def test_mixed_supported_units(farmer,observation,costs):
    farmer.quantity=4000;farmer.quantity_unit='kg';farmer.trader_offer=9;farmer.offer_unit='kg'
    assert result(farmer,observation,costs)['options'][0]['net']=='41000.00'
def test_tonnes(farmer,observation,costs):
    farmer.quantity=4;farmer.quantity_unit='tonne';farmer.trader_offer=9000;farmer.offer_unit='tonne'
    assert result(farmer,observation,costs)['trader']['net']=='36000.00'
def test_unknown_unit():
    with pytest.raises(ValidationError): FarmerState(quantity=4,quantity_unit='bag')
def test_loss_and_percentage_break_even(farmer,observation,costs):
    costs['khanna']=CostAssumptions(transport=4000,loading=500,loss_percent=10,market_fee_percent=2,confirmed=True)
    row=result(farmer,observation,costs)['options'][0]
    assert Decimal(row['saleable_quantity'])==36
    assert row['net']=='37836.00'
    assert row['break_even']=='1147.96'
    # Inverse formula agrees to the displayed paise (within saleable quantity × 0.005).
    assert abs(Decimal(row['break_even'])*36*Decimal('.98')-4500-36000)<Decimal('.18')
def test_trader_cost_and_loss(farmer,observation,costs):
    farmer.trader_costs=500;farmer.trader_loss_percent=10
    assert result(farmer,observation,costs)['trader']['net']=='31900.00'
def test_different_costs(farmer,observation,costs):
    costs['khanna'].transport=9000
    assert result(farmer,observation,costs)['options'][0]['incremental']=='1500.00'
def test_equal_returns(farmer,observation,costs):
    costs['khanna'].transport=10500
    r=result(farmer,observation,costs)
    assert r['options'][0]['incremental']=='0.00' and r['best_option_id'] is None
def test_negative_net(farmer,observation,costs):
    costs['khanna'].transport=50000
    assert result(farmer,observation,costs)['options'][0]['net']=='-3500.00'
def test_unconfirmed_costs(farmer,observation,costs):
    costs['khanna'].confirmed=False
    assert result(farmer,observation,costs)['options'][0]['status']=='costs_needed'
def test_unconfirmed_trader(farmer,observation,costs):
    farmer.baseline_confirmed=False
    assert result(farmer,observation,costs)['best_option_id'] is None
def test_stale_not_best(farmer,observation,costs):
    observation.observation_date=date(2026,11,5)
    r=result(farmer,observation,costs)
    assert r['options'][0]['age_days']==4 and r['best_option_id'] is None
def test_old_excluded(farmer,observation,costs):
    observation.observation_date=date(2026,10,25)
    assert result(farmer,observation,costs)['options']==[]
def test_no_source(observation):
    with pytest.raises(ValidationError): Observation.model_validate({**observation.model_dump(),'source':''})
def test_invalid_price_range(observation):
    with pytest.raises(ValidationError): Observation.model_validate({**observation.model_dump(),'modal_price':1400})
def test_unknown_price_unit(observation):
    with pytest.raises(ValidationError): Observation.model_validate({**observation.model_dump(),'price_unit':'INR/kg'})
def test_duplicate_latest_only(farmer,observation,costs):
    old=observation.model_copy(update={'modal_price':Decimal(1100),'observation_date':date(2026,11,7)})
    r=compare(farmer,[old,observation],costs,TODAY)
    assert len(r['options'])==1 and r['options'][0]['net']=='41000.00'
def test_variety_excluded(farmer,observation,costs):
    farmer.crop_variety='Hybrid'
    assert result(farmer,observation,costs)['options']==[]
def test_grade_excluded(farmer,observation,costs):
    farmer.grade='A'
    assert result(farmer,observation,costs)['options']==[]
def test_crop_excluded(farmer,observation,costs):
    farmer.crop='wheat'
    assert result(farmer,observation,costs)['options']==[]
@pytest.mark.parametrize('field,value',[('transport',-1),('loss_percent',100),('market_fee_percent',31),('other','NaN')])
def test_invalid_costs(field,value):
    with pytest.raises(ValidationError): CostAssumptions(**{field:value})
def test_no_data(farmer): assert compare(farmer,[],{},TODAY)['best_option_id'] is None
def test_sensitivity(farmer,observation,costs):
    values=result(farmer,observation,costs)['options'][0]['sensitivity']
    assert [v['net'] for v in values]==['36200.00','41000.00','45800.00']

def test_minimum_price_never_rounds_below_break_even(farmer,observation,costs):
    farmer.quantity=3
    costs['khanna']=CostAssumptions(other=1,confirmed=True)
    row=result(farmer,observation,costs)['options'][0]
    assert row['break_even']=='900.34'
    assert Decimal(row['break_even'])*3-1 >= Decimal('2700')

def test_other_crop_does_not_hide_valid_observation(farmer,observation,costs):
    other=observation.model_copy(update={'commodity':'wheat','observation_date':TODAY})
    r=compare(farmer,[other,observation],costs,TODAY)
    assert len(r['options'])==1 and r['options'][0]['net']=='41000.00'
