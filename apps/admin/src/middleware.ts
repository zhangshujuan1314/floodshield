import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 公开路径，不需要认证
  const publicPaths = ['/login', '/_next', '/favicon.ico'];
  if (publicPaths.some(p => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Mock 模式下跳过认证检查
  if (process.env.NEXT_PUBLIC_MOCK_MODE === 'true') {
    return NextResponse.next();
  }

  // 检查认证 token
  const token = request.cookies.get('floodshield_admin_token')?.value;
  if (!token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
