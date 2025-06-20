const bcrypt = require('bcryptjs');

async function testPassword() {
  const password = 'demo123';
  const storedHash = '$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewbOEZfxmwgBjyru';
  
  console.log('Testing password verification...');
  const isValid = await bcrypt.compare(password, storedHash);
  console.log(`Password "demo123" is valid: ${isValid}`);
  
  // Generiamo un nuovo hash per essere sicuri
  console.log('\nGenerating new hash...');
  const newHash = await bcrypt.hash('demo123', 12);
  console.log(`New hash: ${newHash}`);
  
  const isNewValid = await bcrypt.compare('demo123', newHash);
  console.log(`New hash is valid: ${isNewValid}`);
}

testPassword().catch(console.error);
