const POSITIVE_STATUSES = new Set(['verified', 'resolved', 'closed']);
const NEGATIVE_STATUSES = new Set(['rejected', 'duplicate', 'insufficient_evidence', 'cancelled']);

export function variantForStatus(status) {
  if (POSITIVE_STATUSES.has(status)) return 'ok';
  if (NEGATIVE_STATUSES.has(status)) return 'error';
  return 'loading';
}

export function formatStatusLabel(status) {
  return status
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
