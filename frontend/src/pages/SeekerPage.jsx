import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, errorText } from "../api.js";
import { Empty, ErrorState, Loading } from "../components/States.jsx";

const STATUS_TEXT = {
  403: "Профили других соискателей недоступны.",
  404: "Профиль не найден.",
};

// S-08: профиль студента глазами работодателя (без email и телефона)
export default function SeekerPage() {
  const { id } = useParams();
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setError(null);
    setProfile(null);
    api(`/profiles/${id}/`)
      .then(setProfile)
      .catch((err) => setError({ status: err.status, message: STATUS_TEXT[err.status] || errorText(err) }));
  }, [id]);

  useEffect(load, [load]);

  if (error) return <ErrorState message={error.message} onRetry={STATUS_TEXT[error.status] ? null : load} />;
  if (!profile) return <Loading />;

  return (
    <article className="stack">
      <section className="card">
        <h2>{profile.full_name || "Соискатель"}</h2>
        {profile.city && <p className="muted">{profile.city}</p>}
        {profile.about && <p className="pre">{profile.about}</p>}
        <div className="row">
          {profile.github_url && (
            <a href={profile.github_url} target="_blank" rel="noreferrer">
              GitHub
            </a>
          )}
          {profile.portfolio_url && (
            <a href={profile.portfolio_url} target="_blank" rel="noreferrer">
              Портфолио
            </a>
          )}
        </div>
        {profile.skills.length > 0 && (
          <div className="tags">
            {profile.skills.map((s) => (
              <span key={s} className="tag">
                {s}
              </span>
            ))}
          </div>
        )}
      </section>
      <section>
        <h2>Проекты</h2>
        {profile.projects.length === 0 && <Empty>Проектов пока нет.</Empty>}
        <ul className="list">
          {profile.projects.map((p) => (
            <li key={p.id} className="card">
              <h3>{p.url ? <a href={p.url} target="_blank" rel="noreferrer">{p.title}</a> : p.title}</h3>
              {p.description && <p className="pre">{p.description}</p>}
              {p.technologies && <p className="muted small">{p.technologies}</p>}
            </li>
          ))}
        </ul>
      </section>
    </article>
  );
}
