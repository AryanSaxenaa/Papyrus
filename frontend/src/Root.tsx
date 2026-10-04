import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import App from "./App";
import EvalPage from "./pages/EvalPage";
import LandingPage from "./pages/LandingPage";
import MethodPage from "./pages/MethodPage";

export default function Root() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/app" element={<App />} />
        <Route path="/eval" element={<EvalPage />} />
        <Route path="/method" element={<MethodPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
