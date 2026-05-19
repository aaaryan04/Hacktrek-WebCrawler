import {
  FaShieldAlt,
  FaWpforms,
  FaRobot,
  FaSitemap,
  FaCode
}
from "react-icons/fa";

function ScanCard({
  title,
  description,
  color,
  onClick
}) {

  // ============================================
  // ICON SELECTION
  // ============================================

  let icon;

  if (title === "Header Scan") {

    icon = <FaShieldAlt size={40} />;

  } else if (title === "Form Extract") {

    icon = <FaWpforms size={40} />;

  } else if (title === "Tech Detect") {

    icon = <FaCode size={40} />;

  } else if (title === "robots.txt") {

    icon = <FaRobot size={40} />;

  } else if (title === "Sitemap") {

    icon = <FaSitemap size={40} />;

  }

  return (

    <div
      className="scan-card"
      onClick={onClick}

      style={{
        border: `1px solid ${color}`
      }}
    >

      {/* ICON */}

      <div
        style={{
          color,
          marginBottom: "20px"
        }}
      >

        {icon}

      </div>

      {/* TITLE */}

      <h2 style={{ color }}>
        {title}
      </h2>

      {/* DESCRIPTION */}

      <p>
        {description}
      </p>

    </div>
  );
}

export default ScanCard;