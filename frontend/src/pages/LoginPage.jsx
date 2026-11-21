import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth.jsx";

// Куда вернуть после входа: только внутренние пути (защита от открытого редиректа)
function safeNext(value) {
  return value && value.startsWith("/") && !value.startsWith("//") ? value : null;
}

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = safeNext(params.get("next"));
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const user = await login(form.email, form.password);
      // F-06: каждая роль попадает в свой кабинет (или туда, откуда пришла на вход)
      navigate(next ?? { seeker: "/vacancies", employer: "/vacancies/my", admin: "/admin/moderation" }[user.role] ?? "/");
    } catch (err) {
      if (err.data?.code === "user_blocked") setError(err.message);
      else setError(err.status === 401 ? "Неверный email или пароль" : err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card narrow" onSubmit={onSubmit}>
      <h2>Вход</h2>
      <label>
        Email
        <input type="email" required autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
      </label>
      <label>
        Пароль
        <input type="password" required autoComplete="current-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
      </label>
      {error && <p className="error">{error}</p>}
      <Link to="/forgot-password" className="small">
        Забыли пароль?
      </Link>
      <button className="btn" disabled={busy}>
        {busy ? "Входим…" : "Войти"}
      </button>
      <p className="muted small">
        Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
      </p>
    </form>
  );
}
