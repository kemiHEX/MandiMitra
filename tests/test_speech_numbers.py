from app.speech_numbers import words,normalize,HI,PA
def test_number_tables(): assert len(HI)==len(PA)==100
def test_punjabi_currency(): assert normalize('₹41000.00','pa')=='ਇਕਤਾਲੀ ਹਜ਼ਾਰ ਰੁਪਏ'
def test_hindi_currency(): assert normalize('₹1,075.50/q','hi')=='एक हज़ार पचहत्तर रुपये और पचास पैसे प्रति क्विंटल'
def test_english_currency(): assert normalize('₹5000','en')=='five thousand rupees'
def test_large_amount(): assert words(124567,'en')=='one lakh twenty four thousand five hundred sixty seven'
