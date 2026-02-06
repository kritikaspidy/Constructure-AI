"use client";

export default function Home() {
  const API = process.env.NEXT_PUBLIC_API_BASE;

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
        background:
          "radial-gradient(1200px 600px at 20% 10%, rgba(109,135,239,0.55), transparent 60%)," +
          "radial-gradient(900px 500px at 80% 30%, rgba(225,146,63,0.35), transparent 55%)," +
          "linear-gradient(135deg, #f8fafc, #f1f5f9)",
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
      }}
    >
      {/* Card */}
      <div
        style={{
          background: "rgba(255,255,255,0.75)",
          backdropFilter: "blur(12px)",
          padding: "60px 70px",
          borderRadius: 18,
          boxShadow: "0 20px 40px rgba(0,0,0,0.08)",
          textAlign: "center",
          display: "flex",
          flexDirection: "column",
          gap: 24,
          maxWidth: 420,
        }}
      >
        <h1
          style={{
            fontSize: 36,
            fontWeight: 700,
            letterSpacing: "-0.5px",
            color: "#0f172a",
            margin: 0,
          }}
        >
          Constructure AI
        </h1>

        <p
          style={{
            fontSize: 16,
            color: "#475569",
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          Your smart email assistant that reads, summarizes and replies — so you
          don’t have to.
        </p>

        <button
          onClick={() => (window.location.href = `${API}/auth/login`)}
          style={{
            marginTop: 10,
            height: 48,
            width: "100%",
            borderRadius: 10,
            border: "none",
            fontSize: 16,
            fontWeight: 600,
            cursor: "pointer",
            color: "#fff",
            background: "linear-gradient(135deg, #6366f1, #4f46e5)",
            boxShadow: "0 10px 20px rgba(79,70,229,0.35)",
            transition: "transform 0.15s ease, box-shadow 0.15s ease",
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = "translateY(-1px)";
            e.currentTarget.style.boxShadow =
              "0 14px 26px rgba(79,70,229,0.45)";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = "translateY(0)";
            e.currentTarget.style.boxShadow =
              "0 10px 20px rgba(79,70,229,0.35)";
          }}
        >
          Sign in with Google
        </button>
      </div>
    </div>
  );
}
