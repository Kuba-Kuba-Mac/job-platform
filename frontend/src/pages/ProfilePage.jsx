import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, errorText } from "../api.js";
import { useAuth } from "../auth.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import { ROLE } from "../labels.js";

const FIELDS = ["full_name", "email", "phone", "city"];
const pick = (user) => Object.fromEntries(FIELDS.map((k) => [k, user[k] ?? ""]));

// F-05: «Мой профиль» — для любой роли
export default function ProfilePage() {
  const { setUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    setLoadError("");
    api("/auth/me/")
      .then((data) => {
        setProfile(data);
        setForm(pick(data));
        setUser(data);
      })
      .catch((err) => setLoadError(errorText(err)));
  }, [setUser]);

  useEffect(load, [load]);

  if (loadError) return <ErrorState message={loadError} onRetry={load} />;
  if (!form) return <Loading />;

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setMessage("");
    setBusy(true);
    // отправляем только изменённые поля
    const body = Object.fromEntries(FIELDS.filter((k) => form[k] !== (profile[k] ?? "")).map((k) => [k, form[k]]));
    try {
      const data = await api("/auth/me/", { method: "PATCH", body });
      setProfile(data);
      setForm(pick(data));
      setUser(data);
      setMessage(
        "email" in body && !data.email_verified
          ? `Сохранено. Мы отправили письмо для подтверждения на ${data.email}.`
          : "Сохранено.",
      );
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  return (
    <form className="card" onSubmit={onSubmit}>
      <div className="row between">
        <h2>Мой профиль</h2>
        <span className="badge approved">{ROLE[profile.role]}</span>
      </div>
      <div className="grid2">
        <label>
          Имя и фамилия
          <input maxLength={200} autoComplete="name" value={form.full_name} onChange={set("full_name")} />
        </label>
        <label>
          Email
          <input type="email" required autoComplete="email" value={form.email} onChange={set("email")} />
          <span className={profile.email_verified ? "small success" : "small warn"}>
            {profile.email_verified ? "✓ подтверждён" : "не подтверждён"}
          </span>
        </label>
        <label>
          Телефон
          <input type="tel" placeholder="+996 555 123 456" autoComplete="tel" value={form.phone} onChange={set("phone")} />
        </label>
        <label>
          Город
          <input maxLength={100} value={form.city} onChange={set("city")} />
        </label>
      </div>
      <p className="muted small">При смене email адрес нужно будет подтвердить заново.</p>
      {error && <p className="error pre">{error}</p>}
      {message && <p className="success">{message}</p>}
      <div className="row">
        <button className="btn" disabled={busy}>
          {busy ? "Сохраняем…" : "Сохранить"}
        </button>
        <Link to="/settings/password">Сменить пароль</Link>
      </div>
    </form>
  );
}
