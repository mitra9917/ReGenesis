import { Link, Outlet } from "react-router-dom";

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <Link to="/" className="brand">
          <span className="brand-mark">RE</span>
          <span>GENESIS</span>
        </Link>
        <p className="tagline">Second-Life Passports for adaptive electronics recovery</p>
      </header>
      <main className="main">
        <Outlet />
      </main>
      <footer className="footer">AWS Environmental Hacks · Waste &amp; Energy · E-waste</footer>
    </div>
  );
}
