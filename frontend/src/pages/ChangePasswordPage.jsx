import { useState } from "react";
import { api, setTokens } from "../api.js";
import PasswordStrength from "../components/PasswordStrength.jsx";

const EMPTY = { old_password: "", new_password: "", new_password2: "" };

// Ошибки сервера вида {field: [msg]}: сообщения уже на русском и понятны без имени поля
function formatError(err) {
  if (!err.data || typeof err.data !== "object" || err.data.detail) return err.message;
  return Object.values(err.data).flat().join("\n");
}

// F-03: смена пароля в личном кабинете (для любой роли)
export default function ChangePasswordPage() {
  const [form, setForm] = useState(EMPTY);
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setMessage("");
    if (form.new_password !== form.new_password2) {
      setError("Новый пароль и повтор не совпадают");
      return;
    }
    setBusy(true);
    try {
      const tokens = await api("/auth/password/change/", {
        method: "POST",
        body: { old_password: form.old_password, new_password: form.new_password },
      });
      // Старые refresh-токены отозваны сервером, продолжаем сессию с новыми
      setTokens(tokens);
      setForm(EMPTY);
      setMessage("Пароль изменён");
    } catch (err) {
      setError(formatError(err));
    } finally {
      setBusy(false);
    }
  }

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });
  const type = show ? "text" : "password";

  return (
    <form className="card narrow" onSubmit={onSubmit}>
      <h2>Смена пароля</h2>
      <label>
        Текущий пароль
        <input type={type} required autoComplete="current-password" value={form.old_password} onChange={set("old_password")} />
      </label>
      <label>
        Новый пароль
        <input type={type} required autoComplete="new-password" value={form.new_password} onChange={set("new_password")} />
      </label>
      <PasswordStrength password={form.new_password} />
      <label>
        Повторите новый пароль
        <input type={type} required autoComplete="new-password" value={form.new_password2} onChange={set("new_password2")} />
      </label>
      <button type="button" className="link small" onClick={() => setShow(!show)} aria-pressed={show}>
        {show ? "Скрыть пароли" : "Показать пароли"}
      </button>
      <button className="btn" disabled={busy}>
        {busy ? "Сохраняем…" : "Сменить пароль"}
      </button>
      {error && <p className="error pre">{error}</p>}
      {message && <p className="success">{message}</p>}
    </form>
  );
}
