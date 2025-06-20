"use client";

import { useSession } from "next-auth/react";

export default function SessionDebug() {
  const { data: session, status } = useSession();

  return (
    <div className="p-8 space-y-4">
      <h1 className="text-2xl font-bold">Session Debug</h1>
      
      <div className="bg-gray-100 p-4 rounded">
        <h2 className="font-semibold">Status:</h2>
        <p>{status}</p>
      </div>
      
      <div className="bg-gray-100 p-4 rounded">
        <h2 className="font-semibold">Session Data:</h2>
        <pre className="text-sm overflow-auto">
          {JSON.stringify(session, null, 2)}
        </pre>
      </div>
    </div>
  );
}
