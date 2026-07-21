function titleize(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function ResultValue({ value }: { value: unknown }) {
  if (value === null || value === undefined || value === "") return <span className="muted">Not provided</span>;
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return <p className="ai-result-text">{String(value)}</p>;
  }
  if (Array.isArray(value)) {
    return (
      <div className="ai-result-list">
        {value.map((item, index) => (
          <div className="ai-result-item" key={index}>
            {typeof item === "object" && item !== null ? (
              <div className="ai-result-object">
                {Object.entries(item).map(([key, nested]) => (
                  <div key={key}>
                    <strong>{titleize(key)}</strong>
                    <ResultValue value={nested} />
                  </div>
                ))}
              </div>
            ) : (
              <ResultValue value={item} />
            )}
          </div>
        ))}
      </div>
    );
  }
  if (typeof value === "object") {
    return (
      <div className="ai-result-object">
        {Object.entries(value).map(([key, nested]) => (
          <div key={key}>
            <strong>{titleize(key)}</strong>
            <ResultValue value={nested} />
          </div>
        ))}
      </div>
    );
  }
  return null;
}

export function AIResult({ result }: { result: unknown }) {
  if (!result) return <p className="muted">Your generated result will appear here.</p>;
  return <ResultValue value={result} />;
}
