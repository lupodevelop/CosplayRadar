const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

console.log('Available models:');
console.log(Object.keys(prisma));

// Test specific models
console.log('\nTest models:');
console.log('Has googleTrendData:', 'googleTrendData' in prisma);
console.log('Has trendSummary:', 'trendSummary' in prisma);
console.log('Has character:', 'character' in prisma);
