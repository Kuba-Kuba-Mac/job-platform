import { useState } from "react";
import { Link } from "react-router-dom";
import { api, errorText } from "../api.js";

// F-04: «Забыли пароль?» — запрос ссылки для сброса
export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const data = await api("/auth/password/reset/", { method: "POST", body: { email } });
      setMessage(data.detail);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  if (message) {
    return (
      <section className="card narrow">
        <h2>Проверьте почту</h2>
        <p className="success">{message}</p>
        <p className="muted small">Письмо может прийти не сразу. Проверьте также папку «Спам».</p>
        <Link to="/login">Вернуться ко входу</Link>
      </section>
    );
  }

  return (
    <form className="card narrow" onSubmit={onSubmit}>
      <h2>Восстановление пароля</h2>
      <p className="muted small">Укажите email, с которым вы регистрировались. Мы пришлём ссылку для нового пароля.</p>
      <label>
        Email
        <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      </label>
      {error && <p className="error pre">{error}</p>}
      <button className="btn" disabled={busy}>
        {busy ? "Отправляем…" : "Отправить ссылку"}
      </button>
      <p className="muted small">
        Вспомнили пароль? <Link to="/login">Войти</Link>
      </p>
    </form>
  );
}
