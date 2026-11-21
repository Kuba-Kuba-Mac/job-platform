import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, errorText } from "../api.js";
import { useAuth } from "../auth.jsx";
import { Empty, ErrorState, Loading } from "../components/States.jsx";
import VacancyCard from "../components/VacancyCard.jsx";

const FRESH_COUNT = 6;

// E-02: последние опубликованные вакансии; полный поиск — на странице /vacancies (S-02)
function FreshVacancies() {
  const [vacancies, setVacancies] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setError("");
    api("/vacancies/")
      .then((data) => setVacancies(data.results.slice(0, FRESH_COUNT)))
      .catch((err) => setError(errorText(err)));
  }, []);

  useEffect(load, [load]);

  return (
    <section>
      <div className="row between">
        <h2>Свежие вакансии</h2>
        <Link to="/vacancies">Все вакансии и фильтры →</Link>
      </div>
      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !vacancies && <Loading />}
      {vacancies?.length === 0 && <Empty>Пока нет опубликованных вакансий.</Empty>}
      <ul className="vacancy-grid">
        {vacancies?.map((v) => (
          <VacancyCard key={v.id} vacancy={v} />
        ))}
      </ul>
    </section>
  );
}

export default function HomePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  return (
    <>
      <section className="hero">
        <h1>Стажировки и первая работа в Кыргызстане</h1>
        <p className="muted">
          Студенты и выпускники создают резюме и портфолио и откликаются на вакансии, компании публикуют вакансии и
          приглашают кандидатов.
        </p>
        {user?.role !== "employer" && (
          <form
            className="search-bar"
            role="search"
            onSubmit={(e) => {
              e.preventDefault();
              const q = new FormData(e.currentTarget).get("q").trim();
              navigate(q ? `/vacancies?q=${encodeURIComponent(q)}` : "/vacancies");
            }}
          >
            <input name="q" type="search" placeholder="Должность, навык или компания" aria-label="Поиск вакансий" />
            <button className="btn">Найти вакансии</button>
          </form>
        )}
        {!user && (
          <div className="row">
            <Link to="/register" className="btn">
              Создать аккаунт
            </Link>
            <Link to="/login">Уже есть аккаунт</Link>
          </div>
        )}
        {user?.role === "employer" && (
          <Link to="/vacancies/my" className="btn">
            Мои вакансии
          </Link>
        )}
      </section>
      <FreshVacancies />
    </>
  );
}
