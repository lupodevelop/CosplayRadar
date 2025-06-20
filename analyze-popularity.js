// Script per analizzare la distribuzione della popolarità
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function analyzePopularityDistribution() {
  try {
    console.log('📊 Analizzando distribuzione popolarità...');
    
    // Recupera tutti i personaggi con popolarità
    const characters = await prisma.character.findMany({
      select: {
        id: true,
        name: true,
        popularity: true,
        popularityScore: true
      },
      where: {
        popularity: {
          gt: 0
        }
      },
      orderBy: {
        popularity: 'desc'
      }
    });

    console.log(`\n🎭 Totale personaggi: ${characters.length}`);
    
    if (characters.length === 0) {
      console.log('❌ Nessun dato di popolarità trovato');
      return;
    }

    const popularities = characters.map(c => c.popularity);
    const max = Math.max(...popularities);
    const min = Math.min(...popularities);
    const avg = popularities.reduce((a, b) => a + b, 0) / popularities.length;
    
    // Calcola percentili
    const sorted = popularities.sort((a, b) => b - a);
    const p90 = sorted[Math.floor(sorted.length * 0.1)]; // Top 10%
    const p75 = sorted[Math.floor(sorted.length * 0.25)]; // Top 25%
    const p50 = sorted[Math.floor(sorted.length * 0.5)]; // Top 50%
    const p25 = sorted[Math.floor(sorted.length * 0.75)]; // Top 75%
    
    console.log('\n📈 Statistiche popolarità:');
    console.log(`Max: ${max.toLocaleString()}`);
    console.log(`Min: ${min.toLocaleString()}`);
    console.log(`Media: ${Math.round(avg).toLocaleString()}`);
    console.log(`\n🎯 Percentili:`);
    console.log(`Top 10% (LEGENDARY): ${p90.toLocaleString()}+`);
    console.log(`Top 25% (ELITE): ${p75.toLocaleString()}+`);
    console.log(`Top 50% (POPULAR): ${p50.toLocaleString()}+`);
    console.log(`Top 75% (KNOWN): ${p25.toLocaleString()}+`);
    console.log(`Bottom 25% (EMERGING): < ${p25.toLocaleString()}`);
    
    console.log('\n🔝 Top 10 personaggi:');
    characters.slice(0, 10).forEach((char, i) => {
      console.log(`${i + 1}. ${char.name}: ${char.popularity.toLocaleString()}`);
    });

    return {
      max,
      min,
      avg,
      percentiles: { p90, p75, p50, p25 },
      total: characters.length
    };
    
  } catch (error) {
    console.error('❌ Errore:', error);
  } finally {
    await prisma.$disconnect();
  }
}

analyzePopularityDistribution();
