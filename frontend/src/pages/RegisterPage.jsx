import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "", password2: "", role: "seeker" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    if (form.password !== form.password2) {
      setError("Пароли не совпадают");
      return;
    }
    setBusy(true);
    try {
      const user = await register(form.email, form.password, form.role);
      navigate(user.role === "employer" ? "/company" : "/resumes");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  return (
    <form className="card narrow" onSubmit={onSubmit}>
      <h2>Регистрация</h2>
      <fieldset className="roles">
        <legend>Я —</legend>
        <label className={form.role === "seeker" ? "role active" : "role"}>
          <input type="radio" name="role" value="seeker" checked={form.role === "seeker"} onChange={set("role")} />
          соискатель
        </label>
        <label className={form.role === "employer" ? "role active" : "role"}>
          <input type="radio" name="role" value="employer" checked={form.role === "employer"} onChange={set("role")} />
          работодатель
        </label>
      </fieldset>
      <label>
        Email
        <input type="email" required autoComplete="email" value={form.email} onChange={set("email")} />
      </label>
      <label>
        Пароль (минимум 8 символов)
        <input type="password" required minLength={8} autoComplete="new-password" value={form.password} onChange={set("password")} />
      </label>
      <label>
        Повторите пароль
        <input type="password" required autoComplete="new-password" value={form.password2} onChange={set("password2")} />
      </label>
      {error && <p className="error pre">{error}</p>}
      <button className="btn" disabled={busy}>
        {busy ? "Создаём…" : "Создать аккаунт"}
      </button>
    </form>
  );
}
