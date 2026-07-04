function StatsCard({ title, value }) {
  return (
    <article className="stats-card">
      <strong>{value}</strong>
      <span>{title}</span>
    </article>
  );
}

export default StatsCard;
