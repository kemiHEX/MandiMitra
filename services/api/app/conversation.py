"""Structured memory, conservative offline extraction, and grounded localized replies."""
import re
from decimal import Decimal
from .schemas import Extraction, FarmerState

CROP_TERMS = {'tomato': ['tomato', 'tomatoes', 'tamatar', 'ਟਮਾਟਰ', 'टमाटर'], 'wheat': ['wheat', 'kanak', 'gehun', 'ਕਣਕ', 'गेहूं', 'गेहूँ'], 'potato': ['potato', 'potatoes', 'aloo', 'ਆਲੂ', 'आलू']}
NUMBER_WORDS = {'forty':40,'chali':40,'chaali':40,'chalis':40,'challis':40,'ਚਾਲੀ':40,'चालीस':40,'fourteen':14,'chaudah':14,'chauda':14,'ਚੌਦਾਂ':14,'चौदह':14,'twenty':20,'ਵੀਹ':20,'बीस':20,'bees':20,'veeh':20,'ten':10,'das':10,'ਦਸ':10,'दस':10,'five':5,'panj':5,'paanch':5,'ਪੰਜ':5,'पाँच':5,'do':2,'two':2,'ਦੋ':2,'दो':2,'one':1,'ik':1,'ek':1,'ਇੱਕ':1,'एक':1,'fifty':50,'pachaas':50,'ਪੰਜਾਹ':50,'पचास':50,'nine hundred':900,'nau sau':900,'ਨੌ ਸੌ':900,'नौ सौ':900,'twelve hundred':1200,'barah sau':1200,'ਬਾਰਾਂ ਸੌ':1200,'बारह सौ':1200,'four thousand':4000,'char hazar':4000,'ਚਾਰ ਹਜ਼ਾਰ':4000,'चार हजार':4000}
PLACES = {'ludhiana': 'Ludhiana', 'ਲੁਧਿਆਣਾ':'Ludhiana','लुधियाना':'Ludhiana','khanna':'Khanna','ਖੰਨਾ':'Khanna','खन्ना':'Khanna','jagraon':'Jagraon','ਜਗਰਾਉਂ':'Jagraon','जगराओं':'Jagraon','patiala':'Patiala','ਪਟਿਆਲਾ':'Patiala','पटियाला':'Patiala','amritsar':'Amritsar','ਅੰਮ੍ਰਿਤਸਰ':'Amritsar','अमृतसर':'Amritsar','jalandhar':'Jalandhar','ਜਲੰਧਰ':'Jalandhar','जालंधर':'Jalandhar'}
UNIT = r'(quintals?|qtl|ਕੁਇੰਟਲ|ਕੁਇੰਟਲਾਂ|क्विंटल|kg|kilos?|kilograms?|ਕਿਲੋ|किलो|tonnes?|tons?)'

def normalized(text):
    text = text.lower().translate(str.maketrans('੦੧੨੩੪੫੬੭੮੯०१२३४५६७८९','01234567890123456789'))
    text = re.sub(r'(?<=\d),(?=\d)', '', text)
    for word, value in sorted(NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
        text = re.sub(r'(?<!\w)' + re.escape(word) + r'(?!\w)', str(value), text)
    return text

def unit_name(unit):
    if unit in ['kg','kilo','kilos','kilogram','kilograms','ਕਿਲੋ','किलो']: return 'kg'
    if unit.startswith('ton'): return 'tonne'
    return 'quintal'

def offline_extract(text: str, state: FarmerState) -> Extraction:
    """Limited demonstrator, never represented as a live LLM or general NLP."""
    result = {key: None for key in Extraction.model_fields}
    result['intent'] = 'compare'
    t = normalized(text)
    if any(term in t for term in ['disease','pesticide','weather','forecast','ਬਿਮਾਰੀ','बीमारी','ਮੌਸਮ','मौसम','bitcoin','rice','paddy','onion','ਝੋਨਾ','प्याज']):
        result['intent'] = 'unsupported'
        return Extraction(**result)
    if any(term in t for term in ['how calculated','break even','break-even','ਕਿਵੇਂ','कैसे निकाला']):
        result['intent'] = 'explain'
        return Extraction(**result)
    for canonical, terms in CROP_TERMS.items():
        matches = [term for term in terms if term in t]
        if matches:
            result['crop'], result['crop_term'] = canonical, matches[0]
            break
    transport = any(term in t for term in ['transport','ਢੋਆਈ','ढुलाई','ਭਾੜਾ','भाड़ा'])
    for term, place in PLACES.items():
        if term in t: result['market_name' if transport else 'location'] = place
    if transport:
        nums = re.findall(r'(?<![\w.])-?\d+(?:\.\d+)?', t)
        if nums:
            result['transport'] = float(nums[-1])
            result['intent'] = 'correct'
        return Extraction(**result)
    matches = list(re.finditer(r'(?<![\w.])(-?\d+(?:\.\d+)?)\s*' + UNIT, t))
    for match in matches:
        # "900 per quintal" is never a quantity; matching requires adjacency.
        result['quantity'] = float(match[1])
        result['quantity_unit'] = unit_name(match[2])
    money_matches = list(re.finditer(r'(?<![\w.])(-?\d+(?:\.\d+)?)\s*(?:rupees|rupaye|rupay|ਰੁਪਏ|रुपये|ਰੁਪੈ)', t))
    if money_matches: result['trader_offer'] = float(money_matches[-1][1])
    offered = re.search(r'(?:offer|price|ਭਾਅ|भाव)\s*(?:is|of|=|:)?\s*₹?\s*(-?\d+(?:\.\d+)?)', t)
    currency = re.search(r'₹\s*(-?\d+(?:\.\d+)?)', t)
    if offered or currency: result['trader_offer'] = float((offered or currency)[1])
    price_unit = re.search(r'(?:per|prati|ਪ੍ਰਤੀ|प्रति|/)\s*' + UNIT, t)
    if result['trader_offer'] is not None:
        if price_unit: result['offer_unit'] = unit_name(price_unit[1])
        elif state.quantity is not None and state.trader_offer is None: result['offer_unit'] = 'quintal'
        else: result['clarification'] = 'Please confirm whether the offer is per kilogram or per quintal.'
    if re.fullmatch(r'\s*\d+(?:\.\d+)?\s*', t):
        if state.quantity is not None and state.trader_offer is None:
            result['trader_offer'], result['offer_unit'] = float(t), 'quintal'
        else: result['clarification'] = 'Please include a unit, for example 14 quintal or 900 rupees per quintal.'
    if re.search(r'nahi|not|ਨਹੀਂ|नहीं', t): result['intent'] = 'correct'
    if re.search(r'bori|bags?|ਬੋਰੀ|बोरी', t):
        result['quantity'] = None
        result['clarification'] = 'What is the total weight in kilograms or quintals? Bag sizes vary.'
    if not any(v is not None for k,v in result.items() if k != 'intent'):
        result['intent'] = 'unknown'
    return Extraction(**result)

def apply_extraction(state: FarmerState, extracted: Extraction):
    if extracted.quantity is not None and extracted.quantity_unit is None and not (extracted.intent=='correct' and state.quantity is not None):
        raise ValueError('Confirm the quantity unit before using this amount')
    if extracted.trader_offer is not None and extracted.offer_unit is None and not (extracted.intent=='correct' and state.trader_offer is not None):
        raise ValueError('Confirm the price unit before using this offer')
    data = state.model_dump()
    for field in ('crop','crop_term','crop_variety','quantity','quantity_unit','trader_offer','offer_unit','location'):
        value = getattr(extracted, field)
        if value is not None:
            data[field] = Decimal(str(value)) if field in ('quantity','trader_offer') else value
    if extracted.crop and extracted.crop != state.crop:
        data['crop_variety'] = extracted.crop_variety
        data['grade'] = None
    return FarmerState.model_validate(data)

TEXT = {
 'welcome': {'en':'Tell me about your crop. What are you selling, and how much do you have?', 'pa':'ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਤੁਸੀਂ ਕਿਹੜੀ ਫ਼ਸਲ ਵੇਚਣੀ ਹੈ ਅਤੇ ਕਿੰਨੀ ਮਾਤਰਾ ਹੈ?', 'hi':'नमस्ते! आप कौन सी फ़सल बेचना चाहते हैं और कितनी मात्रा है?'},
 'crop': {'en':'Which crop are you selling? We currently support tomato, wheat and potato mappings.', 'pa':'ਤੁਸੀਂ ਕਿਹੜੀ ਫ਼ਸਲ ਵੇਚਣੀ ਹੈ—ਟਮਾਟਰ, ਕਣਕ ਜਾਂ ਆਲੂ?', 'hi':'आप कौन सी फ़सल बेच रहे हैं—टमाटर, गेहूँ या आलू?'},
 'quantity': {'en':'How much crop do you have? Please include kilograms or quintals.', 'pa':'ਤੁਹਾਡੇ ਕੋਲ ਕਿੰਨੀ ਫ਼ਸਲ ਹੈ? ਕਿਲੋ ਜਾਂ ਕੁਇੰਟਲ ਵਿੱਚ ਦੱਸੋ।', 'hi':'आपके पास कितनी फ़सल है? किलो या क्विंटल में बताइए।'},
 'trader_offer': {'en':'What is your local trader offering in rupees per quintal?', 'pa':'ਵਪਾਰੀ ਤੁਹਾਨੂੰ ਕਿੰਨੇ ਰੁਪਏ ਪ੍ਰਤੀ ਕੁਇੰਟਲ ਦੇ ਰਿਹਾ ਹੈ?', 'hi':'व्यापारी कितने रुपये प्रति क्विंटल दे रहा है?'},
 'location': {'en':'Which Punjab town or district are you near?', 'pa':'ਤੁਸੀਂ ਪੰਜਾਬ ਦੇ ਕਿਹੜੇ ਸ਼ਹਿਰ ਜਾਂ ਜ਼ਿਲ੍ਹੇ ਦੇ ਨੇੜੇ ਹੋ?', 'hi':'आप पंजाब के किस शहर या ज़िले के पास हैं?'},
 'costs': {'en':'Your crop details are ready. Enter and confirm costs for each market and the local trader before comparing net proceeds.', 'pa':'ਫ਼ਸਲ ਦੀ ਜਾਣਕਾਰੀ ਮਿਲ ਗਈ। ਤੁਲਨਾ ਲਈ ਹਰ ਮੰਡੀ ਅਤੇ ਸਥਾਨਕ ਵਪਾਰੀ ਦੇ ਖਰਚੇ ਭਰ ਕੇ ਪੁਸ਼ਟੀ ਕਰੋ।', 'hi':'फ़सल की जानकारी मिल गई। तुलना से पहले हर मंडी और स्थानीय व्यापारी के खर्च भरकर पुष्टि करें।'},
 'unsupported': {'en':'I help with crop-selling decisions, not disease diagnosis, weather or price forecasts. For crop health, contact your local agricultural extension expert.', 'pa':'ਮੈਂ ਫ਼ਸਲ ਵੇਚਣ ਦੇ ਫ਼ੈਸਲੇ ਵਿੱਚ ਮਦਦ ਕਰਦਾ ਹਾਂ। ਬਿਮਾਰੀ, ਮੌਸਮ ਜਾਂ ਭਵਿੱਖ ਦੇ ਭਾਅ ਲਈ ਸਲਾਹ ਨਹੀਂ ਦੇ ਸਕਦਾ। ਫ਼ਸਲ ਦੀ ਸਿਹਤ ਲਈ ਖੇਤੀ ਮਾਹਰ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।', 'hi':'मैं फ़सल बेचने के फैसले में मदद करता हूँ। बीमारी, मौसम या भविष्य के भाव नहीं बता सकता। फ़सल की सेहत के लिए कृषि विशेषज्ञ से संपर्क करें।'},
 'unknown': {'en':'Please tell me your crop, quantity with units, trader offer and Punjab location. You can also edit the details below.', 'pa':'ਫ਼ਸਲ, ਮਾਤਰਾ, ਵਪਾਰੀ ਦਾ ਭਾਅ ਅਤੇ ਪੰਜਾਬ ਵਿੱਚ ਆਪਣੀ ਥਾਂ ਦੱਸੋ। ਹੇਠਾਂ ਜਾਣਕਾਰੀ ਵੀ ਭਰ ਸਕਦੇ ਹੋ।', 'hi':'फ़सल, मात्रा, व्यापारी का भाव और पंजाब में अपनी जगह बताइए। नीचे जानकारी भी भर सकते हैं।'},
 'confirm': {'en':'Reference prices are not buyer offers. Confirm the achievable price, variety, grade and all costs before travelling.', 'pa':'ਮੰਡੀ ਦਾ ਦਰਜ ਭਾਅ ਖਰੀਦ ਦੀ ਪੱਕੀ ਪੇਸ਼ਕਸ਼ ਨਹੀਂ ਹੈ। ਜਾਣ ਤੋਂ ਪਹਿਲਾਂ ਮਿਲਣ ਵਾਲੇ ਭਾਅ, ਕਿਸਮ, ਗ੍ਰੇਡ ਅਤੇ ਖਰਚਿਆਂ ਦੀ ਪੁਸ਼ਟੀ ਕਰੋ।', 'hi':'मंडी का दर्ज भाव खरीद की पक्की पेशकश नहीं है। जाने से पहले मिलने वाला भाव, किस्म, ग्रेड और खर्चों की पुष्टि करें।'},
 'demo': {'en':'Illustrative example only. ', 'pa':'ਇਹ ਸਿਰਫ਼ ਸਮਝਾਉਣ ਲਈ ਬਣਾਇਆ ਉਦਾਹਰਨ ਹੈ। ', 'hi':'यह केवल समझाने के लिए बनाया उदाहरण है। '},
 'no_data': {'en':'No comparable observations are available for this crop and location. I cannot recommend a market without data.', 'pa':'ਇਸ ਫ਼ਸਲ ਅਤੇ ਥਾਂ ਲਈ ਤੁਲਨਾ ਯੋਗ ਭਾਅ ਨਹੀਂ ਮਿਲੇ। ਅੰਕੜਿਆਂ ਬਿਨਾਂ ਮੰਡੀ ਦੀ ਸਿਫ਼ਾਰਸ਼ ਨਹੀਂ ਕਰ ਸਕਦਾ।', 'hi':'इस फ़सल और जगह के लिए तुलना योग्य भाव नहीं मिले। आंकड़ों के बिना मंडी की सलाह नहीं दे सकता।'},
 'explain': {'en':'Net proceeds = saleable quantity × reference price − transport − handling − other costs − percentage fees. Break-even solves for the price that leaves the same proceeds as your trader. Production costs are not included.', 'pa':'ਬਚੀ ਰਕਮ = ਵਿਕਣ ਯੋਗ ਮਾਤਰਾ × ਹਵਾਲਾ ਭਾਅ − ਢੋਆਈ − ਲਦਾਈ − ਹੋਰ ਖਰਚੇ − ਫ਼ੀਸ। ਬਰਾਬਰੀ ਦਾ ਭਾਅ ਉਹ ਹੈ ਜਿਸ ਨਾਲ ਵਪਾਰੀ ਜਿੰਨੀ ਰਕਮ ਬਚੇ। ਖੇਤੀ ਦੀ ਲਾਗਤ ਸ਼ਾਮਲ ਨਹੀਂ ਹੈ।', 'hi':'बची रकम = बिकने योग्य मात्रा × संदर्भ भाव − ढुलाई − लदाई − अन्य खर्च − फीस। बराबरी का भाव वह है जिस पर व्यापारी जितनी रकम बचे। खेती की लागत शामिल नहीं है।'}
}

def say(key, language): return TEXT[key].get(language, TEXT[key]['en'])

def reply(state: FarmerState, comparison: dict | None, demo: bool):
    lang = state.preferred_language
    if state.missing: return say(state.missing[0],lang)
    if not comparison or not comparison['options']: return say('no_data',lang)
    if not state.baseline_confirmed or any(o['status']=='costs_needed' for o in comparison['options']): return say('costs',lang)
    best = next((r for r in comparison['options'] if r['observation']['id']==comparison['best_option_id']), None)
    prefix = say('demo',lang) if demo else ''
    if not best:
        message = {'en':'No fresh, confirmed-cost alternative currently shows a higher estimate than your local trader. Check the breakdown and any stale references.', 'pa':'ਤਾਜ਼ਾ ਭਾਅ ਅਤੇ ਪੁਸ਼ਟੀ ਕੀਤੇ ਖਰਚਿਆਂ ਨਾਲ ਕੋਈ ਹੋਰ ਵਿਕਲਪ ਵਪਾਰੀ ਤੋਂ ਵੱਧ ਰਕਮ ਨਹੀਂ ਦਿਖਾ ਰਿਹਾ। ਵੇਰਵਾ ਅਤੇ ਪੁਰਾਣੇ ਭਾਅ ਵੇਖੋ।', 'hi':'ताज़ा भाव और पुष्टि किए खर्चों के आधार पर कोई विकल्प व्यापारी से ज़्यादा रकम नहीं दिखा रहा। विवरण और पुराने भाव देखें।'}[lang]
        return prefix + message + ' ' + say('confirm',lang)
    market, net, difference, minimum = best['observation']['market'], best['net'], best['incremental'], best['break_even']
    message = {
      'en':f'At the reference price, {market} could leave you with ₹{net}, or ₹{difference} more than your trader. You need at least ₹{minimum}/q to match the trader after these estimated costs.',
      'pa':f'ਹਵਾਲਾ ਭਾਅ ਉੱਤੇ {market} ਵਿੱਚ ਅੰਦਾਜ਼ਨ ₹{net} ਬਚ ਸਕਦੇ ਹਨ, ਵਪਾਰੀ ਨਾਲੋਂ ₹{difference} ਵੱਧ। ਇਨ੍ਹਾਂ ਅੰਦਾਜ਼ਨ ਖਰਚਿਆਂ ਤੋਂ ਬਾਅਦ ਵਪਾਰੀ ਦੇ ਬਰਾਬਰ ਰਕਮ ਲਈ ਘੱਟੋ-ਘੱਟ ₹{minimum}/q ਮਿਲਣੇ ਚਾਹੀਦੇ ਹਨ।',
      'hi':f'संदर्भ भाव पर {market} में अनुमानित ₹{net} बच सकते हैं, व्यापारी से ₹{difference} अधिक। इन अनुमानित खर्चों के बाद व्यापारी के बराबर रकम के लिए कम से कम ₹{minimum}/q मिलना चाहिए।'
    }[lang]
    return prefix + message + ' ' + say('confirm',lang)
