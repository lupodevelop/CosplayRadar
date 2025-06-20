import { config } from 'dotenv';
import { resolve } from 'path';

// Carica le variabili d'ambiente dal root del progetto
config({ path: resolve(__dirname, '../../../.env.local') });
config({ path: resolve(__dirname, '../.env.local') });

export const DATABASE_URL = process.env.DATABASE_URL || "postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev?schema=public";
export const NEXTAUTH_SECRET = process.env.NEXTAUTH_SECRET || "dev-secret-key";
export const NEXTAUTH_URL = process.env.NEXTAUTH_URL || "http://localhost:3000";
