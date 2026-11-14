// F-03: индикатор надёжности пароля. Это только подсказка —
// окончательная проверка выполняется на сервере (password_validation).
const RULES = [
  { id: "length", label: "Минимум 8 символов", test: (p) => p.length >= 8 },
  { id: "letters", label: "Есть буквы", test: (p) => /\p{L}/u.test(p) },
  { id: "digits", label: "Есть цифры", test: (p) => /\d/.test(p) },
  { id: "not-numeric", label: "Не только цифры", test: (p) => p.length > 0 && !/^\d+$/.test(p) },
  { id: "strong", label: "Есть заглавная буква или спецсимвол", test: (p) => /\p{Lu}/u.test(p) || /[^\p{L}\d\s]/u.test(p) },
];

const LEVELS = {
  weak: { label: "слабый", bars: 1 },
  medium: { label: "средний", bars: 2 },
  strong: { label: "надёжный", bars: 3 },
};

export function passwordStrength(password) {
  const passed = Object.fromEntries(RULES.map((r) => [r.id, r.test(password)]));
  const basic = ["length", "letters", "digits", "not-numeric"].every((id) => passed[id]);
  const level = !basic ? "weak" : passed.strong ? "strong" : "medium";
  return { passed, level };
}

export default function PasswordStrength({ password }) {
  const { passed, level } = passwordStrength(password);
  const empty = password.length === 0;

  return (
    <div className="strength" aria-live="polite">
      <div className="row between">
        <div className={`strength-bar ${empty ? "" : level}`}>
          {[1, 2, 3].map((i) => (
            <span key={i} className={!empty && i <= LEVELS[level].bars ? "on" : ""} />
          ))}
        </div>
        <span className="small muted">
          Надёжность: <strong className={empty ? "" : `strength-label ${level}`}>{empty ? "—" : LEVELS[level].label}</strong>
        </span>
      </div>
      <ul className="rules">
        {RULES.map((rule) => (
          <li key={rule.id} className={passed[rule.id] ? "ok" : ""}>
            <span aria-hidden="true">{passed[rule.id] ? "✓" : "○"}</span> {rule.label}
          </li>
        ))}
      </ul>
    </div>
  );
}
