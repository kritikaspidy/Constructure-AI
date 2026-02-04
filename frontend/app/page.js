"use client";

export default function Home() {
  const API = process.env.NEXT_PUBLIC_API_BASE;

  return (
    <div style={{ padding: 40 }}>
      <h1>Constructure AI Email Assistant</h1>

      <button onClick={() => window.location.href = `${API}/auth/login`}>
        Sign in with Google
      </button>
    </div>
  );
}
