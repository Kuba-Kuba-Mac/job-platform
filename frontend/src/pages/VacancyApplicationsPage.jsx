import { useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api, errorText } from "../api.js";
import Pagination from "../components/Pagination.jsx";
import { Empty, ErrorState, Loading } from "../components/States.jsx";
import { EMPLOYER_STATUS } from "../labels.js";

const FILTERS = [["", "Все"], ...Object.entries(EMPLOYER_STATUS)];

// E-03: отклики на вакансию работодателя
export default function VacancyApplicationsPage() {
  const { id } = useParams();
  const [params, setParams] = useSearchParams();
  const statusFilter = params.get("status") || "";
  const page = Number(params.get("page") || 1);
  const [vacancy, setVacancy] = useState(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setError("");
    setData(null);
    const query = new URLSearchParams({ page: String(page), ...(statusFilter && { status: statusFilter }) });
    Promise.all([api(`/vacancies/my/${id}/`), api(`/vacancies/my/${id}/applications/?${query}`)])
      .then(([v, list]) => {
        setVacancy(v);
        setData(list);
      })
      .catch((err) => setError(err.status === 404 ? "Вакансия не найдена." : errorText(err)));
  }, [id, page, statusFilter]);

  useEffect(load, [load]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <Loading />;

  return (
    <section>
      <Link to="/vacancies/my" className="small">
        ← Мои вакансии
      </Link>
      <h2>Отклики: {vacancy.title}</h2>
      <p className="muted small">
        Всего {vacancy.applications_count}, новых {vacancy.new_applications_count}
      </p>
      <div className="tabs" role="tablist">
        {FILTERS.map(([value, label]) => (
          <button
            key={value || "all"}
            role="tab"
            aria-selected={statusFilter === value}
            className={statusFilter === value ? "tab active" : "tab"}
            onClick={() => setParams(value ? { status: value } : {})}
          >
            {label}
          </button>
        ))}
      </div>
      {data.results.length === 0 && (
        <Empty>{statusFilter ? "Откликов с таким статусом нет." : "На эту вакансию пока никто не откликнулся."}</Empty>
      )}
      <ul className="list">
        {data.results.map((a) => (
          <li key={a.id} className="card">
            <div className="row between">
              <div>
                <h3>
                  <Link to={`/employer/applications/${a.id}`}>{a.seeker.full_name || "Кандидат"}</Link>
                </h3>
                <p className="muted small">
                  {a.resume ? a.resume.title : "резюме удалено"}
                  {a.seeker.city && ` · ${a.seeker.city}`} · {new Date(a.created_at).toLocaleDateString("ru-RU")}
                </p>
              </div>
              <span className={`badge ${a.status}`}>{EMPLOYER_STATUS[a.status]}</span>
            </div>
            {a.cover_letter && <p className="small clamp">{a.cover_letter}</p>}
            <Link to={`/employer/applications/${a.id}`} className="small">
              Открыть резюме →
            </Link>
          </li>
        ))}
      </ul>
      <Pagination
        page={page}
        count={data.count}
        onChange={(n) => setParams({ ...(statusFilter && { status: statusFilter }), page: String(n) })}
      />
    </section>
  );
}
