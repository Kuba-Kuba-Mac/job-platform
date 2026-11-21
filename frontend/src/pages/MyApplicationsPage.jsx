import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, errorText } from "../api.js";
import Pagination from "../components/Pagination.jsx";
import { Empty, ErrorState, Loading } from "../components/States.jsx";
import { SEEKER_STATUS, formatSalary } from "../labels.js";

const FILTERS = [["", "Все"], ...Object.entries(SEEKER_STATUS)];
const date = (iso) => new Date(iso).toLocaleDateString("ru-RU");

// S-05: «Мои отклики» со статусами
export default function MyApplicationsPage() {
  const [params, setParams] = useSearchParams();
  const statusFilter = params.get("status") || "";
  const page = Number(params.get("page") || 1);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(
    (quiet = false) => {
      if (!quiet) setData(null);
      setError("");
      const query = new URLSearchParams({ page: String(page), ...(statusFilter && { status: statusFilter }) });
      api(`/applications/?${query}`)
        .then(setData)
        .catch((err) => setError(errorText(err)));
    },
    [page, statusFilter],
  );

  useEffect(() => load(), [load]);

  // Работодатель мог сменить статус (E-04), пока вкладка была в фоне — перечитываем при возвращении
  useEffect(() => {
    const onVisible = () => document.visibilityState === "visible" && load(true);
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, [load]);

  return (
    <section>
      <h2>Мои отклики</h2>
      <div className="tabs" role="tablist">
        {FILTERS.map(([id, label]) => (
          <button
            key={id || "all"}
            role="tab"
            aria-selected={statusFilter === id}
            className={statusFilter === id ? "tab active" : "tab"}
            onClick={() => setParams(id ? { status: id } : {})}
          >
            {label}
          </button>
        ))}
      </div>
      {error && <ErrorState message={error} onRetry={() => load()} />}
      {!error && !data && <Loading />}
      {data?.results.length === 0 && (
        <Empty>
          {statusFilter ? "С таким статусом откликов нет." : "Вы ещё никуда не откликались."}{" "}
          <Link to="/vacancies">Найти вакансию</Link>
        </Empty>
      )}
      <ul className="list">
        {data?.results.map((a) => (
          <li key={a.id} className="card">
            <div className="row between">
              <div>
                <h3>
                  <Link to={`/vacancies/${a.vacancy.id}`}>{a.vacancy.title}</Link>
                </h3>
                <p className="muted small">
                  {a.vacancy.company.name} · {a.vacancy.city} · {formatSalary(a.vacancy.salary_from, a.vacancy.salary_to)}
                </p>
              </div>
              <span className={`badge ${a.status}`}>{SEEKER_STATUS[a.status]}</span>
            </div>
            {a.status === "invited" && (
              <p className="success small">Работодатель приглашает вас — ждите связи по контактам из резюме.</p>
            )}
            <p className="small muted">
              Отправлен {date(a.created_at)}
              {a.status !== "new" && ` · статус изменён ${date(a.status_changed_at)}`} · резюме:{" "}
              {a.resume ? a.resume.title : "удалено"}
            </p>
            {a.cover_letter && (
              <details>
                <summary className="small">Сопроводительное письмо</summary>
                <p className="pre small">{a.cover_letter}</p>
              </details>
            )}
          </li>
        ))}
      </ul>
      {data && (
        <Pagination
          page={page}
          count={data.count}
          onChange={(n) => setParams({ ...(statusFilter && { status: statusFilter }), page: String(n) })}
        />
      )}
    </section>
  );
}
