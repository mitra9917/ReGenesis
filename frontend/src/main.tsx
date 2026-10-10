import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import App from "./App";
import { LandingPage } from "./pages/Landing";
import { UploadPage } from "./pages/Upload";
import { JobResultsPage } from "./pages/JobResults";
import { PassportsPage } from "./pages/Passports";
import { ImpactReportPage } from "./pages/ImpactReport";
import { ArchitecturePage } from "./pages/Architecture";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          {/* Main Multipage Route Map */}
          <Route index element={<LandingPage />} />
          <Route path="recovery" element={<UploadPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="devices/:deviceId" element={<JobResultsPage />} />
          <Route path="passports" element={<PassportsPage />} />
          <Route path="impact" element={<ImpactReportPage />} />
          <Route path="architecture" element={<ArchitecturePage />} />
          <Route path="how-it-works" element={<ArchitecturePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
