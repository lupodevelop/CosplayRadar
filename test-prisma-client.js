const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

console.log('=== PRISMA CLIENT TEST ===\n');

const models = Object.keys(prisma).filter(k => 
  !k.startsWith('_') && 
  !k.startsWith('$') && 
  k !== 'parent'
).sort();

console.log('Available models (' + models.length + '):', models);

// Test dei nuovi modelli
const expectedModels = [
  'animeRelease',
  'animeReleaseTrend', 
  'character',
  'characterTrendAnalysis',
  'characterWeeklyTrend',
  'trendData',
  'user'
];

console.log('\n=== MODEL VERIFICATION ===');
expectedModels.forEach(model => {
  const exists = model in prisma;
  console.log(`${exists ? '✅' : '❌'} ${model}: ${exists ? 'FOUND' : 'MISSING'}`);
});

// Test specifici
console.log('\n=== SPECIFIC TESTS ===');
console.log('Has googleTrendData:', 'googleTrendData' in prisma);
console.log('Has trendSummary:', 'trendSummary' in prisma);

// Test enums
try {
  const { TrendRegion, KeywordType, QueryVolume, AnimeStatus, MediaFormat, AnimeSeason, MediaSource, TrendCategory, BreakoutLevel } = require('@prisma/client');
  console.log('\n=== ENUMS VERIFICATION ===');
  const enums = {
    TrendRegion, KeywordType, QueryVolume, AnimeStatus, MediaFormat, 
    AnimeSeason, MediaSource, TrendCategory, BreakoutLevel
  };
  
  Object.entries(enums).forEach(([name, enumObj]) => {
    console.log(`✅ ${name}:`, enumObj ? Object.keys(enumObj).join(', ') : 'undefined');
  });
} catch (error) {
  console.log('\n❌ Enums not available:', error.message);
}

async function testBasicOperations() {
  try {
    console.log('\n=== DATABASE CONNECTION TEST ===');
    
    // Test connessione
    const userCount = await prisma.user.count();
    console.log('✅ Database connected. Users count:', userCount);
    
    // Test dei nuovi modelli
    if ('animeRelease' in prisma) {
      const releaseCount = await prisma.animeRelease.count();
      console.log('✅ AnimeRelease count:', releaseCount);
    }
    
    if ('characterTrendAnalysis' in prisma) {
      const trendCount = await prisma.characterTrendAnalysis.count();
      console.log('✅ CharacterTrendAnalysis count:', trendCount);
    }
    
  } catch (error) {
    console.log('❌ Database test failed:', error.message);
  } finally {
    await prisma.$disconnect();
  }
}

testBasicOperations();
