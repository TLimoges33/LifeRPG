import React, { useState } from "react";
import { api } from "./api";

export default function TwoFASetup() {
  const [otpauth, setOtpauth] = useState(null);
  const [codes, setCodes] = useState([]);
  const [code, setCode] = useState("");
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);
  const [qrCode, setQrCode] = useState(null);

  async function beginSetup() {
    setError(null);
    setStatus("loading");
    try {
      const res = await api("/v1/auth/2fa/setup", { method: "POST" });
      setOtpauth(res.otpauth_uri);
      setCodes(res.recovery_codes || []);

      // Get secure QR code from server
      const qrRes = await api("/v1/auth/2fa/qr", { method: "GET" });
      setQrCode(qrRes.qr_code);

      setStatus("ready");
    } catch (e) {
      setError(String(e));
      setStatus("idle");
    }
  }

  async function enable2fa(e) {
    e.preventDefault();
    setError(null);
    try {
      await api("/v1/auth/2fa/enable", {
        method: "POST",
        body: JSON.stringify({ code }),
      });
      setStatus("enabled");
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <div style={{ marginTop: 20 }}>
      <h2>Two-Factor Auth (TOTP) Setup</h2>
      <p>Step 1: Begin setup to get a QR and recovery codes.</p>
      <button onClick={beginSetup} disabled={status === "loading"}>
        Begin Setup
      </button>
      {status === "loading" && <div>Loading…</div>}
      {error && <div style={{ color: "crimson", marginTop: 8 }}>{error}</div>}

      {otpauth && (
        <div style={{ marginTop: 16, display: "flex", gap: 24 }}>
          <div>
            <div>
              <strong>Scan this QR in your authenticator</strong>
            </div>
            {qrCode && (
              <img src={qrCode} alt="TOTP QR" width={180} height={180} />
            )}
            <div style={{ fontSize: 12, color: "#555", marginTop: 8 }}>
              If QR fails, use URI:
              <br />
              <code style={{ wordBreak: "break-all" }}>{otpauth}</code>
            </div>
          </div>
          <div>
            <div>
              <strong>Recovery codes</strong> (save these now — they won't be
              shown again)
            </div>
            <ul>
              {codes.map((c, i) => (
                <li key={i}>
                  <code>{c}</code>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {otpauth && status !== "enabled" && (
        <form onSubmit={enable2fa} style={{ marginTop: 16 }}>
          <div>Step 2: Enter the 6-digit code from your authenticator</div>
          <input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="123456"
          />
          <button type="submit" style={{ marginLeft: 8 }}>
            Enable 2FA
          </button>
        </form>
      )}

      {status === "enabled" && (
        <div style={{ marginTop: 16, color: "green" }}>
          2FA enabled. Keep your recovery codes somewhere safe.
        </div>
      )}
    </div>
  );
}
