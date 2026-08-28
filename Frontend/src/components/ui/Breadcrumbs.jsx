import { ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

/** `items` is [{label, path?}], last item rendered as plain text (current page). */
function Breadcrumbs({ items }) {
  if (!items?.length) return null;
  return (
    <nav aria-label="Breadcrumb" className="mb-2">
      <ol className="flex flex-wrap items-center gap-1 text-sm text-slate-500">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <li key={`${item.label}-${index}`} className="flex items-center gap-1">
              {index > 0 && <ChevronRight className="size-3.5 text-slate-400" aria-hidden="true" />}
              {isLast || !item.path ? (
                <span aria-current={isLast ? 'page' : undefined} className="font-medium text-slate-700">
                  {item.label}
                </span>
              ) : (
                <Link to={item.path} className="hover:text-brand-700 hover:underline">
                  {item.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export default Breadcrumbs;
