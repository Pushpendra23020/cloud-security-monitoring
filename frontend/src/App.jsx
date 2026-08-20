import { BrowserRouter, Routes, Route } from "react-router-dom";
import MainLayout from "./components/layout/MainLayout";
import Dashboard from "./pages/Dashboard";
import Incidents from "./pages/Incidents";
import Alerts from "./pages/Alerts";
import ThreatHunting from "./pages/ThreatHunting";
import Assets from "./pages/Assets";
import Rules from "./pages/Rules";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/threat-hunting" element={<ThreatHunting />} />
          <Route path="/assets" element={<Assets />} />
          <Route path="/rules" element={<Rules />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
