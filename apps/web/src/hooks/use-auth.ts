"use client";

import { useSession } from "next-auth/react";
import { UserRole } from "@cosplayradar/db";

export function useAuth() {
  const { data: session, status } = useSession();

  const isLoading = status === "loading";
  const isAuthenticated = !!session?.user;
  const user = session?.user;

  const isAdmin = user?.role === UserRole.ADMIN;
  const isCreator = user?.role === UserRole.CREATOR;

  return {
    session,
    user,
    isLoading,
    isAuthenticated,
    isAdmin,
    isCreator,
    status,
  };
}
