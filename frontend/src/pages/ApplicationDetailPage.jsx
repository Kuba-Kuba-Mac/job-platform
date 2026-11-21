import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, errorText } from "../api.js";
import { ErrorState, Loading } from "../components/States.jsx";
import { EMPLOYER_STATUS } from "../labels.js";

function Field({ title, children }) {
  if (!children) return null;
  return (
    <div>
      <h3>{title}</h3>
      <p className="pre">{children}</p>
    </div>
  );
}

// E-03: отклик и полное резюме кандидата
export default function ApplicationDetailPage() {
  const { id } = useParams();
  const [application, setApplication] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setError("");
    api(`/employer/applications/${id}/`)
      .then(setApplication)
      .catch((err) => setError(err.status === 404 ? "Отклик не найден." : errorText(err)));
  }, [id]);

  useEffect(load, [load]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!application) return <Loading />;

  const a = application;
  const r = a.resume;

  return (
    <article className="stack">
      <Link to={`/vacancies/my/${a.vacancy.id}/applications`} className="small">
        ← Отклики на «{a.vacancy.title}»
      </Link>

      <section className="card">
        <div className="row between">
          <h2>{a.seeker.full_name || r?.full_name || "Кандидат"}</h2>
          <span className={`badge ${a.status}`}>{EMPLOYER_STATUS[a.status]}</span>
        </div>
        <p className="muted small">
          Откликнулся {new Date(a.created_at).toLocaleString("ru-RU")} на «{a.vacancy.title}»
        </p>
        <Link to={`/seekers/${a.seeker.id}`}>Профиль студента: проекты и GitHub →</Link>
        <Field title="Сопроводительное письмо">{a.cover_letter || "Без сопроводительного письма."}</Field>
      </section>

      {r ? (
        <section className="card">
          <h2>Резюме: {r.title}</h2>
          <p className="muted">
            {r.full_name}
            {r.city && ` · ${r.city}`}
            {r.salary && ` · желаемая зарплата ${r.salary.toLocaleString("ru-RU")} сом`}
          </p>
          <div className="row small">
            {r.contact_email && <a href={`mailto:${r.contact_email}`}>{r.contact_email}</a>}
            {r.phone && <a href={`tel:${r.phone.replace(/[^\d+]/g, "")}`}>{r.phone}</a>}
          </div>
          {r.skills.length > 0 && (
            <div className="tags">
              {r.skills.map((s) => (
                <span key={s} className="tag">
                  {s}
                </span>
              ))}
            </div>
          )}
          <Field title="Опыт работы">{r.experience}</Field>
          <Field title="Образование">{r.education}</Field>
          <Field title="Языки">{r.languages.join(", ")}</Field>
          <Field title="О себе">{r.about}</Field>
        </section>
      ) : (
        <p className="muted">Кандидат удалил резюме, которое прикладывал к отклику.</p>
      )}
    </article>
  );
}
