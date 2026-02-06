"use client";

import { useEffect, useMemo, useRef,useState } from "react";


const API = process.env.NEXT_PUBLIC_API_BASE;
console.log("API BASE:", API);

const token =
  typeof window !== "undefined"
    ? new URLSearchParams(window.location.search).get("token")
    : null;

if (token) {
  sessionStorage.setItem("access_token", token);
}



export default function Dashboard() {
const [profile, setProfile] = useState(null);
const [loading, setLoading] = useState(true);
const [lastEmails, setLastEmails] = useState([]);
const [pendingReply, setPendingReply] = useState(null);
const [pendingEmail, setPendingEmail] = useState(null);

const [authError, setAuthError] = useState(false)


  // Chat state
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text:
        "Hi! I can read your last emails, summarize them, draft replies, and send replies if you confirm.\n\n" +
        "Try typing: show last 5 emails",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  // Load profile (and confirm user is authenticated)
  useEffect(() => {
    async function run() {
       try {
      const res = await fetch(`${API}/gmail/profile`, {
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
          },
       });

      if (!res.ok) {
        setAuthError(true);
        setLoading(false);
        return;
      }
const data = await res.json();
      setProfile(data);
    } catch (e) {
      setAuthError(true);
    } finally {
      setLoading(false);
    }
  }
    run();
  }, []);

  const headerText = useMemo(() => {
    if (!profile) return "Dashboard";
    return `Dashboard — ${profile.emailAddress}`;
  }, [profile]);

  async function logout() {
    await fetch(`${API}/auth/logout`, {
      method: "POST",
      headers: {
  Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
},

    });
    window.location.href = "/";
  }

  function addMessage(role, text) {
    setMessages((prev) => [...prev, { role, text }]);
  }

  function extractNumber(text) {
  const m = text.match(/last\s+(\d+)/i);
  return m ? Number(m[1]) : null;
}

function extractIndex(text) {
  const m = text.match(/reply\s+(\d+)/i);
  return m ? Number(m[1]) : null;
}

function formatRawEmails(emails) {
  return emails
    .map((e, i) => {
      const idx = e.index ?? i + 1;
      return (
        `Email #${idx}\n` +
        `From: ${e.from}\n` +
        `Subject: ${e.subject}\n\n` +
        `${e.snippet || ""}\n`
      );
    })
    .join("\n---\n\n");
}

function formatSummaries(emails) {
  return emails
    .map((e, i) => {
      const idx = e.index ?? i + 1;
      return (
        `Email #${idx}\n` +
        `From: ${e.from}\n` +
        `Subject: ${e.subject}\n` +
        `Summary: ${e.ai_summary}\n`
      );
    })
    .join("\n---\n\n");
}

function formatReplies(emails) {
  return emails
    .map((e) => {
      const idx = e.index;

      return (
        `Email #${idx}\n` +
        `From: ${e.from || "Unknown"}\n` +
        `Subject: ${e.subject || "(no subject)"}\n\n` +
        `Draft Reply:\n${e.ai_reply_draft || "(no reply)"}\n`
      );
    })
    .join("\n---\n\n");
}

function extractSendEmail(text) {
  // format:
  // send email to someone@gmail.com subject: Hello body: Hi there
  const mTo = text.match(/to\s+([^\s]+@[^\s]+)/i);
  const mSubject = text.match(/subject\s*:\s*([\s\S]+?)(?=\s+body\s*:|$)/i);
  const mBody = text.match(/body\s*:\s*([\s\S]+)$/i);

  if (!mTo || !mSubject || !mBody) return null;

  return {
    to: mTo[1].trim(),
    subject: mSubject[1].trim(),
    body: mBody[1].trim(),
  };
}

function formatSendEmailPreview(p) {
  return (
    `You're about to send an email:\n\n` +
    `To: ${p.to}\n` +
    `Subject: ${p.subject}\n` +
    `Body:\n${p.body}\n\n` +
    `Confirm? Type: yes / no`
  );
}

function extractReplyIndex(text) {
  //"send reply 9" OR "reply 9"
  const m = text.match(/\b(?:send\s+reply|reply)\s+(\d+)\b/i);
  return m ? Number(m[1]) : null;
}




async function handleSend(override) {
  const text =
  typeof override === "string"
    ? override.trim()
    : input.trim();

  if (!text || busy) return;

  setInput("");
  addMessage("user", text);

  const normalized = text.toLowerCase();
  const n = extractNumber(text);

  try {

    // SHOW RAW EMAILS
  
    if (normalized.startsWith("show last") && n) {
      setBusy(true);
      addMessage("assistant", `Fetching last ${n} emails...`);

      const res = await fetch(`${API}/gmail/last?n=${n}`, {
        headers: {
  Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
},

      });

      const data = await res.json();
      setLastEmails(data.emails || []);

      addMessage("assistant", formatRawEmails(data.emails || []));
      return;
    }

    // SUMMARIZE EMAILS

    if (normalized.startsWith("summarize last") && n) {
      setBusy(true);
      addMessage("assistant", `Summarizing last ${n} emails...`);

      const res = await fetch(`${API}/gmail/last_with_summaries?n=${n}`, {
       headers: {
  Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
},

      });

      const data = await res.json();
      setLastEmails(data.emails || []);

      addMessage("assistant", formatSummaries(data.emails || []));
      return;
    }

    // DRAFT REPLIES

    if (normalized.startsWith("draft replies") && n) {
      const count = Math.max(n, 20);
      setBusy(true);
      addMessage("assistant", `Drafting replies for last ${n} emails...`);

      const res = await fetch(`${API}/gmail/last_with_replies?n=${n}`, {
        headers: {
  Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
},

      });

      const data = await res.json();
      setLastEmails(data.emails || []);

      addMessage("assistant", formatReplies(data.emails || []));
      addMessage("assistant", `Type: send reply 2`);
      return;
    }

    // ✅ SEND EMAIL (ask confirmation)

if (normalized.startsWith("send email")) {
  const payload = extractSendEmail(text);

  if (!payload) {
    addMessage(
      "assistant",
      `Use this format:\n\nsend email to someone@gmail.com \nsubject: Hello \nbody: Hi there`
    );
    return;
  }

  setPendingEmail(payload);
  addMessage("assistant", formatSendEmailPreview(payload));
  return;
}

// ✅ confirm send email
if (normalized === "yes" && pendingEmail) {
  const payload = pendingEmail;
  setPendingEmail(null);

  setBusy(true);
  addMessage("assistant", "Sending email...");

  try {
    const res = await fetch(`${API}/gmail/send`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
  },
  body: JSON.stringify(payload),
});




    if (!res.ok) {
      const errText = await res.text();
      addMessage("assistant", `Failed to send email.\n\n${errText}`);
      return;
    }

    const data = await res.json();
    addMessage(
      "assistant",
      `✅ Sent!\n\nStatus: ${data.status}\nId: ${data.id}\nThread: ${data.threadId}`
    );
  } catch (e) {
    addMessage("assistant", "Network error while sending email.");
  } finally {
    setBusy(false);
  }
  return;
}

if (normalized === "no" && pendingEmail) {
  setPendingEmail(null);
  addMessage("assistant", "Cancelled.");
  return;
}

    // SEND REPLY


if (normalized.startsWith("send reply") || normalized.startsWith("reply")) {
  const idx = extractReplyIndex(text);

  if (!idx) {
    addMessage("assistant", 'Say: "send reply 9"');
    return;
  }

  if (!lastEmails || lastEmails.length === 0) {
    addMessage(
      "assistant",
      "First run: draft replies for last 15 emails\nThen: send reply 9"
    );
    return;
  }

  const email = lastEmails.find((e) => e.index === idx);

  if (!email) {
    addMessage(
      "assistant",
      `I don’t have Email #${idx} cached.\nRun: draft replies for last 15 emails (or more) first.`
    );
    return;
  }

  const draft = email.ai_reply_draft;
  if (!draft) {
    addMessage("assistant", `No draft reply found for Email #${idx}.`);
    return;
  }

  setPendingReply({
  index: idx,                 // keep for UI only
  to_email: email.to_email,
  subject: email.subject || "",
  body: draft,
});

  addMessage(
    "assistant",
    `Confirm sending reply for Email #${idx}?\nType: yes / no`
  );
  return;
}

// CONFIRM SEND REPLY

if (normalized === "yes" && pendingReply) {
  const payload = {
  to_email: pendingReply.to_email,
  subject: pendingReply.subject,
  body: pendingReply.body,
  confirm: true,
};



  setPendingReply(null);

  setBusy(true);
  addMessage("assistant", `Sending reply for Email #${payload.email_index}...`);

  try {
   const res = await fetch(`${API}/gmail/send_reply`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
  },
  body: JSON.stringify(payload),
});



    if (!res.ok) {
      const errText = await res.text();
      addMessage("assistant", `Failed to send reply.\n\n${errText}`);
      return;
    }

    const data = await res.json();
    addMessage(
      "assistant",
      `✅ Reply sent!\n\nTo: ${data.to}\nSubject: ${data.subject}\nId: ${data.id}\nThread: ${data.threadId}`
    );
  } catch (e) {
    addMessage("assistant", "Network error while sending reply.");
  } finally {
    setBusy(false);
  }
  return;
}

if (normalized === "no" && pendingReply) {
  setPendingReply(null);
  addMessage("assistant", "Okay, not sending.");
  return;
}


    // FALLBACK

    addMessage(
      "assistant",
      `Try:
show last 5 emails
summarize last 5 emails
draft replies for last 5 emails`
    );

  } catch (err) {
    addMessage("assistant", "Backend error. Is server running?");
  } finally {
    setBusy(false);
  }
}


   const bottomRef = useRef(null);

useEffect(() => {
  bottomRef.current?.scrollIntoView({ behavior: "smooth" });
}, [messages, busy]);

  if (loading) {
    return <div style={{ padding: 40, fontFamily: "system-ui" }}>Loading…</div>;
  }

 
  return (
  <div
    style={{
      minHeight: "100vh",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      padding: 18,
      fontFamily: "system-ui",
      background:
        "radial-gradient(1200px 600px at 20% 10%, rgba(109, 135, 239, 0.55), transparent 60%)," +
        "radial-gradient(900px 500px at 80% 30%, rgba(225, 146, 63, 0.35), transparent 55%)," +
        "linear-gradient(135deg, #f8fafc, #f1f5f9)",
    }}
  >
    {/* Main Card */}
    <div
      style={{
        width: "100%",
        maxWidth: 980,
        height: "92vh",
        borderRadius: 22,
        background: "rgba(221, 219, 219, 0.65)",
        backdropFilter: "blur(10px)",
        boxShadow: "0 18px 60px rgba(0,0,0,0.10)",
        border: "1px solid rgba(255,255,255,0.6)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Top bar */}
      <div
        style={{
          height: 56,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 16px",
          color: "#353434",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: 10,
              background: "rgba(17,24,39,0.08)",
              display: "grid",
              placeItems: "center",
              fontWeight: 700,
              color: "#353434",
            }}
          >
            ✦
          </div>
          <div style={{ fontWeight: 700, color: "#353434" }}>
            <a href="/dashboard">Constructure AI</a>
          </div>
        </div>

        <button
          onClick={logout}
          style={{
            width: 34,
            height: 34,
            borderRadius: 12,
            border: "1px solid rgba(0,0,0,0.08)",
            background: "rgba(255,255,255,0.7)",
            cursor: "pointer",
            color: "#353434",
            fontWeight: "bold",
          }}
          title="Logout"
        >
          ⎋
        </button>
      </div>

      {/* Content area: MUST be flex column + minHeight 0 */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minHeight: 0, // ✅ key for scroll to work
          position: "relative",
        }}
      >
        {/* Scrollable content */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: 16,
            minHeight: 0,
            paddingBottom: 130, // ✅ space for input bar (so text doesn’t hide under it)
          }}
        >
          {/* If chat hasn't started: show hero */}
          {messages.filter((m) => m.role === "user").length === 0 ? (
            <div
              style={{
                height: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: 18,
                textAlign: "center",
                gap: 14,
                color: "#353434",
              }}
            >
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: 18,
                  background: "rgba(17,24,39,0.08)",
                  display: "grid",
                  placeItems: "center",
                  fontSize: 22,
                }}
              >
                👋
              </div>

              <div
                style={{
                  fontSize: 18,
                  color: "rgba(17,24,39,0.65)",
                  fontWeight: 500,
                }}
              >
                Hi, {profile?.emailAddress || "there"}
              </div>

              <div style={{ fontSize: 32, fontWeight: 800, lineHeight: 1.1 }}>
                Can I help you with anything?
              </div>

              <div
                style={{
                  maxWidth: 520,
                  color: "rgba(17,24,39,0.6)",
                  fontWeight: 400,
                }}
              >
                I can summarize your latest emails, draft replies, and send them
                after your confirmation. Try a command below to get started.
              </div>

              {/* Suggestion cards */}
              <div
                style={{
                  marginTop: 18,
                  display: "grid",
                  gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                  gap: 12,
                  width: "100%",
                  maxWidth: 760,
                }}
              >
                <SuggestionCard
                  title="Summarize Last 5 Emails"
                  subtitle="AI summaries of recent messages"
                  onClick={() => handleSend("summarize last 5 emails")}
                />

                <SuggestionCard
                  title="Send Email"
                  subtitle="Send a new email "
                  onClick={() =>
                    handleSend(
                      "send email"
                    )
                  }
                />

                <SuggestionCard
                  title="Show last 5 Emails"
                  subtitle="Show recent emails"
                  onClick={() => handleSend("show last 5 emails")}
                />
                  

                <SuggestionCard
                  title="Draft Replies"
                  subtitle="AI-generated response suggestions"
                  onClick={() => handleSend("draft replies for last 5 emails")}
                />

                <SuggestionCard
                  title="Send Reply"
                  subtitle="Send a drafted reply by number"
                  onClick={() =>
                    addMessage("assistant", 'Type: send reply 2')
                  }
                />


              </div>
            </div>
          ) : (
            <>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>
                {headerText}
              </div>

              {messages.map((m, idx) => (
                <div
                  key={idx}
                  style={{
                    marginBottom: 12,
                    display: "flex",
                    justifyContent:
                      m.role === "user" ? "flex-end" : "flex-start",
                  }}
                >
                  <div
                    style={{
                      maxWidth: "70%",
                      padding: "10px 12px",
                      borderRadius: 14,
                      background:
                        m.role === "user"
                          ? "rgba(59,130,246,0.12)"
                          : "rgba(17,24,39,0.06)",
                      whiteSpace: "pre-wrap",
                      lineHeight: 1.35,
                      border: "1px solid rgba(0,0,0,0.06)",
                      color: "#353434",
                    }}
                  >
                    {m.text}
                  </div>
                </div>
              ))}

              {/* ✅ put bottomRef ONCE here, not inside map */}
              <div ref={bottomRef} />
            </>
          )}
        </div>

        {/* Input bar pinned (sticky inside card) */}
        <div
          style={{
            flexShrink: 0,
            padding: 14,
            borderTop: "1px solid rgba(0,0,0,0.08)",
            background: "rgba(248,250,252,0.85)",
            backdropFilter: "blur(10px)",
          }}
        >
          <div
            style={{
              display: "flex",
              gap: 10,
              padding: 10,
              borderRadius: 16,
              background: "rgba(255,255,255,0.75)",
              border: "1px solid rgba(0,0,0,0.08)",
              boxShadow: "0 10px 25px rgba(0,0,0,0.06)",
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={busy ? "Working..." : "Ask or type a command…"}
              disabled={busy}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
              style={{
                flex: 1,
                padding: "12px 12px",
                borderRadius: 12,
                border: "1px solid rgba(0,0,0,0.10)",
                outline: "none",
                background: "rgba(255,255,255,0.9)",
                color: "#353434",
              }}
            />

            <button
              onClick={handleSend}
              disabled={busy || !input.trim()}
              style={{
                padding: "12px 14px",
                borderRadius: 12,
                border: "1px solid rgba(0,0,0,0.10)",
                background: busy
                  ? "rgba(0,0,0,0.05)"
                  : "rgba(9, 9, 9, 0.2)",
                cursor: busy ? "not-allowed" : "pointer",
                fontWeight: 900,
                color: "#353434",
              }}
            >
              Send →
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
);



    
}
function SuggestionCard({ title, subtitle, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        textAlign: "left",
        padding: 14,
        borderRadius: 16,
        border: "1px solid rgba(0,0,0,0.08)",
        background: "rgba(255,255,255,0.72)",
        cursor: "pointer",
        boxShadow: "0 10px 25px rgba(0,0,0,0.05)",
      }}
    >
      <div style={{ fontWeight: 900, marginBottom: 6, color: "#353434" }}>{title}</div>
      <div style={{ fontSize: 12, color: "rgba(17,24,39,0.6)", fontWeight: 500 }}>{subtitle}</div>
    </button>
  );
}

