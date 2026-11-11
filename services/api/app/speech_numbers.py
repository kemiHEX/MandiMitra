"""Deterministic Indian-number pronunciation for financial replies."""
import re

HI = 'शून्य एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस बीस इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस छत्तीस सैंतीस अड़तीस उनतालीस चालीस इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस उनचास पचास इक्यावन बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ इकसठ बासठ तिरसठ चौंसठ पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर उनासी अस्सी इक्यासी बयासी तिरासी चौरासी पचासी छियासी सत्तासी अट्ठासी नवासी नब्बे इक्यानवे बानवे तिरानवे चौरानवे पंचानवे छियानवे सत्तानवे अट्ठानवे निन्यानवे'.split()
PA = 'ਸਿਫ਼ਰ ਇੱਕ ਦੋ ਤਿੰਨ ਚਾਰ ਪੰਜ ਛੇ ਸੱਤ ਅੱਠ ਨੌਂ ਦਸ ਗਿਆਰਾਂ ਬਾਰਾਂ ਤੇਰਾਂ ਚੌਦਾਂ ਪੰਦਰਾਂ ਸੋਲਾਂ ਸਤਾਰਾਂ ਅਠਾਰਾਂ ਉੱਨੀ ਵੀਹ ਇੱਕੀ ਬਾਈ ਤੇਈ ਚੌਵੀ ਪੱਚੀ ਛੱਬੀ ਸਤਾਈ ਅਠਾਈ ਉਨੱਤੀ ਤੀਹ ਇਕੱਤੀ ਬੱਤੀ ਤੇਤੀ ਚੌਂਤੀ ਪੈਂਤੀ ਛੱਤੀ ਸੈਂਤੀ ਅਠੱਤੀ ਉਨਤਾਲੀ ਚਾਲੀ ਇਕਤਾਲੀ ਬਤਾਲੀ ਤਰਤਾਲੀ ਚੁਤਾਲੀ ਪੰਤਾਲੀ ਛਿਆਲੀ ਸੰਤਾਲੀ ਅਠਤਾਲੀ ਉਨੰਜਾ ਪੰਜਾਹ ਇਕਵੰਜਾ ਬਵੰਜਾ ਤਰਵੰਜਾ ਚੁਰੰਜਾ ਪਚਵੰਜਾ ਛਪੰਜਾ ਸਤਵੰਜਾ ਅਠਵੰਜਾ ਉਨਾਹਠ ਸੱਠ ਇਕਾਹਠ ਬਾਹਠ ਤਰੇਂਹਠ ਚੌਂਹਠ ਪੈਂਹਠ ਛਿਆਹਠ ਸਤਾਹਠ ਅਠਾਹਠ ਉਨੱਤਰ ਸੱਤਰ ਇਕੱਤਰ ਬਹੱਤਰ ਤਿਹੱਤਰ ਚੁਹੱਤਰ ਪੰਝੱਤਰ ਛਿਅੱਤਰ ਸਤੱਤਰ ਅਠੱਤਰ ਉਨਾਸੀ ਅੱਸੀ ਇਕਿਆਸੀ ਬਿਆਸੀ ਤਿਰਾਸੀ ਚੁਰਾਸੀ ਪਚਾਸੀ ਛਿਆਸੀ ਸਤਾਸੀ ਅਠਾਸੀ ਉਨਾਨਵੇਂ ਨੱਬੇ ਇਕਾਨਵੇਂ ਬਾਨਵੇਂ ਤਿਰਾਨਵੇਂ ਚੁਰਾਨਵੇਂ ਪਚਾਨਵੇਂ ਛਿਆਨਵੇਂ ਸਤਾਨਵੇਂ ਅਠਾਨਵੇਂ ਨੜਿਨਵੇਂ'.split()
EN = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS = ['', '', 'twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety']

def words(n: int, language: str):
    if n < 0: return {'en':'minus','hi':'ऋण','pa':'ਘਟਾਓ'}[language]+' '+words(-n,language)
    if n < 100:
        if language=='hi': return HI[n]
        if language=='pa': return PA[n]
        return EN[n] if n<20 else TENS[n//10]+(' '+EN[n%10] if n%10 else '')
    scales=[(10000000,{'en':'crore','hi':'करोड़','pa':'ਕਰੋੜ'}),(100000,{'en':'lakh','hi':'लाख','pa':'ਲੱਖ'}),(1000,{'en':'thousand','hi':'हज़ार','pa':'ਹਜ਼ਾਰ'}),(100,{'en':'hundred','hi':'सौ','pa':'ਸੌ'})]
    for scale,names in scales:
        if n>=scale:
            return words(n//scale,language)+' '+names[language]+(' '+words(n%scale,language) if n%scale else '')

def normalize(text: str, language: str):
    currency={'en':'rupees','hi':'रुपये','pa':'ਰੁਪਏ'}[language]
    paise={'en':'paise','hi':'पैसे','pa':'ਪੈਸੇ'}[language]
    conjunction={'en':'and','hi':'और','pa':'ਅਤੇ'}[language]
    def amount(match):
        parts=match[1].replace(',','').split('.')
        major=int(parts[0]); minor=int((parts[1]+'00')[:2]) if len(parts)>1 else 0
        return words(major,language)+' '+currency+(f' {conjunction} '+words(minor,language)+' '+paise if minor else '')
    text=re.sub(r'₹(-?\d[\d,]*(?:\.\d+)?)',amount,text)
    return text.replace('/q',{'en':' per quintal','hi':' प्रति क्विंटल','pa':' ਪ੍ਰਤੀ ਕੁਇੰਟਲ'}[language])
