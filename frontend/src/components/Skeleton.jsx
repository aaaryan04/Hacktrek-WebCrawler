/**
 * Loading skeleton for the result panel while a scan is in flight.
 */
function ResultSkeleton() {
  return (
    <div className="skeleton-report" aria-hidden="true">
      <div className="skeleton-overview">
        <div className="skeleton-block skeleton-gauge" />
        <div className="skeleton-lines">
          <span className="skeleton-line w-70" />
          <span className="skeleton-line w-90" />
          <span className="skeleton-line w-50" />
          <span className="skeleton-line w-80" />
        </div>
      </div>
      <div className="skeleton-cards">
        <div className="skeleton-block skeleton-card" />
        <div className="skeleton-block skeleton-card" />
        <div className="skeleton-block skeleton-card" />
      </div>
    </div>
  );
}

export default ResultSkeleton;
