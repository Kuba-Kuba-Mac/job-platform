import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api, errorText } from "../api.js";
import { useAuth } from "../auth.jsx";
import FavoriteButton from "../components/FavoriteButton.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import { EMPLOYMENT_TYPE, EXPERIENCE, SCHEDULE, formatSalary } from "../labels.js";

// S-03: страница вакансии — полное описание и данные компании
export default function VacancyPage() {
  const { id } = useParams();
  const location = useLocation();
  const { user } = useAuth();
  const [vacancy, setVacancy] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setError(null);
    api(`/vacancies/${id}/`)
      .then(setVacancy)
      .catch((err) =>
        setError({
          status: err.status,
          message: err.status === 404 ? "Вакансия не найдена или снята с публикации." : errorText(err),
        }),
      );
  }, [id]);

  useEffect(load, [load]);

  if (error) {
    return (
      <>
        <ErrorState message={error.message} onRetry={error.status === 404 ? null : load} />
        <Link to="/vacancies">← К поиску вакансий</Link>
      </>
    );
  }
  if (!vacancy) return <Loading />;

  const v = vacancy;
  const c = v.company;
  const loginLink = `/login?next=${encodeURIComponent(location.pathname)}`;

  return (
    <article className="vacancy-page">
      <Link to="/vacancies" className="small">
        ← К поиску вакансий
      </Link>
      <section className="card">
        <div className="row between">
          <h1>{v.title}</h1>
          <FavoriteButton vacancy={v} />
        </div>
        <p className="salary big">{formatSalary(v.salary_from, v.salary_to)}</p>
        <p className="muted">
          {c.name} · {v.city}
        </p>
        <div className="tags">
          {v.is_internship && <span className="tag accent">Стажировка</span>}
          <span className="tag">{EXPERIENCE[v.experience]}</span>
          <span className="tag">{EMPLOYMENT_TYPE[v.employment_type]}</span>
          <span className="tag">{SCHEDULE[v.schedule]}</span>
        </div>
        {/* F-06: работодатель и администратор не откликаются; гостя отправляем на вход */}
        {!user && (
          <div className="row">
            <Link to={loginLink} className="btn">
              Откликнуться
            </Link>
            <span className="muted small">Нужно войти как соискатель</span>
          </div>
        )}
        <p className="muted small">Опубликована {new Date(v.created_at).toLocaleDateString("ru-RU")}</p>
      </section>

      <section className="card">
        <h2>Описание</h2>
        <p className="pre">{v.description}</p>
        {v.skills.length > 0 && (
          <>
            <h3>Навыки</h3>
            <div className="tags">
              {v.skills.map((s) => (
                <span key={s} className="tag">
                  {s}
                </span>
              ))}
            </div>
          </>
        )}
      </section>

      <section className="card">
        <div className="row">
          {c.logo && <img className="logo-preview" src={c.logo} alt="" />}
          <div>
            <h2>{c.name}</h2>
            {c.city && <p className="muted">{c.city}</p>}
          </div>
        </div>
        {c.description && <p className="pre">{c.description}</p>}
        <div className="row small">
          {c.website && (
            <a href={c.website} target="_blank" rel="noreferrer">
              Сайт компании
            </a>
          )}
          {c.contact_email && <a href={`mailto:${c.contact_email}`}>{c.contact_email}</a>}
          {c.phone && <a href={`tel:${c.phone.replace(/[^\d+]/g, "")}`}>{c.phone}</a>}
        </div>
      </section>
    </article>
  );
}
