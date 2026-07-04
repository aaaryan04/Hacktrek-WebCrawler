import { FaCheckCircle, FaExclamationTriangle, FaInfoCircle, FaTimes } from "react-icons/fa";

const ICONS = {
  success: FaCheckCircle,
  error: FaExclamationTriangle,
  info: FaInfoCircle
};

function ToastStack({ toasts, onDismiss }) {
  if (!toasts.length) {
    return null;
  }

  return (
    <div className="toast-stack" role="region" aria-label="Notifications" aria-live="polite">
      {toasts.map((toast) => {
        const Icon = ICONS[toast.tone] || FaInfoCircle;
        return (
          <div className={`toast toast-${toast.tone}`} key={toast.id} role="status">
            <Icon aria-hidden="true" className="toast-icon" />
            <p>{toast.message}</p>
            <button
              type="button"
              className="toast-close"
              onClick={() => onDismiss(toast.id)}
              aria-label="Dismiss notification"
            >
              <FaTimes aria-hidden="true" />
            </button>
          </div>
        );
      })}
    </div>
  );
}

export default ToastStack;
