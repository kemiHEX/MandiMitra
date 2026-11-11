"""Authoritative money arithmetic. No provider or LLM dependencies."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING
from .schemas import FarmerState, Observation, CostAssumptions

D = Decimal
UNITS = {'quintal': D(1), 'kg': D('0.01'), 'tonne': D(10)}

def money(value: Decimal) -> str:
    return str(value.quantize(D('.01'), rounding=ROUND_HALF_UP))

def compare(state: FarmerState, observations: list[Observation], costs: dict[str, CostAssumptions], today: date | None = None) -> dict:
    if state.missing:
        raise ValueError('Missing: ' + ', '.join(state.missing))
    today = today or date.today()
    quantity = state.quantity * UNITS[state.quantity_unit]
    trader_price = state.trader_offer / UNITS[state.offer_unit]
    trader_saleable = quantity * (1 - state.trader_loss_percent / 100)
    trader_gross = trader_saleable * trader_price
    baseline = trader_gross - state.trader_costs
    rows, excluded, seen = [], [], set()
    # Newest observation wins within the same market/variety/grade; do not duplicate options.
    for o in sorted(observations, key=lambda x: (x.observation_date, x.retrieved_at), reverse=True):
        key = (o.commodity, o.state.lower(), o.district.lower(), o.market.lower(), o.variety.lower(), (o.grade or '').casefold())
        if key in seen:
            continue
        seen.add(key)
        reason = None
        if o.commodity != state.crop: reason = 'Different commodity'
        elif state.crop_variety and o.variety.casefold() != state.crop_variety.casefold(): reason = 'Different variety'
        elif state.grade and (o.grade or '').casefold() != state.grade.casefold(): reason = 'Different grade'
        elif (today - o.observation_date).days > 7: reason = 'Observation is over 7 days old; excluded from comparison'
        elif o.observation_date > today: reason = 'Future observation'
        if reason:
            excluded.append({'market': o.market, 'reason': reason})
            continue
        c = costs.get(o.id)
        flags = ['Illustrative prices, not actual market data'] if o.kind == 'demonstration_fixture' else []
        age = (today - o.observation_date).days
        if age > 2: flags.append(f'Stale reference: {age} days old')
        if not state.crop_variety: flags.append('Your variety has not been matched')
        if not state.grade: flags.append('Your grade has not been matched')
        if not state.baseline_confirmed: flags.append('Confirm local trader costs and saleable quantity')
        base = {'observation': o.model_dump(mode='json'), 'age_days': age, 'flags': flags, 'costs': c.model_dump(mode='json') if c else None}
        if not c or not c.confirmed:
            rows.append({**base, 'status': 'costs_needed', 'flags': flags + ['Enter and confirm selling costs']})
            continue
        saleable = quantity * (1 - c.loss_percent / 100)
        gross = saleable * o.modal_price
        fixed = c.transport + c.loading + c.other
        fees = gross * c.market_fee_percent / 100
        total = fixed + fees
        net = gross - total
        # A percentage commission also varies at break-even; solve algebraically.
        break_even = max(D(0), (baseline + fixed) / (saleable * (1 - c.market_fee_percent / 100)))
        # The displayed minimum must meet the baseline, never round below it.
        break_even_display = str(break_even.quantize(D('.01'), rounding=ROUND_CEILING))
        sensitivity = []
        for factor in (D('.9'), D(1), D('1.1')):
            hypothetical = o.modal_price * factor
            hyp_net = saleable * hypothetical * (1 - c.market_fee_percent / 100) - fixed
            sensitivity.append({'price': money(hypothetical), 'net': money(hyp_net), 'label': 'Hypothetical price, not a forecast'})
        rows.append({**base, 'status': 'calculated', 'saleable_quantity': str(saleable), 'gross': money(gross), 'market_fees': money(fees), 'total_costs': money(total), 'net': money(net), 'incremental': money(net-baseline), 'break_even': break_even_display, 'sensitivity': sensitivity})
    rows.sort(key=lambda r: D(r.get('net', '-999999999999')), reverse=True)
    eligible = [r for r in rows if r['status'] == 'calculated' and r['age_days'] <= 2]
    best = eligible[0]['observation']['id'] if eligible and D(eligible[0]['incremental']) > 0 and state.baseline_confirmed else None
    return {'quantity_quintal': str(quantity), 'trader': {'price': money(trader_price), 'saleable_quantity': str(trader_saleable), 'gross': money(trader_gross), 'costs': money(state.trader_costs), 'net': money(baseline), 'confirmed': state.baseline_confirmed, 'kind': 'farmer_reported_offer'}, 'options': rows, 'excluded': excluded, 'best_option_id': best, 'calculated_at': today.isoformat(), 'disclaimer': 'Conditional estimates using reference prices. Confirm the achievable price, variety, grade and costs before travelling. These are net proceeds, not profit.'}
