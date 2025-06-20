import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function testConnection() {
  try {
    console.log('🔍 Testing database connection...');
    
    const characters = await prisma.character.findMany({
      take: 3,
      select: {
        id: true,
        name: true,
        series: true,
        category: true,
        popularity: true
      }
    });

    console.log('✅ Database connection successful!');
    console.log(`Found ${characters.length} characters:`);
    characters.forEach(char => {
      console.log(`- ${char.name} from ${char.series} (${char.category})`);
    });

  } catch (error) {
    console.error('❌ Database connection failed:', error);
  } finally {
    await prisma.$disconnect();
  }
}

testConnection();
