import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, errorText } from "../api.js";
import FavoriteButton from "../components/FavoriteButton.jsx";
import Pagination from "../components/Pagination.jsx";
import { Empty, ErrorState, Loading } from "../components/States.jsx";
import VacancyCard from "../components/VacancyCard.jsx";

// S-06: избранные вакансии соискателя
export default function FavoritesPage() {
  const [params, setParams] = useSearchParams();
  const page = Number(params.get("page") || 1);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setError("");
    api(`/favorites/?page=${page}`)
      .then(setData)
      .catch((err) => setError(errorText(err)));
  }, [page]);

  useEffect(load, [load]);

  // убранная вакансия сразу исчезает из списка
  const remove = (id) =>
    setData((d) => ({ ...d, count: d.count - 1, results: d.results.filter((f) => f.id !== id) }));

  return (
    <section>
      <h2>Избранное</h2>
      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !data && <Loading />}
      {data?.results.length === 0 && (
        <Empty>
          Здесь будут вакансии, отмеченные звёздочкой. <Link to="/vacancies">Перейти к поиску</Link>
        </Empty>
      )}
      <ul className="list">
        {data?.results.map((f) =>
          f.is_available ? (
            <VacancyCard
              key={f.id}
              vacancy={{ ...f.vacancy, favorite_id: f.id }}
              actions={<FavoriteButton vacancy={{ ...f.vacancy, favorite_id: f.id }} onChange={(id) => !id && remove(f.id)} />}
            />
          ) : (
            <li key={f.id} className="card unavailable">
              <div className="row between">
                <div>
                  <h3>{f.vacancy.title}</h3>
                  <p className="muted small">
                    {f.vacancy.company.name} · вакансия снята с публикации
                  </p>
                </div>
                <FavoriteButton vacancy={{ ...f.vacancy, favorite_id: f.id }} onChange={(id) => !id && remove(f.id)} />
              </div>
            </li>
          ),
        )}
      </ul>
      {data && <Pagination page={page} count={data.count} onChange={(n) => setParams({ page: String(n) })} />}
    </section>
  );
}
