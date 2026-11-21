import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, errorText } from "../api.js";
import Pagination from "../components/Pagination.jsx";
import { Empty, ErrorState, Loading } from "../components/States.jsx";
import VacancyCard from "../components/VacancyCard.jsx";
import { EMPLOYMENT_TYPE, EXPERIENCE, SCHEDULE } from "../labels.js";

const MULTI = [
  ["experience", "Опыт", EXPERIENCE],
  ["employment_type", "Занятость", EMPLOYMENT_TYPE],
  ["schedule", "График", SCHEDULE],
];

function plural(n, one, few, many) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}

// S-02: поиск вакансий. Все фильтры живут в URL — ссылкой на поиск можно поделиться.
export default function SearchPage() {
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [cities, setCities] = useState([]);
  const [text, setText] = useState(params.get("q") || "");
  const [salary, setSalary] = useState(params.get("salary") || "");

  const query = params.toString();
  const page = Number(params.get("page") || 1);

  const load = useCallback(() => {
    setError("");
    setData(null);
    api(`/vacancies/?${query}`)
      .then(setData)
      .catch((err) => setError(errorText(err)));
  }, [query]);

  useEffect(load, [load]);

  useEffect(() => {
    api("/vacancies/cities/")
      .then(setCities)
      .catch(() => setCities([]));
  }, []);

  // при переходе «назад» в браузере поля ввода догоняют URL
  useEffect(() => {
    setText(params.get("q") || "");
    setSalary(params.get("salary") || "");
  }, [params]);

  function update(changes) {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    if (!("page" in changes)) next.delete("page");
    setParams(next);
  }

  function toggle(name, value) {
    const current = (params.get(name) || "").split(",").filter(Boolean);
    const next = current.includes(value) ? current.filter((x) => x !== value) : [...current, value];
    update({ [name]: next.join(",") });
  }

  const active = (name) => (params.get(name) || "").split(",").filter(Boolean);
  const hasFilters = [...params.keys()].some((k) => k !== "page" && k !== "ordering");

  return (
    <section className="search">
      <form
        className="search-bar"
        role="search"
        onSubmit={(e) => {
          e.preventDefault();
          update({ q: text.trim(), salary: salary.trim() });
        }}
      >
        <input
          type="search"
          placeholder="Должность, навык или компания"
          aria-label="Поиск по тексту"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button className="btn">Найти</button>
      </form>

      <div className="search-layout">
        <details className="filters card" open={window.matchMedia?.("(min-width: 721px)").matches}>
          <summary>Фильтры{hasFilters && " •"}</summary>
          <label>
            Город
            <select value={params.get("city") || ""} onChange={(e) => update({ city: e.target.value })}>
              <option value="">Любой</option>
              {cities.map((c) => (
                <option key={c.city} value={c.city}>
                  {c.city} ({c.count})
                </option>
              ))}
            </select>
          </label>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              update({ salary: salary.trim() });
            }}
          >
            <label>
              Зарплата от, сом
              <div className="row nowrap">
                <input type="number" min={0} step={1000} value={salary} onChange={(e) => setSalary(e.target.value)} />
                <button className="btn small-btn">OK</button>
              </div>
            </label>
          </form>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={params.get("internship") === "true"}
              onChange={(e) => update({ internship: e.target.checked ? "true" : "" })}
            />
            Только стажировки
          </label>
          {MULTI.map(([name, title, options]) => (
            <fieldset key={name}>
              <legend>{title}</legend>
              {Object.entries(options).map(([code, label]) => (
                <label key={code} className="checkbox">
                  <input type="checkbox" checked={active(name).includes(code)} onChange={() => toggle(name, code)} />
                  {label}
                </label>
              ))}
            </fieldset>
          ))}
          {hasFilters && (
            <button
              type="button"
              className="link"
              onClick={() => {
                setText("");
                setSalary("");
                setParams({});
              }}
            >
              Сбросить фильтры
            </button>
          )}
        </details>

        <div className="results">
          <div className="row between">
            <p className="muted">
              {data
                ? `Найдено ${data.count} ${plural(data.count, "вакансия", "вакансии", "вакансий")}`
                : "Ищем…"}
            </p>
            <select
              aria-label="Сортировка"
              className="ordering"
              value={params.get("ordering") || "new"}
              onChange={(e) => update({ ordering: e.target.value === "new" ? "" : e.target.value })}
            >
              <option value="new">Сначала новые</option>
              <option value="salary">По зарплате</option>
            </select>
          </div>
          {error && <ErrorState message={error} onRetry={load} />}
          {!error && !data && <Loading />}
          {data?.results.length === 0 && (
            <Empty>Ничего не нашлось. Попробуйте убрать часть фильтров или изменить запрос.</Empty>
          )}
          <ul className="list">
            {data?.results.map((v) => (
              <VacancyCard key={v.id} vacancy={v} />
            ))}
          </ul>
          {data && (
            <Pagination
              page={page}
              count={data.count}
              onChange={(n) => {
                update({ page: String(n) });
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
            />
          )}
        </div>
      </div>
    </section>
  );
}
