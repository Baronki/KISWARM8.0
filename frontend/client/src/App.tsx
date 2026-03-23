import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import DownloadCenter from "./pages/DownloadCenter";
import MessagingCenter from "./pages/MessagingCenter";
import AccountOpening from "./pages/AccountOpening";
import AdminDashboard from "./pages/AdminDashboard";
import KIAgentProfiles from "./pages/KIAgentProfiles";
import AnalyticsDashboard from "./pages/AnalyticsDashboard";
import TCSOrderSystem from "./pages/TCSOrderSystem";
import WaitlistManagement from "./pages/WaitlistManagement";
import ComplianceVerification from "./pages/ComplianceVerification";
import TCSOrderForm from "./pages/TCSOrderForm";
import ReputationManagement from '@/pages/ReputationManagement';
import Transparency from '@/pages/Transparency';
import TCSGreenSafeHouse from '@/pages/TCSGreenSafeHouse';
import KIProofVerification from "./pages/KIProofVerification";
import ComplianceReports from "./pages/ComplianceReports";
import FileManager from "./pages/FileManager";
import { KIWZBProvider } from "./contexts/KIWZBContext";
import { NotificationProvider } from "./contexts/NotificationContext";
function Router() {
  // make sure to consider if you need authentication for certain routes
  return (
    <Switch>
      <Route path={"/"} component={Home} />
      <Route path={"/downloads"} component={DownloadCenter} />
      <Route path={"/messaging"} component={MessagingCenter} />
      <Route path={"/account-opening"} component={AccountOpening} />
      <Route path={"/tcs-order"} component={TCSOrderForm} />
      <Route path={"/waitlist"} component={WaitlistManagement} />
      <Route path={"/compliance"} component={ComplianceVerification} />
      <Route path="/reputation" component={ReputationManagement} />
      <Route path="/transparency" component={Transparency} />
      <Route path="/tcs-green-safehouse" component={TCSGreenSafeHouse} />
      <Route path="/ki-proof" component={KIProofVerification} />
      <Route path={"/compliance-reports"} component={ComplianceReports} />
      <Route path={"/files"} component={FileManager} />
      <Route path={"/admin"} component={AdminDashboard} />
      <Route path={"/ki-directors"} component={KIAgentProfiles} />
      <Route path={"/analytics"} component={AnalyticsDashboard} />
      <Route path={"/404"} component={NotFound} />
      {/* Final fallback route */}
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="dark">
        <KIWZBProvider>
          <NotificationProvider>
            <TooltipProvider>
              <Toaster />
              <Router />
            </TooltipProvider>
          </NotificationProvider>
        </KIWZBProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
