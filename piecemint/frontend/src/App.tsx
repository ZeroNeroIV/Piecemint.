import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { FinanceDataProvider } from './context/FinanceDataContext';
import AppLayout from './components/AppLayout';
import Overview from './pages/Overview';
import Analytics from './pages/Analytics';
import Contacts from './pages/Contacts';
import Activity from './pages/Activity';
import BudgetCashFlow from './pages/BudgetCashFlow';
import Marketplace from './pages/Marketplace';
import PluginDocsPage from './pages/PluginDocsPage';
import PluginPage from './pages/PluginPage';
import FinancialSettingsPage from './pages/FinancialSettings';

function App() {
  return (
    <Router>
      <FinanceDataProvider>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Overview />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/contacts" element={<Contacts />} />
            <Route path="/activity" element={<Activity />} />
            <Route path="/budget" element={<BudgetCashFlow />} />
            <Route path="/financial-settings" element={<FinancialSettingsPage />} />
            <Route path="/library" element={<Marketplace />} />
            <Route path="/marketplace" element={<Navigate to="/library" replace />} />
            <Route path="/docs/plugins" element={<PluginDocsPage />} />
            <Route path="/plugin/:pluginId" element={<PluginPage />} />
          </Route>
        </Routes>
      </FinanceDataProvider>
    </Router>
  );
}

export default App;
