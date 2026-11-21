import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, errorText } from "../api.js";
import { useAuth } from "../auth.jsx";
import Pagination from "../components/Pagination.jsx";
import { Empty, ErrorState, Loading } from "../components/States.jsx";
import { ROLE } from "../labels.js";

const dateTime = (iso) => (iso ? new Date(iso).toLocaleString("ru-RU") : "—");

// A-01: пользователи платформы — просмотр и блокировка
export default function AdminUsersPage() {
  const { user: me } = useAuth();
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [q, setQ] = useState(params.get("q") || "");

  const page = Number(params.get("page") || 1);
  const query = params.toString();

  const load = useCallback(() => {
    setError("");
    api(`/admin/users/?${query}`)
      .then(setData)
      .catch((err) => setError(errorText(err)));
  }, [query]);

  useEffect(load, [load]);

  function update(changes) {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    if (!("page" in changes)) next.delete("page");
    setParams(next);
  }

  async function toggle(user) {
    setActionError("");
    let body;
    if (user.is_active) {
      const reason = prompt(`Заблокировать ${user.email}? Укажите причину (необязательно):`, "");
      if (reason === null) return;
      body = { reason };
    }
    try {
      const updated = await api(`/admin/users/${user.id}/${user.is_active ? "block" : "unblock"}/`, {
        method: "POST",
        body,
      });
      setData({ ...data, results: data.results.map((u) => (u.id === updated.id ? updated : u)) });
    } catch (err) {
      setActionError(errorText(err));
    }
  }

  return (
    <section>
      <h2>Пользователи</h2>
      <form
        className="filters-inline"
        onSubmit={(e) => {
          e.preventDefault();
          update({ q: q.trim() });
        }}
      >
        <input type="search" placeholder="Email или имя" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={params.get("role") || ""} onChange={(e) => update({ role: e.target.value })} aria-label="Роль">
          <option value="">Все роли</option>
          {Object.entries(ROLE).map(([code, label]) => (
            <option key={code} value={code}>
              {label}
            </option>
          ))}
        </select>
        <select
          value={params.get("is_active") || ""}
          onChange={(e) => update({ is_active: e.target.value })}
          aria-label="Статус"
        >
          <option value="">Все</option>
          <option value="true">Активные</option>
          <option value="false">Заблокированные</option>
        </select>
        <button className="btn">Найти</button>
      </form>

      {actionError && <p className="error">{actionError}</p>}
      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !data && <Loading />}
      {data?.results.length === 0 && <Empty>Никого не нашли.</Empty>}
      <ul className="list">
        {data?.results.map((u) => (
          <li key={u.id} className={u.is_active ? "card" : "card blocked"}>
            <div className="row between">
              <div>
                <h3>{u.full_name || u.email}</h3>
                <p className="muted small">
                  {u.email} · {ROLE[u.role]} · с {new Date(u.created_at).toLocaleDateString("ru-RU")} · последний вход:{" "}
                  {dateTime(u.last_login)}
                </p>
              </div>
              {u.is_active ? (
                <span className="badge approved">Активен</span>
              ) : (
                <span className="badge rejected">Заблокирован</span>
              )}
            </div>
            {!u.is_active && (
              <p className="small">
                Заблокирован {dateTime(u.blocked_at)}
                {u.block_reason && ` — ${u.block_reason}`}
              </p>
            )}
            {u.role !== "admin" && u.id !== me.id && (
              <button className={u.is_active ? "link danger" : "link"} onClick={() => toggle(u)}>
                {u.is_active ? "Заблокировать" : "Разблокировать"}
              </button>
            )}
          </li>
        ))}
      </ul>
      {data && <Pagination page={page} count={data.count} onChange={(n) => update({ page: String(n) })} />}
    </section>
  );
}
