"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function SimpleSignInPage() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const router = useRouter();

  const handleSimpleLogin = () => {
    setLoading(true);
    setMessage("Simulando login...");
    
    // Simuliamo un login riuscito
    setTimeout(() => {
      setMessage("Login simulato riuscito! Reindirizzamento...");
      setTimeout(() => {
        router.push("/dashboard");
      }, 1000);
    }, 1000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Login Semplificato (Debug)
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Test della dashboard senza autenticazione
          </p>
        </div>
        <div className="mt-8 space-y-6">
          <div className="space-y-4">
            <div className="text-sm text-gray-700 bg-blue-50 p-4 rounded">
              <p><strong>Credenziali demo:</strong></p>
              <p>Email: demo@cosplayradar.com</p>
              <p>Password: demo123</p>
            </div>
            
            <button
              onClick={handleSimpleLogin}
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? "Accedendo..." : "Accedi alla Dashboard (Debug)"}
            </button>
            
            {message && (
              <div className="text-center text-sm text-green-600">
                {message}
              </div>
            )}
            
            <div className="text-center">
              <Link 
                href="/auth/signin"
                className="font-medium text-indigo-600 hover:text-indigo-500"
              >
                Vai al login normale
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
