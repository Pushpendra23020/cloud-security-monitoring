import {
  lazy,
  Suspense,
} from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import MainLayout from "./components/layout/MainLayout";
import { AuthProvider } from "./context/AuthContext";
import { useAuth } from "./context/authState";

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

const SystemHealth = lazy(() => import("./pages/SystemHealth"));
const Settings = lazy(() => import("./pages/Settings"));
const Login = lazy(() => import("./pages/Login"));
const Users = lazy(() => import("./pages/Users"));

function ProtectedLayout() {
  const { enabled, loading, user } = useAuth();
  if (loading) return <RouteLoadingFallback />;
  if (enabled && !user) return <Navigate to="/login" replace />;
  return <MainLayout />;
}


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
      <AuthProvider>
      <Suspense
        fallback={<RouteLoadingFallback />}
      >
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedLayout />}>
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
            <Route path="/health" element={<SystemHealth />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/users" element={<Users />} />
          </Route>
        </Routes>
      </Suspense>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
