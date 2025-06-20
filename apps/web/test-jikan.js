/**
 * Script di test per Jikan API
 */

const axios = require('axios');

const testJikanAPI = async () => {
  try {
    console.log('Testing Jikan API...');
    
    const response = await axios.get('https://api.jikan.moe/v4/top/characters?page=1', {
      timeout: 10000,
    });

    console.log('Response status:', response.status);
    console.log('Characters found:', response.data.data?.length || 0);
    
    if (response.data.data && response.data.data.length > 0) {
      const firstCharacter = response.data.data[0];
      console.log('First character:', {
        name: firstCharacter.name,
        favorites: firstCharacter.favorites,
        anime: firstCharacter.anime?.length || 0,
        image: firstCharacter.images?.jpg?.image_url,
      });
    }

    return response.data;
  } catch (error) {
    console.error('Error testing Jikan API:', error.message);
    
    if (axios.isAxiosError && axios.isAxiosError(error)) {
      console.error('Status:', error.response?.status);
      console.error('Response:', error.response?.data);
    }
    
    throw error;
  }
};

// Esegui il test
testJikanAPI()
  .then(() => {
    console.log('✅ Jikan API test completed successfully');
    process.exit(0);
  })
  .catch((error) => {
    console.error('❌ Jikan API test failed:', error.message);
    process.exit(1);
  });
