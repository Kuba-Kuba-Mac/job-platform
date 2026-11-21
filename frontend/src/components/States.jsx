// Общие состояния страниц: загрузка, ошибка, пустой список
export function Loading({ text = "Загрузка…" }) {
  return (
    <p className="muted state" role="status">
      {text}
    </p>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="state error-state" role="alert">
      <p className="error pre">{message}</p>
      {onRetry && (
        <button type="button" className="link" onClick={onRetry}>
          Повторить
        </button>
      )}
    </div>
  );
}

export function Empty({ children }) {
  return <p className="muted state empty">{children}</p>;
}
