import {
  lazy,
  Suspense,
} from "react";
import {
  BrowserRouter,
  Route,
  Routes,
} from "react-router-dom";

import MainLayout from "./components/layout/MainLayout";

const Dashboard = lazy(
  () => import("./pages/Dashboard")
);

const Incidents = lazy(
  () => import("./pages/Incidents")
);

const Alerts = lazy(
  () => import("./pages/Alerts")
);

const ThreatHunting = lazy(
  () => import("./pages/ThreatHunting")
);

const Assets = lazy(
  () => import("./pages/Assets")
);

const Rules = lazy(
  () => import("./pages/Rules")
);


function RouteLoadingFallback() {
  return (
    <div className="panel route-loading">
      Loading security workspace...
    </div>
  );
}


function App() {
  return (
    <BrowserRouter>
      <Suspense
        fallback={<RouteLoadingFallback />}
      >
        <Routes>
          <Route element={<MainLayout />}>
            <Route
              path="/"
              element={<Dashboard />}
            />

            <Route
              path="/incidents"
              element={<Incidents />}
            />

            <Route
              path="/alerts"
              element={<Alerts />}
            />

            <Route
              path="/threat-hunting"
              element={<ThreatHunting />}
            />

            <Route
              path="/assets"
              element={<Assets />}
            />

            <Route
              path="/rules"
              element={<Rules />}
            />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
