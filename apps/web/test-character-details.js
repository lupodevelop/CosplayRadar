/**
 * Script di test per verificare come ottenere i dettagli dei personaggi con serie
 */

const testCharacterDetails = async () => {
  try {
    console.log('Testing character details API...');
    
    // Test con un personaggio famoso (Lelouch)
    const response = await fetch('https://api.jikan.moe/v4/characters/417');
    const data = await response.json();
    
    console.log('Character details:', {
      name: data.data.name,
      anime: data.data.anime?.slice(0, 3).map(a => a.anime.title),
      manga: data.data.manga?.slice(0, 3).map(m => m.manga.title),
      favorites: data.data.favorites,
    });

    return data;
  } catch (error) {
    console.error('Error testing character details:', error);
    throw error;
  }
};

// Esegui il test
testCharacterDetails()
  .then(() => {
    console.log('✅ Character details test completed successfully');
    process.exit(0);
  })
  .catch((error) => {
    console.error('❌ Character details test failed:', error.message);
    process.exit(1);
  });
