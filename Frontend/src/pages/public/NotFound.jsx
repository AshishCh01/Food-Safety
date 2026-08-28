import { Link } from 'react-router-dom';

function NotFound() {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-3 px-4 py-24 text-center">
      <p className="text-sm font-semibold text-brand-700">404</p>
      <h1 className="text-xl font-semibold text-slate-900">Page not found</h1>
      <p className="text-sm text-slate-500">The page you're looking for doesn't exist or has moved.</p>
      <Link
        to="/"
        className="mt-2 inline-flex h-9 items-center justify-center rounded-md border border-brand-700 bg-brand-700 px-4 text-sm font-medium text-white hover:bg-brand-800"
      >
        Back to home
      </Link>
    </div>
  );
}

export default NotFound;
