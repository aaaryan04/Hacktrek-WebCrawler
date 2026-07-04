export const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"];

export const SEVERITY_COLORS = {
  critical: "#f43f5e",
  high: "#f97316",
  medium: "#facc15",
  low: "#38bdf8",
  info: "#5eead4"
};

export function getSeverityCounts(findings = []) {
  return SEVERITY_ORDER.reduce((counts, severity) => {
    counts[severity] = findings.filter(
      (finding) => finding.severity?.toLowerCase() === severity
    ).length;
    return counts;
  }, {});
}

export function riskLevelClass(level = "") {
  const value = level.toLowerCase();
  if (value.includes("critical")) return "critical";
  if (value.includes("high")) return "high";
  if (value.includes("moderate") || value.includes("medium")) return "moderate";
  return "low";
}

export function formatTimestamp(value) {
  if (!value) return "";
  try {
    return new Date(value).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  } catch {
    return "";
  }
}

export function normalizeLogLines(payload) {
  if (!payload) return [];

  if (Array.isArray(payload)) {
    return payload.map(String);
  }

  if (Array.isArray(payload.logs)) {
    return payload.logs.map(String);
  }

  if (Array.isArray(payload.lines)) {
    return payload.lines.map(String);
  }

  if (typeof payload.content === "string") {
    return payload.content.split("\n").filter(Boolean);
  }

  if (typeof payload.logs === "string") {
    return payload.logs.split("\n").filter(Boolean);
  }

  return [];
}
