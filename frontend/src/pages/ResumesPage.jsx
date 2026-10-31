import { useEffect, useState } from "react";
import { api } from "../api.js";

const EMPTY = {
  title: "",
  full_name: "",
  city: "",
  phone: "",
  contact_email: "",
  salary: "",
  experience: "",
  education: "",
  about: "",
  skills: "",
  languages: "",
};

const splitList = (s) =>
  s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);

// S-01: список своих резюме + форма создания/редактирования
export default function ResumesPage() {
  const [resumes, setResumes] = useState([]);
  const [editing, setEditing] = useState(null); // null — список, "new" или id
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");

  const load = () =>
    api("/resumes/")
      .then((data) => setResumes(data.results))
      .catch((err) => setError(err.message));

  useEffect(() => {
    load();
  }, []);

  function startEdit(resume) {
    setError("");
    if (!resume) {
      setForm(EMPTY);
      setEditing("new");
      return;
    }
    setForm({
      ...EMPTY,
      ...Object.fromEntries(Object.entries(resume).map(([k, v]) => [k, v ?? ""])),
      skills: resume.skills.join(", "),
      languages: resume.languages.join(", "),
    });
    setEditing(resume.id);
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    const body = {
      ...Object.fromEntries(Object.keys(EMPTY).map((k) => [k, form[k]])),
      salary: form.salary === "" ? null : Number(form.salary),
      skills: splitList(form.skills),
      languages: splitList(form.languages),
    };
    try {
      if (editing === "new") await api("/resumes/", { method: "POST", body });
      else await api(`/resumes/${editing}/`, { method: "PATCH", body });
      setEditing(null);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onDelete(id) {
    if (!confirm("Удалить резюме?")) return;
    await api(`/resumes/${id}/`, { method: "DELETE" });
    load();
  }

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  if (editing !== null) {
    return (
      <form className="card" onSubmit={onSubmit}>
        <h2>{editing === "new" ? "Новое резюме" : "Редактирование резюме"}</h2>
        <div className="grid2">
          <label>
            Желаемая должность *
            <input required value={form.title} onChange={set("title")} />
          </label>
          <label>
            ФИО *
            <input required value={form.full_name} onChange={set("full_name")} />
          </label>
          <label>
            Город
            <input value={form.city} onChange={set("city")} />
          </label>
          <label>
            Желаемая зарплата, сом
            <input type="number" min={0} value={form.salary} onChange={set("salary")} />
          </label>
          <label>
            Телефон
            <input value={form.phone} onChange={set("phone")} />
          </label>
          <label>
            Email для связи
            <input type="email" value={form.contact_email} onChange={set("contact_email")} />
          </label>
        </div>
        <label>
          Навыки (через запятую)
          <input placeholder="python, django, sql" value={form.skills} onChange={set("skills")} />
        </label>
        <label>
          Языки (через запятую)
          <input placeholder="кыргызский, русский, английский B1" value={form.languages} onChange={set("languages")} />
        </label>
        <label>
          Опыт работы
          <textarea rows={4} value={form.experience} onChange={set("experience")} />
        </label>
        <label>
          Образование
          <textarea rows={3} value={form.education} onChange={set("education")} />
        </label>
        <label>
          О себе
          <textarea rows={3} value={form.about} onChange={set("about")} />
        </label>
        {error && <p className="error pre">{error}</p>}
        <div className="row">
          <button className="btn">Сохранить</button>
          <button type="button" className="link" onClick={() => setEditing(null)}>
            Отмена
          </button>
        </div>
      </form>
    );
  }

  return (
    <section>
      <div className="row between">
        <h2>Мои резюме</h2>
        <button className="btn" onClick={() => startEdit(null)}>
          + Новое резюме
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {resumes.length === 0 && <p className="muted">Пока нет ни одного резюме.</p>}
      <ul className="list">
        {resumes.map((r) => (
          <li key={r.id} className="card">
            <div className="row between">
              <div>
                <h3>{r.title}</h3>
                <p className="muted small">
                  {r.full_name}
                  {r.city && ` · ${r.city}`}
                  {r.salary && ` · от ${r.salary.toLocaleString("ru-RU")} сом`}
                </p>
              </div>
              <div className="row">
                <button className="link" onClick={() => startEdit(r)}>
                  Изменить
                </button>
                <button className="link danger" onClick={() => onDelete(r.id)}>
                  Удалить
                </button>
              </div>
            </div>
            <div className="tags">
              {r.skills.map((s) => (
                <span key={s} className="tag">
                  {s}
                </span>
              ))}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
