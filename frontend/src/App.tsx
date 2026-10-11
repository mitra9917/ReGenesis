import { useState, useEffect } from "react";
import { NavLink, Link, Outlet, useLocation } from "react-router-dom";

export default function App() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  function getBreadcrumb() {
    const path = location.pathname;
    if (path === "/") return null;
    if (path.startsWith("/recovery") || path.startsWith("/upload")) {
      return { parent: "Recovery", current: "Intake" };
    }
    if (path.startsWith("/devices/")) {
      return { parent: "Devices", current: path.split("/")[2] || "" };
    }
    if (path.startsWith("/passports")) return { parent: "Trust", current: "Passports" };
    if (path.startsWith("/impact")) return { parent: "Impact", current: "LCA ledger" };
    if (path.startsWith("/architecture") || path.startsWith("/how-it-works")) {
      return { parent: "System", current: "Architecture" };
    }
    return null;
  }

  const breadcrumb = getBreadcrumb();
  const isHome = location.pathname === "/";

  return (
    <div className="pl-root">
      <div className="pl-frame">
        <header className="pl-header">
          <Link to="/" className="pl-logo">
            RE:GENESIS
          </Link>

          <button
            type="button"
            className="pl-menu-btn"
            aria-label="Menu"
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((v) => !v)}
          >
            Menu
          </button>

          <nav className={`pl-nav ${mobileOpen ? "is-open" : ""}`} aria-label="Primary">
            <NavLink to="/" end>
              Overview
            </NavLink>
            <NavLink to="/recovery">Recovery</NavLink>
            <NavLink to="/passports">Passports</NavLink>
            <NavLink to="/impact">Impact</NavLink>
            <NavLink to="/architecture">Architecture</NavLink>
            <Link to="/recovery" className="pl-nav-cta">
              Get started →
            </Link>
          </nav>
        </header>

        {breadcrumb && (
          <div className="pl-breadcrumb">
            <Link to="/">Home</Link>
            <span>/</span>
            <span>{breadcrumb.parent}</span>
            <span>/</span>
            <span className="is-current">{breadcrumb.current}</span>
          </div>
        )}

        <main className={`pl-main ${isHome ? "pl-main-home" : ""}`}>
          <Outlet />
        </main>

        <footer className="pl-footer">
          <div className="pl-footer-row">
            <div>
              <strong>RE:GENESIS</strong>
              <p>Adaptive electronics recovery. No shred-first defaults.</p>
            </div>
            <div className="pl-footer-links">
              <Link to="/recovery">Recovery</Link>
              <Link to="/passports">Passports</Link>
              <Link to="/architecture">Architecture</Link>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
