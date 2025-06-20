// Test semplice per una API alla volta
const testAPI = async (url, method = 'GET', body = null) => {
  try {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' }
    };
    
    if (body) {
      options.body = JSON.stringify(body);
    }
    
    console.log(`Testing ${method} ${url}...`);
    const response = await fetch(url, options);
    const data = await response.json();
    
    console.log('Status:', response.status);
    console.log('Response:', JSON.stringify(data, null, 2));
    return data;
    
  } catch (error) {
    console.error('Error:', error.message);
    return null;
  }
};

const runTests = async () => {
  console.log('=== Testing Google Trends APIs ===\n');
  
  // Test 1: Sync status
  await testAPI('http://localhost:3000/api/admin/sync', 'POST', { action: 'status' });
  
  console.log('\n---\n');
  
  // Test 2: Google Trends status
  await testAPI('http://localhost:3000/api/admin/trends');
  
  console.log('\n---\n');
  
  // Test 3: Query trends
  await testAPI('http://localhost:3000/api/trends?limit=3');
};

runTests();
