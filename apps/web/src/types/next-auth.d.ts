import { DefaultSession, DefaultUser } from "next-auth";
import { UserRole } from "@cosplayradar/db";

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      role: UserRole;
      username?: string;
    } & DefaultSession["user"];
  }

  interface User extends DefaultUser {
    role: UserRole;
    username?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    role: UserRole;
    username?: string;
  }
}
