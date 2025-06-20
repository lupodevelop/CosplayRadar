import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding database...');

  // Seed characters
  const characters = await Promise.all([
    // Anime characters
    prisma.character.upsert({
      where: { id: 'nezuko-kamado' },
      update: {},
      create: {
        id: 'nezuko-kamado',
        name: 'Nezuko Kamado',
        series: 'Demon Slayer',
        category: 'ANIME',
        difficulty: 3,
        popularity: 95.5,
        description: 'Protagonista di Demon Slayer, molto popolare per cosplay',
        tags: ['anime', 'demon slayer', 'pink hair', 'kimono'],
        imageUrl: 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=400&fit=crop'
      }
    }),
    prisma.character.upsert({
      where: { id: 'goku-dbz' },
      update: {},
      create: {
        id: 'goku-dbz',
        name: 'Son Goku',
        series: 'Dragon Ball Z',
        category: 'ANIME',
        difficulty: 2,
        popularity: 88.2,
        description: 'Protagonista iconico di Dragon Ball',
        tags: ['anime', 'dragon ball', 'orange gi', 'saiyan'],
        imageUrl: 'https://images.unsplash.com/photo-1618336753974-aae8e04506aa?w=400&h=400&fit=crop'
      }
    }),
    prisma.character.upsert({
      where: { id: 'sailor-moon' },
      update: {},
      create: {
        id: 'sailor-moon',
        name: 'Sailor Moon',
        series: 'Sailor Moon',
        category: 'ANIME',
        difficulty: 3,
        popularity: 91.8,
        description: 'Iconica magical girl degli anni 90',
        tags: ['anime', 'sailor moon', 'blonde hair', 'magical girl'],
        imageUrl: 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=400&fit=crop'
      }
    }),
    prisma.character.upsert({
      where: { id: 'pikachu' },
      update: {},
      create: {
        id: 'pikachu',
        name: 'Pikachu',
        series: 'Pokémon',
        category: 'ANIME',
        difficulty: 2,
        popularity: 92.3,
        description: 'Il Pokémon più famoso al mondo',
        tags: ['anime', 'pokemon', 'yellow', 'electric'],
        imageUrl: 'https://images.unsplash.com/photo-1605979399824-6d3897b88096?w=400&h=400&fit=crop'
      }
    }),
    
    // Video game characters
    prisma.character.upsert({
      where: { id: 'link-zelda' },
      update: {},
      create: {
        id: 'link-zelda',
        name: 'Link',
        series: 'The Legend of Zelda',
        category: 'VIDEOGAME',
        difficulty: 4,
        popularity: 82.7,
        description: 'Eroe di Hyrule dalla serie Zelda',
        tags: ['videogame', 'zelda', 'green tunic', 'elf'],
        imageUrl: 'https://images.unsplash.com/photo-1511512578047-dfb367046420?w=400&h=400&fit=crop'
      }
    }),
    prisma.character.upsert({
      where: { id: 'lara-croft' },
      update: {},
      create: {
        id: 'lara-croft',
        name: 'Lara Croft',
        series: 'Tomb Raider',
        category: 'VIDEOGAME',
        difficulty: 3,
        popularity: 85.1,
        description: 'Archeologa avventuriera iconica',
        tags: ['videogame', 'tomb raider', 'adventure', 'action'],
        imageUrl: 'https://images.unsplash.com/photo-1544725176-7c40e5a71c5e?w=400&h=400&fit=crop'
      }
    }),
    prisma.character.upsert({
      where: { id: 'mario' },
      update: {},
      create: {
        id: 'mario',
        name: 'Super Mario',
        series: 'Super Mario Bros',
        category: 'VIDEOGAME',
        difficulty: 1,
        popularity: 78.9,
        description: 'L\'idraulico più famoso del mondo',
        tags: ['videogame', 'nintendo', 'plumber', 'red hat'],
        imageUrl: 'https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?w=400&h=400&fit=crop'
      }
    }),

    // Movie characters
    prisma.character.upsert({
      where: { id: 'harley-quinn' },
      update: {},
      create: {
        id: 'harley-quinn',
        name: 'Harley Quinn',
        series: 'DC Comics/Movies',
        category: 'MOVIE',
        difficulty: 3,
        popularity: 89.6,
        description: 'Antieroe caotica del DC Universe',
        tags: ['movie', 'dc comics', 'blonde', 'villain'],
        imageUrl: 'https://images.unsplash.com/photo-1578914498693-15f41e6a8a8a?w=400&h=400&fit=crop'
      }
    }),
    prisma.character.upsert({
      where: { id: 'spider-man' },
      update: {},
      create: {
        id: 'spider-man',
        name: 'Spider-Man',
        series: 'Marvel/Spider-Man Movies',
        category: 'MOVIE',
        difficulty: 4,
        popularity: 94.2,
        description: 'Il vostro amichevole Spider-Man di quartiere',
        tags: ['movie', 'marvel', 'superhero', 'red blue'],
        imageUrl: 'https://images.unsplash.com/photo-1535016120720-40c646be5580?w=400&h=400&fit=crop'
      }
    }),
    prisma.character.upsert({
      where: { id: 'wonder-woman' },
      update: {},
      create: {
        id: 'wonder-woman',
        name: 'Wonder Woman',
        series: 'DC Movies',
        category: 'MOVIE',
        difficulty: 4,
        popularity: 87.4,
        description: 'Principessa guerriera di Themyscira',
        tags: ['movie', 'dc comics', 'superhero', 'warrior'],
        imageUrl: 'https://images.unsplash.com/photo-1544725176-7c40e5a71c5e?w=400&h=400&fit=crop'
      }
    })
  ]);

  console.log(`✅ Seeded ${characters.length} characters`);

  // Seed trend data for characters
  const trendData = await Promise.all([
    // Nezuko trending data
    prisma.trendData.create({
      data: {
        characterId: 'nezuko-kamado',
        platform: 'INSTAGRAM',
        mentions: 1250,
        engagement: 8750,
        date: new Date('2024-01-01')
      }
    }),
    prisma.trendData.create({
      data: {
        characterId: 'nezuko-kamado',
        platform: 'TIKTOK',
        mentions: 2100,
        engagement: 15600,
        date: new Date('2024-01-01')
      }
    }),
    
    // Spider-Man trending data
    prisma.trendData.create({
      data: {
        characterId: 'spider-man',
        platform: 'INSTAGRAM',
        mentions: 1800,
        engagement: 12400,
        date: new Date('2024-01-01')
      }
    }),
    prisma.trendData.create({
      data: {
        characterId: 'spider-man',
        platform: 'TIKTOK',
        mentions: 3200,
        engagement: 28900,
        date: new Date('2024-01-01')
      }
    }),

    // Sailor Moon trending data
    prisma.trendData.create({
      data: {
        characterId: 'sailor-moon',
        platform: 'INSTAGRAM',
        mentions: 980,
        engagement: 6200,
        date: new Date('2024-01-01')
      }
    }),
    
    // Harley Quinn trending data
    prisma.trendData.create({
      data: {
        characterId: 'harley-quinn',
        platform: 'TIKTOK',
        mentions: 1650,
        engagement: 11200,
        date: new Date('2024-01-01')
      }
    }),

    // Link trending data
    prisma.trendData.create({
      data: {
        characterId: 'link-zelda',
        platform: 'INSTAGRAM',
        mentions: 750,
        engagement: 4800,
        date: new Date('2024-01-01')
      }
    })
  ]);

  console.log(`✅ Seeded ${trendData.length} trend data entries`);
}

main()
  .catch((e) => {
    console.error('❌ Seeding failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
