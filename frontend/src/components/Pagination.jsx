// Пагинация для списков DRF (PAGE_SIZE = 20 на сервере)
export const PAGE_SIZE = 20;

export default function Pagination({ page, count, onChange, pageSize = PAGE_SIZE }) {
  const pages = Math.ceil(count / pageSize);
  if (pages <= 1) return null;

  // Номера вокруг текущей страницы + первая и последняя
  const numbers = [...new Set([1, page - 1, page, page + 1, pages])].filter((n) => n >= 1 && n <= pages);

  return (
    <nav className="pagination" aria-label="Страницы">
      <button type="button" className="page" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ← Назад
      </button>
      {numbers.map((n, i) => (
        <span key={n} className="row">
          {i > 0 && n - numbers[i - 1] > 1 && <span className="muted">…</span>}
          <button
            type="button"
            className={n === page ? "page active" : "page"}
            aria-current={n === page ? "page" : undefined}
            onClick={() => onChange(n)}
          >
            {n}
          </button>
        </span>
      ))}
      <button type="button" className="page" disabled={page >= pages} onClick={() => onChange(page + 1)}>
        Вперёд →
      </button>
    </nav>
  );
}
