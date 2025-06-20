/**
 * Test configuration for NextAuth setup
 * This file demonstrates the complete authentication flow
 */

import { NextAuthOptions } from "next-auth";
import { authOptions } from "@/lib/auth";

describe("NextAuth Configuration", () => {
  test("should have correct providers configured", () => {
    expect(authOptions.providers).toBeDefined();
    expect(authOptions.providers.length).toBeGreaterThan(0);
  });

  test("should use JWT strategy", () => {
    expect(authOptions.session?.strategy).toBe("jwt");
  });

  test("should have custom sign-in page", () => {
    expect(authOptions.pages?.signIn).toBe("/auth/signin");
  });
});

// Mock data for testing
export const mockUser = {
  id: "test-user-id",
  name: "Test User",
  email: "test@example.com",
  role: "CREATOR" as const,
  username: "testuser",
};

export const mockSession = {
  user: mockUser,
  expires: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
};
