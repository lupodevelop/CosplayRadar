import { PrismaClient } from '@prisma/client';

declare global {
  var __db__: PrismaClient | undefined;
}

let prisma: PrismaClient;

try {
  if (process.env.NODE_ENV === 'production') {
    prisma = new PrismaClient();
  } else {
    if (!global.__db__) {
      global.__db__ = new PrismaClient();
    }
    prisma = global.__db__;
  }
} catch (error) {
  console.error('Failed to initialize Prisma client:', error);
  // Fallback per sviluppo quando il client non è generato
  prisma = {} as PrismaClient;
}

export { prisma };
export { PrismaClient };
export * from '@prisma/client';
export default prisma;
