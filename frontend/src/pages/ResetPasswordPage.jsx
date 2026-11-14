import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, errorText } from "../api.js";
import PasswordStrength from "../components/PasswordStrength.jsx";

// F-04: новый пароль по ссылке из письма — /reset-password?uid=…&token=…
export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const uid = params.get("uid");
  const token = params.get("token");
  const [form, setForm] = useState({ password: "", password2: "" });
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  if (!uid || !token) {
    return (
      <section className="card narrow">
        <h2>Новый пароль</h2>
        <p className="error">Ссылка неполная. Откройте ссылку из письма целиком или запросите новую.</p>
        <Link to="/forgot-password">Запросить ссылку ещё раз</Link>
      </section>
    );
  }

  if (done) {
    return (
      <section className="card narrow">
        <h2>Пароль изменён</h2>
        <p className="success">Теперь войдите с новым паролем. На других устройствах сессии завершены.</p>
        <Link to="/login" className="btn">
          Войти
        </Link>
      </section>
    );
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    if (form.password !== form.password2) {
      setError("Пароли не совпадают");
      return;
    }
    setBusy(true);
    try {
      await api("/auth/password/reset/confirm/", {
        method: "POST",
        body: { uid, token, new_password: form.password },
      });
      setDone(true);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });
  const type = show ? "text" : "password";

  return (
    <form className="card narrow" onSubmit={onSubmit}>
      <h2>Новый пароль</h2>
      <label>
        Новый пароль
        <input type={type} required minLength={8} autoComplete="new-password" value={form.password} onChange={set("password")} />
      </label>
      <PasswordStrength password={form.password} />
      <label>
        Повторите пароль
        <input type={type} required autoComplete="new-password" value={form.password2} onChange={set("password2")} />
      </label>
      <button type="button" className="link small" onClick={() => setShow(!show)} aria-pressed={show}>
        {show ? "Скрыть пароли" : "Показать пароли"}
      </button>
      {error && (
        <div>
          <p className="error pre">{error}</p>
          <Link to="/forgot-password" className="small">
            Запросить новую ссылку
          </Link>
        </div>
      )}
      <button className="btn" disabled={busy}>
        {busy ? "Сохраняем…" : "Сохранить пароль"}
      </button>
    </form>
  );
}
