import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, errorText } from "../api.js";
import { Empty, ErrorState, Loading } from "../components/States.jsx";

const LINKS = { about: "", github_url: "", portfolio_url: "" };
const EMPTY_PROJECT = { title: "", description: "", url: "", technologies: "" };
const pick = (obj, shape) => Object.fromEntries(Object.keys(shape).map((k) => [k, obj[k] ?? ""]));

function ProjectForm({ initial, onSave, onCancel }) {
  const [form, setForm] = useState(initial);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await onSave(form);
    } catch (err) {
      setError(errorText(err));
      setBusy(false);
    }
  }

  return (
    <form className="card inset" onSubmit={onSubmit}>
      <div className="grid2">
        <label>
          Название *
          <input required maxLength={200} value={form.title} onChange={set("title")} />
        </label>
        <label>
          Технологии
          <input maxLength={255} placeholder="Python, Django, PostgreSQL" value={form.technologies} onChange={set("technologies")} />
        </label>
      </div>
      <label>
        Ссылка
        <input type="url" placeholder="https://github.com/…" value={form.url} onChange={set("url")} />
      </label>
      <label>
        Описание
        <textarea rows={3} value={form.description} onChange={set("description")} />
      </label>
      {error && <p className="error pre">{error}</p>}
      <div className="row">
        <button className="btn" disabled={busy}>
          {busy ? "Сохраняем…" : "Сохранить проект"}
        </button>
        <button type="button" className="link" onClick={onCancel}>
          Отмена
        </button>
      </div>
    </form>
  );
}

// S-08: профиль студента — ссылки на GitHub и портфолио, проекты
export default function PortfolioPage() {
  const [profile, setProfile] = useState(null);
  const [links, setLinks] = useState(LINKS);
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState(null); // null, "new" или id проекта

  const load = useCallback(() => {
    setLoadError("");
    return api("/profiles/me/")
      .then((data) => {
        setProfile(data);
        setLinks(pick(data, LINKS));
      })
      .catch((err) => setLoadError(errorText(err)));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loadError) return <ErrorState message={loadError} onRetry={load} />;
  if (!profile) return <Loading />;

  async function saveLinks(e) {
    e.preventDefault();
    setError("");
    setMessage("");
    setBusy(true);
    try {
      const data = await api("/profiles/me/", { method: "PATCH", body: links });
      setProfile(data);
      setLinks(pick(data, LINKS));
      setMessage("Сохранено.");
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function saveProject(form) {
    if (editing === "new") await api("/profiles/me/projects/", { method: "POST", body: form });
    else await api(`/profiles/me/projects/${editing}/`, { method: "PATCH", body: form });
    setEditing(null);
    await load();
  }

  async function deleteProject(project) {
    if (!confirm(`Удалить проект «${project.title}»?`)) return;
    try {
      await api(`/profiles/me/projects/${project.id}/`, { method: "DELETE" });
      await load();
    } catch (err) {
      setLoadError(errorText(err));
    }
  }

  const set = (field) => (e) => setLinks({ ...links, [field]: e.target.value });

  return (
    <div className="stack">
      <form className="card" onSubmit={saveLinks}>
        <div className="row between">
          <h2>Проекты и GitHub</h2>
          <Link to={`/seekers/${profile.user_id}`} className="small">
            Как видят работодатели →
          </Link>
        </div>
        {!profile.full_name && (
          <p className="muted small">
            Укажите имя и город в <Link to="/profile">профиле</Link> — они показываются работодателям.
          </p>
        )}
        <label>
          О себе
          <textarea rows={3} value={links.about} onChange={set("about")} />
        </label>
        <div className="grid2">
          <label>
            GitHub
            <input type="url" placeholder="https://github.com/username" value={links.github_url} onChange={set("github_url")} />
          </label>
          <label>
            Портфолио
            <input type="url" placeholder="https://" value={links.portfolio_url} onChange={set("portfolio_url")} />
          </label>
        </div>
        <div>
          <p className="muted small">Навыки из ваших резюме:</p>
          {profile.skills.length ? (
            <div className="tags">
              {profile.skills.map((s) => (
                <span key={s} className="tag">
                  {s}
                </span>
              ))}
            </div>
          ) : (
            <p className="muted small">
              Пока нет — добавьте навыки в <Link to="/resumes">резюме</Link>.
            </p>
          )}
        </div>
        {error && <p className="error pre">{error}</p>}
        {message && <p className="success">{message}</p>}
        <button className="btn" disabled={busy}>
          {busy ? "Сохраняем…" : "Сохранить"}
        </button>
      </form>

      <section>
        <div className="row between">
          <h2>Мои проекты</h2>
          {editing === null && profile.projects.length < 20 && (
            <button className="btn" onClick={() => setEditing("new")}>
              + Добавить проект
            </button>
          )}
        </div>
        {editing === "new" && (
          <ProjectForm initial={EMPTY_PROJECT} onSave={saveProject} onCancel={() => setEditing(null)} />
        )}
        {profile.projects.length === 0 && editing !== "new" && (
          <Empty>Добавьте учебные или pet-проекты — работодатели смотрят на них в первую очередь.</Empty>
        )}
        <ul className="list">
          {profile.projects.map((p) =>
            editing === p.id ? (
              <li key={p.id}>
                <ProjectForm initial={pick(p, EMPTY_PROJECT)} onSave={saveProject} onCancel={() => setEditing(null)} />
              </li>
            ) : (
              <li key={p.id} className="card">
                <div className="row between">
                  <h3>{p.url ? <a href={p.url} target="_blank" rel="noreferrer">{p.title}</a> : p.title}</h3>
                  <div className="row">
                    <button className="link" onClick={() => setEditing(p.id)}>
                      Изменить
                    </button>
                    <button className="link danger" onClick={() => deleteProject(p)}>
                      Удалить
                    </button>
                  </div>
                </div>
                {p.description && <p className="pre">{p.description}</p>}
                {p.technologies && <p className="muted small">{p.technologies}</p>}
              </li>
            ),
          )}
        </ul>
      </section>
    </div>
  );
}
