import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";
import { UserRole } from "@cosplayradar/db";

export default withAuth(
  function middleware(req) {
    const token = req.nextauth.token;
    const { pathname } = req.nextUrl;

    // Temporaneamente disabilitiamo la protezione per debug
    console.log('Middleware - pathname:', pathname);
    console.log('Middleware - token:', token ? 'present' : 'absent');
    
    // DEBUG: Permettiamo l'accesso alla dashboard senza autenticazione per ora
    if (pathname.startsWith("/dashboard")) {
      console.log('Dashboard access - token check disabled for debug');
      // if (!token) {
      //   return NextResponse.redirect(new URL("/auth/signin", req.url));
      // }
    }

    // API routes protection
    if (pathname.startsWith("/api/protected")) {
      if (!token) {
        return NextResponse.json(
          { error: "Authentication required" },
          { status: 401 }
        );
      }
    }

    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token, req }) => {
        const { pathname } = req.nextUrl;
        
        // Public routes that don't require authentication
        const publicRoutes = [
          "/",
          "/auth/signin",
          "/auth/signup",
          "/about",
          "/features",
          "/pricing",
        ];

        // Allow public routes
        if (publicRoutes.some(route => pathname.startsWith(route))) {
          return true;
        }

        // API auth routes are always accessible
        if (pathname.startsWith("/api/auth")) {
          return true;
        }

        // For protected routes, require authentication
        return !!token;
      },
    },
  }
);

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/admin/:path*",
    "/api/protected/:path*",
    "/profile/:path*",
  ],
};
