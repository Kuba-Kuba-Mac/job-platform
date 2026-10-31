import { useEffect, useState } from "react";
import { api } from "../api.js";

const EMPTY = { name: "", description: "", city: "", phone: "", contact_email: "", website: "" };
const STATUS = { pending: "На модерации", approved: "Одобрена", rejected: "Отклонена" };

// E-01: профиль компании работодателя
export default function CompanyPage() {
  const [company, setCompany] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [logo, setLogo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api("/companies/me/")
      .then((data) => {
        setCompany(data);
        setForm(pick(data));
      })
      .catch((err) => {
        if (err.status !== 404) setError(err.message);
      })
      .finally(() => setLoading(false));
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setMessage("");
    const body = new FormData();
    Object.entries(form).forEach(([k, v]) => body.append(k, v ?? ""));
    if (logo) body.append("logo", logo);
    try {
      const data = await api("/companies/me/", { method: company ? "PATCH" : "POST", body });
      setCompany(data);
      setForm(pick(data));
      setLogo(null);
      setMessage("Сохранено. Профиль отправлен на модерацию.");
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading) return <p className="muted">Загрузка…</p>;
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  return (
    <form className="card" onSubmit={onSubmit}>
      <div className="row between">
        <h2>{company ? "Профиль компании" : "Создайте профиль компании"}</h2>
        {company && <span className={`badge ${company.moderation_status}`}>{STATUS[company.moderation_status]}</span>}
      </div>
      {company?.logo && <img className="logo-preview" src={company.logo} alt="Логотип" />}
      <label>
        Название *
        <input required maxLength={200} value={form.name} onChange={set("name")} />
      </label>
      <label>
        Описание
        <textarea rows={5} value={form.description} onChange={set("description")} />
      </label>
      <div className="grid2">
        <label>
          Город
          <input value={form.city} onChange={set("city")} />
        </label>
        <label>
          Телефон
          <input value={form.phone} onChange={set("phone")} />
        </label>
        <label>
          Контактный email
          <input type="email" value={form.contact_email} onChange={set("contact_email")} />
        </label>
        <label>
          Сайт
          <input type="url" placeholder="https://" value={form.website} onChange={set("website")} />
        </label>
      </div>
      <label>
        Логотип (до 2 МБ)
        <input type="file" accept="image/*" onChange={(e) => setLogo(e.target.files[0] || null)} />
      </label>
      {error && <p className="error pre">{error}</p>}
      {message && <p className="success">{message}</p>}
      <button className="btn">{company ? "Сохранить" : "Создать"}</button>
    </form>
  );
}

function pick(data) {
  return Object.fromEntries(Object.keys(EMPTY).map((k) => [k, data[k] ?? ""]));
}
