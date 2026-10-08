import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import App from "./App";
import { UploadPage } from "./pages/Upload";
import { JobResultsPage } from "./pages/JobResults";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<UploadPage />} />
          <Route path="devices/:deviceId" element={<JobResultsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
