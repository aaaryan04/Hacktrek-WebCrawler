function ScanCard({ active, color, description, icon: Icon, onClick, title }) {
  return (
    <button
      className={`scan-card ${active ? "active" : ""}`}
      onClick={onClick}
      style={{ "--accent": color }}
      type="button"
    >
      <span className="scan-icon">
        <Icon aria-hidden="true" />
      </span>
      <span className="scan-title">{title}</span>
      <span className="scan-description">{description}</span>
    </button>
  );
}

export default ScanCard;
