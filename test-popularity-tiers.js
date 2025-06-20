const testPopularityCalculation = () => {
  // Simulazione dei dati reali dal nostro DB
  const characters = [
    { name: 'Lelouch Lamperouge', favorites: 174158 },
    { name: 'Luffy Monkey D.', favorites: 144366 },
    { name: 'L Lawliet', favorites: 128641 },
    { name: 'Naruto Uzumaki', favorites: 85780 },
    { name: 'Character medio', favorites: 27658 },
    { name: 'Character emergente', favorites: 1000 },
    { name: 'Character nuovo', favorites: 100 }
  ];

  const scores = characters.map(c => c.favorites).sort((a, b) => b - a);
  const total = scores.length;

  // Calcolo percentili dinamici (come nel nostro servizio)
  const tiers = {
    legendary: scores[Math.floor(total * 0.03)] || 100,  // Top 3%
    elite: scores[Math.floor(total * 0.10)] || 80,       // Top 10%
    popular: scores[Math.floor(total * 0.25)] || 60,     // Top 25%
    known: scores[Math.floor(total * 0.50)] || 40,       // Top 50%
    emerging: scores[Math.floor(total * 0.75)] || 20,    // Top 75%
  };

  console.log('🎯 Tiers dinamici calcolati:');
  console.log(`- LEGENDARY: ${tiers.legendary}+ (top 3%)`);
  console.log(`- ELITE: ${tiers.elite}+ (top 10%)`);
  console.log(`- POPULAR: ${tiers.popular}+ (top 25%)`);
  console.log(`- KNOWN: ${tiers.known}+ (top 50%)`);
  console.log(`- EMERGING: ${tiers.emerging}+ (top 75%)`);

  console.log('\n🏷️ Badge assegnati:');
  characters.forEach(char => {
    let level = 'FRESH';
    if (char.favorites >= tiers.legendary) level = 'LEGENDARY';
    else if (char.favorites >= tiers.elite) level = 'ELITE';
    else if (char.favorites >= tiers.popular) level = 'POPULAR';
    else if (char.favorites >= tiers.known) level = 'KNOWN';
    else if (char.favorites >= tiers.emerging) level = 'EMERGING';

    console.log(`${char.name}: ${char.favorites} → ${level}`);
  });

  // Calcolo distribuzione
  const counts = { LEGENDARY: 0, ELITE: 0, POPULAR: 0, KNOWN: 0, EMERGING: 0, FRESH: 0 };
  characters.forEach(char => {
    if (char.favorites >= tiers.legendary) counts.LEGENDARY++;
    else if (char.favorites >= tiers.elite) counts.ELITE++;
    else if (char.favorites >= tiers.popular) counts.POPULAR++;
    else if (char.favorites >= tiers.known) counts.KNOWN++;
    else if (char.favorites >= tiers.emerging) counts.EMERGING++;
    else counts.FRESH++;
  });

  console.log('\n📊 Distribuzione badge:');
  Object.entries(counts).forEach(([level, count]) => {
    const percentage = ((count / characters.length) * 100).toFixed(1);
    console.log(`${level}: ${count} (${percentage}%)`);
  });
};

testPopularityCalculation();
