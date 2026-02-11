import Breadcrumbs from './Breadcrumbs';
import SearchBar from '../shared/SearchBar';

export default function Header() {
  return (
    <header className="flex items-center justify-between border-b border-border bg-surface px-6 py-3">
      <Breadcrumbs />
      <SearchBar />
    </header>
  );
}
