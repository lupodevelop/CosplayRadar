const { PrismaClient, UserRole } = require('@prisma/client');
const bcrypt = require('bcryptjs');

const prisma = new PrismaClient();

async function createTestUser() {
  console.log('🚀 Starting test user creation...');
  try {
    console.log('🔐 Creating test user...');
    
    // Hash della password "demo123"
    const hashedPassword = await bcrypt.hash('demo123', 12);
    
    const user = await prisma.user.upsert({
      where: {
        email: 'demo@cosplayradar.com'
      },
      update: {},
      create: {
        email: 'demo@cosplayradar.com',
        password: hashedPassword,
        name: 'Demo User',
        role: UserRole.CREATOR,
        emailVerified: new Date(),
        username: 'demo-user',
        bio: 'Utente demo per test'
      }
    });

    console.log('✅ Test user created successfully!');
    console.log('📧 Email: demo@cosplayradar.com');
    console.log('🔑 Password: demo123');
    console.log(`👤 User ID: ${user.id}`);

  } catch (error) {
    console.error('❌ Failed to create test user:', error);
  } finally {
    await prisma.$disconnect();
  }
}

createTestUser();
