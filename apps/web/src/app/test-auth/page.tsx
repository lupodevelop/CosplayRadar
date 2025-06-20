// Test di autenticazione semplice
import { signIn } from 'next-auth/react';

export default function TestAuth() {
  const handleLogin = async () => {
    console.log('Tentativo di login...');
    
    const result = await signIn('credentials', {
      email: 'demo@cosplayradar.com',
      password: 'demo123',
      redirect: false,
    });
    
    console.log('Risultato login:', result);
    
    if (result?.error) {
      console.error('Errore di login:', result.error);
    } else {
      console.log('Login riuscito!');
    }
  };

  return (
    <div className="p-8">
      <h1>Test Autenticazione</h1>
      <button 
        onClick={handleLogin}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Test Login
      </button>
    </div>
  );
}
