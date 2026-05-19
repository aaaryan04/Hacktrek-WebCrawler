function StatsCard({
  title,
  value,
  color
}) {

  return (

    <div className="stats-card">

      <h2 style={{ color }}>
        {value}
      </h2>

      <p>
        {title}
      </p>

    </div>
  );
}

export default StatsCard;