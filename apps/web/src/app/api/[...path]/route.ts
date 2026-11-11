import { NextRequest, NextResponse } from 'next/server';
import { createHmac, randomBytes, timingSafeEqual } from 'node:crypto';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
const production = process.env.DEPLOYMENT_ENV === 'production';
const secret = process.env.APP_SESSION_SECRET || 'local-demo-session-secret';
const accessCode = process.env.APP_ACCESS_CODE || '';
const cookieOptions = { httpOnly: true, secure: production, sameSite: 'strict' as const, path: '/', maxAge: 30 * 86400 };
const sign = (value: string) => createHmac('sha256', secret).update(value).digest('hex');
const equal = (a: string, b: string) => { const aa = Buffer.from(a), bb = Buffer.from(b); return aa.length === bb.length && timingSafeEqual(aa, bb); };
const loginAttempts = new Map<string, { count: number; expires: number }>();

function validCookie(value: string | undefined) {
  if (!value) return null;
  const [id, expires, sig] = value.split('.');
  if (!/^[a-f0-9]{64}$/.test(id) || Number(expires) < Date.now() || !equal(sign(`${id}.${expires}`), sig || '')) return null;
  return id;
}
async function route(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  const endpoint = path.join('/');
  if (production && (secret.length < 32 || !accessCode || !process.env.API_INTERNAL_TOKEN || !process.env.APP_PUBLIC_URL)) return NextResponse.json({ error: 'Deployment security settings are incomplete.' }, { status: 503 });
  // POST/PATCH/DELETE require an exact same-origin request. Browsers supply Origin.
  const allowedOrigins = process.env.APP_PUBLIC_URL ? [new URL(process.env.APP_PUBLIC_URL).origin] : ['http://localhost:3000','http://127.0.0.1:3000'];
  if (!['GET', 'HEAD'].includes(req.method) && !allowedOrigins.includes(req.headers.get('origin') || '')) return NextResponse.json({ error: 'Invalid request origin.' }, { status: 403 });
  const maxBytes = endpoint === 'stt' ? 2_100_000 : 32_000;
  if (Number(req.headers.get('content-length') || 0) > maxBytes) return NextResponse.json({ error: 'Request is too large.' }, { status: 413 });
  let body: ArrayBuffer | undefined;
  if (!['GET','HEAD'].includes(req.method)) {
    // Read with a running limit, including chunked uploads.
    const reader = req.body?.getReader(); const chunks: Uint8Array[] = []; let size = 0;
    if (reader) { while (true) { const { done, value } = await reader.read(); if (done) break; size += value.byteLength; if (size > maxBytes) { await reader.cancel(); return NextResponse.json({ error: 'Request is too large.' }, { status: 413 }); } chunks.push(value); } }
    const all = new Uint8Array(size); let offset = 0; for (const chunk of chunks) { all.set(chunk,offset); offset += chunk.length; } body = all.buffer;
  }
  if (endpoint === 'auth' && req.method === 'POST') {
    // Global login throttle intentionally does not trust spoofable forwarded-IP headers.
    const now = Date.now(); const previous = loginAttempts.get('global');
    const bucket = previous && previous.expires > now ? previous : { count: 0, expires: now + 60_000 };
    bucket.count++; loginAttempts.set('global',bucket);
    if (bucket.count > 15) return NextResponse.json({ error: 'Please wait a minute before trying again.' }, { status: 429 });
    let supplied: string; try { supplied = JSON.parse(Buffer.from(body || new ArrayBuffer(0)).toString()).code; } catch { return NextResponse.json({ error: 'Enter the access code.' }, { status: 400 }); }
    if (typeof supplied !== 'string' || !equal(supplied,accessCode)) return NextResponse.json({ error: 'That access code is not correct.' }, { status: 401 });
    const value = `${randomBytes(32).toString('hex')}.${Date.now()+30*86400_000}`;
    const result = NextResponse.json({ ok: true }); result.cookies.set('mm_auth',`${value}.${sign(value)}`,cookieOptions); return result;
  }
  if (accessCode && !validCookie(req.cookies.get('mm_auth')?.value)) return NextResponse.json({ error: 'Enter your access code to use MandiMitra.', auth_required: true }, { status: 401 });
  const allowed: Record<string,string[]> = { session:['GET','DELETE'], demo:['POST'], inputs:['PATCH'], chat:['POST'], costs:['PATCH'], compare:['POST'], decisions:['GET','POST'], stt:['POST'], tts:['POST'], health:['GET'] };
  const permitted = allowed[endpoint] || (/^decisions\/[a-f0-9]{32}$/.test(endpoint) ? ['DELETE'] : []);
  if (!permitted.includes(req.method)) return NextResponse.json({ error: 'Not found.' }, { status: 404 });
  const existing = validCookie(req.cookies.get('mm_session')?.value);
  const sid = existing || randomBytes(32).toString('hex');
  try {
    const upstream = await fetch(`${process.env.API_BASE_URL || 'http://127.0.0.1:8000'}/${endpoint}${endpoint==='session' && req.nextUrl.searchParams.get('everything')==='true' ? '?everything=true' : ''}`, {
      method: req.method, headers: { Authorization: `Bearer ${process.env.API_INTERNAL_TOKEN || 'local-demo-only'}`, 'X-Session-ID': sid, ...(req.headers.get('content-type') ? { 'Content-Type': req.headers.get('content-type')! } : {}) }, body, cache: 'no-store', signal: AbortSignal.timeout(110_000), redirect: 'error',
    });
    const response = new NextResponse(upstream.body,{status:upstream.status,headers:{'Content-Type':upstream.headers.get('content-type') || 'application/json','Cache-Control':'no-store',...(upstream.headers.get('x-request-id') ? {'X-Request-ID':upstream.headers.get('x-request-id')!} : {})}});
    if (!existing) { const value=`${sid}.${Date.now()+30*86400_000}`; response.cookies.set('mm_session',`${value}.${sign(value)}`,cookieOptions); }
    return response;
  } catch { return NextResponse.json({ error: 'The MandiMitra server is unavailable. Check your connection and make sure the backend is running.' }, { status: 503 }); }
}
export { route as GET, route as POST, route as PATCH, route as DELETE };
