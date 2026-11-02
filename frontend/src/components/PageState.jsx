export function LoadingState() {
  return (
    <div className="page-state">
      <div className="spinner" />
      <p>Загрузка...</p>
    </div>
  );
}

export function EmptyState({ title = "Ничего не найдено", text }) {
  return (
    <div className="page-state">
      <h3>{title}</h3>
      {text && <p className="muted">{text}</p>}
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="page-state error-state">
      <h3>Не удалось загрузить данные</h3>
      <p>{message || "Попробуйте ещё раз."}</p>
      {onRetry && (
        <button className="btn" onClick={onRetry}>
          Повторить
        </button>
      )}
    </div>
  );
}