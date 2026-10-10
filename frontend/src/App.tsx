import { NavLink, Link, Outlet } from "react-router-dom";

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <div className="header-top-row">
          <Link to="/" className="brand">
            <span className="brand-mark">RE</span>
            <span className="brand-name">GENESIS</span>
            <span className="brand-sub">E-Waste AI</span>
          </Link>

          <div className="header-status-pill">
            <span className="status-dot-pulse"></span>
            <span className="status-label">AWS Serverless Pipeline Active</span>
          </div>
        </div>

        {/* Global Navigation Bar */}
        <nav className="main-nav" aria-label="Main Navigation">
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
              + Start Intake
            </Link>
          </div>
        </nav>
      </header>

      <main className="main">
        <Outlet />
      </main>

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
            <span className="track-badge">AWS Environmental Hacks · Waste &amp; Energy Track</span>
          </div>
          <div className="footer-right">
            <div className="footer-aws-services">
              <span>Step Functions</span> · <span>SageMaker</span> · <span>Textract</span> · <span>KMS</span> · <span>DynamoDB</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
