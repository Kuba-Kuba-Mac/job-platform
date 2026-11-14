import { useState } from "react";
import { useLocation } from "react-router-dom";
import { api, errorText } from "../api.js";
import { useAuth } from "../auth.jsx";

// F-04: напоминание подтвердить email. Вход не блокируется, но адрес нужен для писем.
export default function VerifyEmailBanner() {
  const { user } = useAuth();
  const { pathname } = useLocation();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (!user || user.email_verified || pathname === "/verify-email") return null;

  async function resend() {
    setBusy(true);
    setError("");
    try {
      const data = await api("/auth/verify-email/resend/", { method: "POST" });
      setMessage(data.detail);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="banner" role="status">
      <span>
        Подтвердите email <strong>{user.email}</strong> — ссылка в письме.
      </span>
      {message ? (
        <span className="success">{message}</span>
      ) : (
        <button type="button" className="link" onClick={resend} disabled={busy}>
          {busy ? "Отправляем…" : "Отправить письмо ещё раз"}
        </button>
      )}
      {error && <span className="error">{error}</span>}
    </div>
  );
}
