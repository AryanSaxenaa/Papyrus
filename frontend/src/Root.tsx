import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import App from "./App";
import LandingPage from "./pages/LandingPage";

export default function Root() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/app" element={<App />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
