import { Component } from "react";

/** Catches unexpected rendering crashes anywhere below it in the tree.
 * Without this, a single unhandled error in any page shows the user a
 * blank white screen with nothing on it (and the real error only in
 * the browser console, which a normal user will never open). This
 * shows a friendly, on-brand message instead and lets them recover
 * without losing their login session. */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    // Logged for developers only - never shown in the UI.
    console.error("Unhandled UI error:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
            padding: 32,
            gap: 14,
            fontFamily: "var(--font-body, sans-serif)",
          }}
        >
          <h2 style={{ margin: 0 }}>Something went wrong</h2>
          <p style={{ color: "#64748B", maxWidth: 360 }}>
            This page ran into an unexpected problem. Your account is still
            signed in - reloading usually fixes it.
          </p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => window.location.reload()}
          >
            Reload page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
