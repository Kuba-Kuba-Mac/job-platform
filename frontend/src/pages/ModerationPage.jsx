import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, errorText } from "../api.js";
import Pagination from "../components/Pagination.jsx";
import { Empty, ErrorState, Loading } from "../components/States.jsx";
import { EMPLOYMENT_TYPE, EXPERIENCE, MODERATION, SCHEDULE, formatSalary } from "../labels.js";

const KINDS = { vacancies: "Вакансии", companies: "Компании" };
const STATUSES = { pending: "Ждут проверки", rejected: "Отклонённые", approved: "Одобренные", all: "Все" };

function Decision({ item, kind, onDone }) {
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function send(action, body) {
    setBusy(true);
    setError("");
    try {
      onDone(await api(`/admin/moderation/${kind}/${item.id}/${action}/`, { method: "POST", body }));
      setRejecting(false);
      setReason("");
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  if (rejecting) {
    return (
      <form
        className="decision"
        onSubmit={(e) => {
          e.preventDefault();
          send("reject", { reason });
        }}
      >
        <label>
          Причина отклонения (её увидит работодатель) *
          <textarea required maxLength={500} rows={2} value={reason} onChange={(e) => setReason(e.target.value)} />
        </label>
        {error && <p className="error pre">{error}</p>}
        <div className="row">
          <button className="btn danger" disabled={busy}>
            Отклонить
          </button>
          <button type="button" className="link" onClick={() => setRejecting(false)}>
            Отмена
          </button>
        </div>
      </form>
    );
  }

  return (
    <div className="decision">
      {error && <p className="error pre">{error}</p>}
      <div className="row">
        {item.moderation_status !== "approved" && (
          <button className="btn" disabled={busy} onClick={() => send("approve")}>
            Одобрить
          </button>
        )}
        {item.moderation_status !== "rejected" && (
          <button className="btn secondary" disabled={busy} onClick={() => setRejecting(true)}>
            Отклонить
          </button>
        )}
      </div>
    </div>
  );
}

function VacancyItem({ v }) {
  return (
    <>
      <h3>{v.title}</h3>
      <p className="muted small">
        {v.company.name}
        {v.company.moderation_status !== "approved" && ` (компания: ${MODERATION[v.company.moderation_status].toLowerCase()})`} ·{" "}
        {v.city} · {formatSalary(v.salary_from, v.salary_to)}
      </p>
      <p className="small">
        {EXPERIENCE[v.experience]} · {EMPLOYMENT_TYPE[v.employment_type]} · {SCHEDULE[v.schedule]}
        {v.is_internship && " · стажировка"}
        {v.is_archived && " · в архиве"}
      </p>
      <p className="pre clamp">{v.description}</p>
      {v.skills.length > 0 && <p className="muted small">Навыки: {v.skills.join(", ")}</p>}
    </>
  );
}

function CompanyItem({ c }) {
  return (
    <>
      <h3>{c.name}</h3>
      <p className="muted small">
        {c.owner_email}
        {c.city && ` · ${c.city}`}
        {c.website && (
          <>
            {" · "}
            <a href={c.website} target="_blank" rel="noreferrer">
              {c.website}
            </a>
          </>
        )}
      </p>
      {c.description && <p className="pre clamp">{c.description}</p>}
    </>
  );
}

// A-02: очередь модерации вакансий и компаний
export default function ModerationPage() {
  const [params, setParams] = useSearchParams();
  const kind = params.get("kind") === "companies" ? "companies" : "vacancies";
  const statusFilter = params.get("status") || "pending";
  const page = Number(params.get("page") || 1);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setError("");
    setData(null);
    api(`/admin/moderation/${kind}/?status=${statusFilter}&page=${page}`)
      .then(setData)
      .catch((err) => setError(errorText(err)));
  }, [kind, statusFilter, page]);

  useEffect(load, [load]);

  const set = (changes) => setParams({ kind, status: statusFilter, ...changes });

  function onDone(updated) {
    // решённое уходит из очереди «Ждут проверки», в остальных фильтрах — обновляется на месте
    const results =
      statusFilter === "all" || statusFilter === updated.moderation_status
        ? data.results.map((x) => (x.id === updated.id ? updated : x))
        : data.results.filter((x) => x.id !== updated.id);
    setData({ ...data, results, count: data.count - (data.results.length - results.length) });
  }

  return (
    <section>
      <h2>Модерация</h2>
      <div className="tabs" role="tablist">
        {Object.entries(KINDS).map(([id, label]) => (
          <button key={id} role="tab" aria-selected={kind === id} className={kind === id ? "tab active" : "tab"} onClick={() => set({ kind: id, page: 1 })}>
            {label}
          </button>
        ))}
      </div>
      <div className="filters-inline">
        <select value={statusFilter} onChange={(e) => set({ status: e.target.value, page: 1 })} aria-label="Статус">
          {Object.entries(STATUSES).map(([id, label]) => (
            <option key={id} value={id}>
              {label}
            </option>
          ))}
        </select>
        {data && <span className="muted small">Найдено: {data.count}</span>}
      </div>
      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !data && <Loading />}
      {data?.results.length === 0 && <Empty>{statusFilter === "pending" ? "Очередь пуста — всё проверено." : "Ничего нет."}</Empty>}
      <ul className="list">
        {data?.results.map((item) => (
          <li key={item.id} className="card">
            <div className="row between">
              <span className={`badge ${item.moderation_status}`}>{MODERATION[item.moderation_status]}</span>
              <span className="muted small">от {new Date(item.created_at).toLocaleDateString("ru-RU")}</span>
            </div>
            {kind === "vacancies" ? <VacancyItem v={item} /> : <CompanyItem c={item} />}
            {item.rejection_reason && <p className="error small">Причина отклонения: {item.rejection_reason}</p>}
            <Decision item={item} kind={kind} onDone={onDone} />
          </li>
        ))}
      </ul>
      {data && <Pagination page={page} count={data.count} onChange={(n) => set({ page: n })} />}
    </section>
  );
}
