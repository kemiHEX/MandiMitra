import asyncio
import httpx

class ProviderError(Exception):
    def __init__(self, message: str, status: int = 503):
        self.message, self.status = message, status
        super().__init__(message)

async def request(client: httpx.AsyncClient, method: str, url: str, **kwargs):
    """Retry GET failures and rejected 429s; never blindly repeat billable POST timeouts."""
    for attempt in range(3):
        try:
            response = await client.request(method, url, **kwargs)
        except httpx.RequestError:
            if method == 'GET' and attempt < 2:
                await asyncio.sleep(.3 * 2**attempt)
                continue
            raise ProviderError('The service did not respond. Please try again or use the text form.') from None
        if response.status_code == 429 or (method == 'GET' and response.status_code >= 500):
            if attempt < 2:
                await asyncio.sleep(.5 * 2**attempt)
                continue
        if response.status_code >= 400:
            if response.status_code in (401, 402, 403):
                raise ProviderError('Provider access is unavailable. Check the server credentials, scopes and balance.')
            raise ProviderError('The provider could not complete this request. Please try again later.')
        return response

def json_body(response: httpx.Response):
    try:
        body = response.json()
        if not isinstance(body, dict): raise ValueError()
        return body
    except (ValueError, TypeError):
        raise ProviderError('The provider returned an unreadable response.') from None
