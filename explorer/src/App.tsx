import { Routes, Route } from 'react-router-dom';
import PageLayout from './components/layout/PageLayout';
import Dashboard from './pages/Dashboard';
import ModuleCatalog from './pages/ModuleCatalog';
import ModuleDetailPage from './pages/ModuleDetailPage';
import SkillCatalog from './pages/SkillCatalog';
import SkillDetailPage from './pages/SkillDetailPage';
import ProfileCatalog from './pages/ProfileCatalog';
import ProfileDetailPage from './pages/ProfileDetailPage';
import SearchPage from './pages/SearchPage';
import HowTo from './pages/HowTo';

export default function App() {
  return (
    <PageLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/modules" element={<ModuleCatalog />} />
        <Route path="/modules/:name" element={<ModuleDetailPage />} />
        <Route path="/skills" element={<SkillCatalog />} />
        <Route path="/skills/:category/:name" element={<SkillDetailPage />} />
        <Route path="/profiles" element={<ProfileCatalog />} />
        <Route path="/profiles/:name" element={<ProfileDetailPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/how-to" element={<HowTo />} />
      </Routes>
    </PageLayout>
  );
}
