import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, errorText } from "../api.js";
import { useAuth } from "../auth.jsx";

// S-06: «В избранное». Гостя ведём на вход, работодателю и администратору кнопка не нужна.
export default function FavoriteButton({ vacancy, onChange }) {
  const { user } = useAuth();
  const location = useLocation();
  const [favoriteId, setFavoriteId] = useState(vacancy.favorite_id ?? null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  if (!user) {
    return (
      <Link
        to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`}
        className="fav"
        title="Войдите, чтобы сохранять вакансии"
        aria-label="В избранное (нужен вход)"
      >
        ☆
      </Link>
    );
  }
  if (user.role !== "seeker") return null;

  async function toggle() {
    setBusy(true);
    setError("");
    try {
      if (favoriteId) {
        await api(`/favorites/${favoriteId}/`, { method: "DELETE" });
        setFavoriteId(null);
        onChange?.(null);
      } else {
        const data = await api("/favorites/", { method: "POST", body: { vacancy_id: vacancy.id } });
        setFavoriteId(data.id);
        onChange?.(data.id);
      }
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  const label = favoriteId ? "Убрать из избранного" : "В избранное";
  return (
    <span className="fav-wrap">
      <button
        type="button"
        className={favoriteId ? "fav on" : "fav"}
        onClick={toggle}
        disabled={busy}
        aria-pressed={Boolean(favoriteId)}
        aria-label={label}
        title={label}
      >
        {favoriteId ? "★" : "☆"}
      </button>
      {error && <span className="error small">{error}</span>}
    </span>
  );
}
