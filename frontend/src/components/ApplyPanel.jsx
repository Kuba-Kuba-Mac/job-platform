import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, errorText } from "../api.js";
import { SEEKER_STATUS } from "../labels.js";

const MAX_LETTER = 3000;

// S-04: отклик на вакансию — выбор своего резюме и сопроводительное письмо
export default function ApplyPanel({ vacancy, onApplied }) {
  const [open, setOpen] = useState(false);
  const [resumes, setResumes] = useState(null);
  const [form, setForm] = useState({ resume_id: "", cover_letter: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open || resumes) return;
    api("/resumes/")
      .then((data) => {
        setResumes(data.results);
        if (data.results.length) setForm((f) => ({ ...f, resume_id: String(data.results[0].id) }));
      })
      .catch((err) => setError(errorText(err)));
  }, [open, resumes]);

  if (vacancy.application_status) {
    return (
      <p className="applied">
        Вы откликнулись · статус: <strong>{SEEKER_STATUS[vacancy.application_status]}</strong> ·{" "}
        <Link to="/applications">Мои отклики</Link>
      </p>
    );
  }

  if (!open) {
    return (
      <button className="btn" onClick={() => setOpen(true)}>
        Откликнуться
      </button>
    );
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const data = await api("/applications/", {
        method: "POST",
        body: { vacancy_id: vacancy.id, resume_id: Number(form.resume_id), cover_letter: form.cover_letter },
      });
      onApplied(data.status);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  if (resumes && resumes.length === 0) {
    return (
      <div className="card inset">
        <p>Чтобы откликнуться, сначала создайте резюме — работодатель увидит его вместе с откликом.</p>
        <Link to="/resumes" className="btn">
          Создать резюме
        </Link>
      </div>
    );
  }

  return (
    <form className="card inset" onSubmit={onSubmit}>
      <h3>Отклик на вакансию</h3>
      {!resumes && !error && <p className="muted">Загружаем ваши резюме…</p>}
      {resumes && (
        <>
          <label>
            Резюме *
            <select required value={form.resume_id} onChange={(e) => setForm({ ...form, resume_id: e.target.value })}>
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            Сопроводительное письмо
            <textarea
              rows={5}
              maxLength={MAX_LETTER}
              placeholder="Пара предложений о том, почему вам интересна эта вакансия"
              value={form.cover_letter}
              onChange={(e) => setForm({ ...form, cover_letter: e.target.value })}
            />
            <span className="small muted">
              {form.cover_letter.length} / {MAX_LETTER}
            </span>
          </label>
        </>
      )}
      {error && <p className="error pre">{error}</p>}
      <div className="row">
        <button className="btn" disabled={busy || !resumes}>
          {busy ? "Отправляем…" : "Отправить отклик"}
        </button>
        <button type="button" className="link" onClick={() => setOpen(false)}>
          Отмена
        </button>
      </div>
    </form>
  );
}
