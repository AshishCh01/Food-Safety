import { ChevronLeft, ChevronRight } from 'lucide-react';
import Button from './Button';

/** Prev/Next pagination matching the page/pageSize/total shape every list
 * page already fetches from the paginated list endpoints. */
function Pagination({ page, pageSize, total, onPageChange, className }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;

  return (
    <div className={`flex items-center justify-between gap-3 ${className || ''}`}>
      <p className="text-sm text-slate-500">
        Page {page} of {totalPages} &middot; {total} total
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          <ChevronLeft className="size-4" aria-hidden="true" />
          Prev
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
        >
          Next
          <ChevronRight className="size-4" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}

export default Pagination;
