import asyncio
import json
import httpx
from app.config import Settings
from app.integrations.response_plan import choose,emphasis
from app.decision import compare
from datetime import date
def test_groq_response_plan_contract():
    def handler(request):
        body=json.loads(request.content)
        assert body['response_format']['json_schema']['strict'] is True
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"focus":"break_even"}'}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await choose(client,Settings(groq_key='test'),'Minimum price?',{})
    assert asyncio.run(run())=='break_even'
def test_grounded_response_values(farmer,observation,costs):
    result=compare(farmer,[observation],costs,date(2026,11,9))
    assert '₹1075.00' in emphasis('break_even',result,'pa')
    assert '₹7000.00' in emphasis('cost_breakdown',result,'hi')
