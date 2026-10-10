import { useState, useEffect } from "react";
import { NavLink, Link, Outlet, useLocation } from "react-router-dom";
import { checkBackendHealth } from "./api";

export default function App() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [health, setHealth] = useState<{
    checked: boolean;
    online: boolean;
    apiUrl: string;
    isAwsDirect: boolean;
    latencyMs: number;
  }>({
    checked: false,
    online: false,
    apiUrl: "/api",
    isAwsDirect: false,
    latencyMs: 0,
  });

  useEffect(() => {
    checkBackendHealth().then((res) => {
      setHealth({
        checked: true,
        online: res.online,
        apiUrl: res.apiUrl,
        isAwsDirect: res.isAwsDirect,
        latencyMs: res.latencyMs,
      });
    });
  }, [location.pathname]);

  // Close mobile nav upon page transition
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Derive breadcrumbs based on pathname
  function getBreadcrumb() {
    const path = location.pathname;
    if (path === "/") return null;
    if (path.startsWith("/recovery") || path.startsWith("/upload")) {
      return { parent: "Intake", current: "New Device Recovery" };
    }
    if (path.startsWith("/devices/")) {
      const devId = path.split("/")[2] || "";
      const label = devId.includes("t14")
        ? "ThinkPad T14"
        : devId.includes("c9300")
        ? "Catalyst 9300"
        : "PowerEdge R740";
      return { parent: "Devices", current: `${label} (${devId})` };
    }
    if (path.startsWith("/passports")) {
      return { parent: "Security", current: "Digital Product Passports" };
    }
    if (path.startsWith("/impact")) {
      return { parent: "ESG", current: "Environmental Impact Ledger" };
    }
    if (path.startsWith("/architecture") || path.startsWith("/how-it-works")) {
      return { parent: "Cloud", current: "AWS Serverless Architecture" };
    }
    return null;
  }

  const breadcrumb = getBreadcrumb();

  return (
    <div className="app-shell">
      {/* Background Ambient Glows */}
      <div className="ambient-glow ambient-glow-top-left" aria-hidden="true" />
      <div className="ambient-glow ambient-glow-top-right" aria-hidden="true" />

      {/* Main Container */}
      <div className="app-container">
        {/* Top Header */}
        <header className="header">
          <div className="header-top-row">
            <Link to="/" className="brand" aria-label="RE:GENESIS Home">
              <div className="brand-logo-icon">
                <span className="brand-mark">RE</span>
              </div>
              <div className="brand-text-block">
                <span className="brand-name">GENESIS</span>
                <span className="brand-sub">E-Waste AI</span>
              </div>
            </Link>

            {/* Backend Connectivity Status Pill */}
            <div
              className={`header-status-pill ${
                health.checked
                  ? health.online
                    ? "status-online"
                    : "status-local"
                  : "status-checking"
              }`}
              title={`Endpoint: ${health.apiUrl} (${health.latencyMs}ms)`}
            >
              <span className="status-dot-pulse" />
              <span className="status-label">
                {!health.checked
                  ? "Probing API..."
                  : health.online
                  ? health.isAwsDirect
                    ? `AWS Cloud API (${health.latencyMs}ms)`
                    : `API Gateway Proxy (${health.latencyMs}ms)`
                  : "Local / Offline Fallback Active"}
              </span>
            </div>

            {/* Mobile Hamburger Toggle */}
            <button
              className="mobile-nav-toggle"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
            >
              <span className="hamburger-bar" />
              <span className="hamburger-bar" />
              <span className="hamburger-bar" />
            </button>
          </div>

          {/* Navigation Bar */}
          <nav
            className={`main-nav ${mobileMenuOpen ? "main-nav-mobile-open" : ""}`}
            aria-label="Main Navigation"
          >
            <div className="nav-links">
              <NavLink
                to="/"
                className={({ isActive }) =>
                  `nav-link ${isActive ? "nav-link-active" : ""}`
                }
                end
              >
                Overview
              </NavLink>
              <NavLink
                to="/recovery"
                className={({ isActive }) =>
                  `nav-link ${isActive ? "nav-link-active" : ""}`
                }
              >
                New Recovery
              </NavLink>
              <NavLink
                to="/passports"
                className={({ isActive }) =>
                  `nav-link ${isActive ? "nav-link-active" : ""}`
                }
              >
                Passports Registry
              </NavLink>
              <NavLink
                to="/impact"
                className={({ isActive }) =>
                  `nav-link ${isActive ? "nav-link-active" : ""}`
                }
              >
                Impact Ledger
              </NavLink>
              <NavLink
                to="/architecture"
                className={({ isActive }) =>
                  `nav-link ${isActive ? "nav-link-active" : ""}`
                }
              >
                AWS Architecture
              </NavLink>
            </div>

            <div className="nav-cta-wrap">
              <Link to="/recovery" className="btn btn-sm btn-primary nav-cta-btn">
                <span className="btn-icon">⚡</span>
                <span>+ Start Intake</span>
              </Link>
            </div>
          </nav>

          {/* Contextual Breadcrumb Bar */}
          {breadcrumb && (
            <div className="breadcrumb-bar" aria-label="Breadcrumb">
              <Link to="/" className="breadcrumb-root">Home</Link>
              <span className="breadcrumb-separator">/</span>
              <span className="breadcrumb-parent">{breadcrumb.parent}</span>
              <span className="breadcrumb-separator">/</span>
              <span className="breadcrumb-current">{breadcrumb.current}</span>
            </div>
          )}
        </header>

        {/* Dynamic Page Content */}
        <main className="main-content" id="main-content">
          <Outlet />
        </main>

        {/* Global Footer */}
        <footer className="footer">
          <div className="footer-content">
            <div className="footer-left">
              <div className="footer-brand">
                <span className="brand-mark">RE</span>:GENESIS
              </div>
              <p className="footer-tagline">
                Autonomous Electronics Recovery &amp; Second-Life Hardware Passports
              </p>
            </div>

            <div className="footer-center">
              <span className="track-badge">
                <span className="track-icon">🌱</span>
                <span>AWS Environmental Hacks · Waste &amp; Energy Track</span>
              </span>
            </div>

            <div className="footer-right">
              <div className="footer-aws-services">
                <span className="svc-tag">Step Functions</span>
                <span className="svc-tag">SageMaker</span>
                <span className="svc-tag">Textract</span>
                <span className="svc-tag">KMS</span>
                <span className="svc-tag">DynamoDB</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
