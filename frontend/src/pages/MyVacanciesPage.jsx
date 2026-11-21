import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, errorText } from "../api.js";
import { Empty, ErrorState, Loading } from "../components/States.jsx";
import { EMPLOYMENT_TYPE, EXPERIENCE, MODERATION, SCHEDULE, formatSalary, splitList } from "../labels.js";

const EMPTY = {
  title: "",
  description: "",
  city: "",
  salary_from: "",
  salary_to: "",
  experience: "none",
  employment_type: "full",
  schedule: "full_day",
  is_internship: false,
  skills: "",
};

const TABS = [
  { id: "false", label: "Активные" },
  { id: "true", label: "Архив" },
];

function Select({ label, value, onChange, options }) {
  return (
    <label>
      {label}
      <select value={value} onChange={onChange}>
        {Object.entries(options).map(([code, text]) => (
          <option key={code} value={code}>
            {text}
          </option>
        ))}
      </select>
    </label>
  );
}

// E-02: вакансии работодателя — создание, редактирование, архив
export default function MyVacanciesPage() {
  const [tab, setTab] = useState("false");
  const [data, setData] = useState(null);
  const [hasCompany, setHasCompany] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [editing, setEditing] = useState(null); // null — список, "new" или id
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    setLoadError("");
    setData(null);
    Promise.all([
      api("/companies/me/").then(
        () => true,
        (err) => (err.status === 404 ? false : Promise.reject(err)),
      ),
      api(`/vacancies/my/?archived=${tab}`),
    ])
      .then(([company, vacancies]) => {
        setHasCompany(company);
        setData(vacancies);
      })
      .catch((err) => setLoadError(errorText(err)));
  }, [tab]);

  useEffect(load, [load]);

  function startEdit(vacancy) {
    setError("");
    setMessage("");
    if (!vacancy) {
      setForm(EMPTY);
      setEditing("new");
      return;
    }
    setForm({
      ...EMPTY,
      ...Object.fromEntries(Object.keys(EMPTY).map((k) => [k, vacancy[k] ?? ""])),
      skills: vacancy.skills.join(", "),
    });
    setEditing(vacancy.id);
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    const body = {
      ...form,
      salary_from: form.salary_from === "" ? null : Number(form.salary_from),
      salary_to: form.salary_to === "" ? null : Number(form.salary_to),
      skills: splitList(form.skills),
    };
    try {
      if (editing === "new") await api("/vacancies/my/", { method: "POST", body });
      else await api(`/vacancies/my/${editing}/`, { method: "PATCH", body });
      setEditing(null);
      setMessage("Вакансия сохранена и отправлена на модерацию.");
      load();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function toggleArchive(vacancy) {
    const action = vacancy.is_archived ? "restore" : "archive";
    if (action === "archive" && !confirm(`Перенести «${vacancy.title}» в архив? Соискатели перестанут её видеть.`)) return;
    setMessage("");
    try {
      await api(`/vacancies/my/${vacancy.id}/${action}/`, { method: "POST" });
      setMessage(action === "archive" ? "Вакансия перенесена в архив." : "Вакансия восстановлена.");
      load();
    } catch (err) {
      setLoadError(errorText(err));
    }
  }

  const set = (field) => (e) =>
    setForm({ ...form, [field]: e.target.type === "checkbox" ? e.target.checked : e.target.value });

  if (loadError) return <ErrorState message={loadError} onRetry={load} />;
  if (!data) return <Loading />;

  if (hasCompany === false) {
    return (
      <section className="card">
        <h2>Мои вакансии</h2>
        <p>Вакансии публикуются от имени компании. Сначала заполните профиль компании.</p>
        <Link to="/company" className="btn">
          Создать профиль компании
        </Link>
      </section>
    );
  }

  if (editing !== null) {
    return (
      <form className="card" onSubmit={onSubmit}>
        <h2>{editing === "new" ? "Новая вакансия" : "Редактирование вакансии"}</h2>
        <label>
          Должность *
          <input required maxLength={200} value={form.title} onChange={set("title")} />
        </label>
        <label>
          Описание *
          <textarea required rows={6} value={form.description} onChange={set("description")} />
        </label>
        <div className="grid2">
          <label>
            Город *
            <input required maxLength={100} value={form.city} onChange={set("city")} />
          </label>
          <label className="checkbox">
            <input type="checkbox" checked={form.is_internship} onChange={set("is_internship")} />
            Это стажировка
          </label>
          <label>
            Зарплата от, сом
            <input type="number" min={0} value={form.salary_from} onChange={set("salary_from")} />
          </label>
          <label>
            Зарплата до, сом
            <input type="number" min={0} value={form.salary_to} onChange={set("salary_to")} />
          </label>
          <Select label="Опыт" value={form.experience} onChange={set("experience")} options={EXPERIENCE} />
          <Select
            label="Тип занятости"
            value={form.employment_type}
            onChange={set("employment_type")}
            options={EMPLOYMENT_TYPE}
          />
          <Select label="График" value={form.schedule} onChange={set("schedule")} options={SCHEDULE} />
        </div>
        <label>
          Навыки (через запятую)
          <input placeholder="python, django, sql" value={form.skills} onChange={set("skills")} />
        </label>
        <p className="muted small">После сохранения вакансия уходит на модерацию и появится в поиске после проверки.</p>
        {error && <p className="error pre">{error}</p>}
        <div className="row">
          <button className="btn" disabled={busy}>
            {busy ? "Сохраняем…" : "Сохранить"}
          </button>
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
        <h2>Мои вакансии</h2>
        <button className="btn" onClick={() => startEdit(null)}>
          + Новая вакансия
        </button>
      </div>
      <div className="tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            className={tab === t.id ? "tab active" : "tab"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>
      {message && <p className="success">{message}</p>}
      {data.results.length === 0 && (
        <Empty>{tab === "true" ? "В архиве пока пусто." : "Пока нет активных вакансий. Создайте первую."}</Empty>
      )}
      <ul className="list">
        {data.results.map((v) => (
          <li key={v.id} className="card">
            <div className="row between">
              <div>
                <h3>{v.title}</h3>
                <p className="muted small">
                  {v.city} · {formatSalary(v.salary_from, v.salary_to)} · {SCHEDULE[v.schedule]}
                </p>
              </div>
              <span className={`badge ${v.moderation_status}`}>{MODERATION[v.moderation_status]}</span>
            </div>
            {v.moderation_status === "rejected" && v.rejection_reason && (
              <p className="error small">Причина отклонения: {v.rejection_reason}. Исправьте вакансию — она снова уйдёт на проверку.</p>
            )}
            <div className="tags">
              {v.is_internship && <span className="tag accent">Стажировка</span>}
              {v.skills.map((s) => (
                <span key={s} className="tag">
                  {s}
                </span>
              ))}
            </div>
            <div className="row">
              <button className="link" onClick={() => startEdit(v)}>
                Изменить
              </button>
              <button className={v.is_archived ? "link" : "link danger"} onClick={() => toggleArchive(v)}>
                {v.is_archived ? "Восстановить" : "В архив"}
              </button>
            </div>
          </li>
        ))}
      </ul>
      {data.count > data.results.length && (
        <p className="muted small">
          Показаны первые {data.results.length} из {data.count}.
        </p>
      )}
    </section>
  );
}
