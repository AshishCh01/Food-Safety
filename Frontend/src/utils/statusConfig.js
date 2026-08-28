// Canonical value/label/tone tables for every enum the backend exposes
// (see docs/API_ARCHITECTURE.md, Backend/app/utils/enums.py). Centralized here
// so status/priority lists and colors are defined once instead of being
// duplicated per page/filter component.

// Raw hex values (not Tailwind classes) for contexts that need a literal
// color string: Leaflet divIcon markers (components/map/markerIcons.js) and
// Recharts fills (components/charts/*). Kept identical to the `priority-*`
// tokens in src/index.css so map pins, badges, and charts always match.
export const PRIORITY_COLORS = {
  low: '#2563eb',
  medium: '#d97706',
  high: '#ea580c',
  critical: '#dc2626',
};

export const COMPLAINT_STATUSES = [
  { value: 'submitted', label: 'Submitted', tone: 'info' },
  { value: 'under_review', label: 'Under Review', tone: 'info' },
  { value: 'needs_information', label: 'Needs Information', tone: 'warning' },
  { value: 'verified', label: 'Verified', tone: 'success' },
  { value: 'rejected', label: 'Rejected', tone: 'danger' },
  { value: 'duplicate', label: 'Duplicate', tone: 'danger' },
  { value: 'insufficient_evidence', label: 'Insufficient Evidence', tone: 'warning' },
  { value: 'assigned', label: 'Assigned', tone: 'info' },
  { value: 'inspection_scheduled', label: 'Inspection Scheduled', tone: 'info' },
  { value: 'under_inspection', label: 'Under Inspection', tone: 'info' },
  { value: 'inspection_completed', label: 'Inspection Completed', tone: 'success' },
  { value: 'action_in_progress', label: 'Action In Progress', tone: 'warning' },
  { value: 'resolved', label: 'Resolved', tone: 'success' },
  { value: 'closed', label: 'Closed', tone: 'neutral' },
  { value: 'cancelled', label: 'Cancelled', tone: 'danger' },
];

export const PRIORITIES = [
  { value: 'low', label: 'Low', tone: 'priority-low' },
  { value: 'medium', label: 'Medium', tone: 'priority-medium' },
  { value: 'high', label: 'High', tone: 'priority-high' },
  { value: 'critical', label: 'Critical', tone: 'priority-critical' },
];

// FindingSeverity shares the same four values as ComplaintPriority.
export const FINDING_SEVERITIES = PRIORITIES;

export const ASSIGNMENT_STATUSES = [
  { value: 'assigned', label: 'Assigned', tone: 'info' },
  { value: 'in_progress', label: 'In Progress', tone: 'warning' },
  { value: 'completed', label: 'Completed', tone: 'success' },
];

export const INSPECTION_STATUSES = [
  { value: 'scheduled', label: 'Scheduled', tone: 'info' },
  { value: 'in_progress', label: 'In Progress', tone: 'warning' },
  { value: 'completed', label: 'Completed', tone: 'success' },
];

export const RAG_DOCUMENT_TYPES = [
  { value: 'law', label: 'Law' },
  { value: 'regulation', label: 'Regulation' },
  { value: 'inspection_guideline', label: 'Inspection Guideline' },
  { value: 'hygiene_guideline', label: 'Hygiene Guideline' },
  { value: 'sampling_procedure', label: 'Sampling Procedure' },
  { value: 'recall_procedure', label: 'Recall Procedure' },
  { value: 'licensing', label: 'Licensing' },
  { value: 'department_sop', label: 'Department SOP' },
  { value: 'other', label: 'Other' },
];

export const RAG_DOCUMENT_STATUSES = [
  { value: 'pending', label: 'Pending', tone: 'neutral' },
  { value: 'ingested', label: 'Ingested', tone: 'success' },
  { value: 'failed', label: 'Failed', tone: 'danger' },
  { value: 'superseded', label: 'Superseded', tone: 'neutral' },
  { value: 'deactivated', label: 'Deactivated', tone: 'neutral' },
];

export const NOTIFICATION_TYPES = [
  { value: 'complaint_submitted', label: 'Complaint submitted' },
  { value: 'complaint_verified', label: 'Complaint verified' },
  { value: 'complaint_rejected', label: 'Complaint rejected' },
  { value: 'inspector_assigned', label: 'Inspector assigned' },
  { value: 'inspection_scheduled', label: 'Inspection scheduled' },
  { value: 'inspection_completed', label: 'Inspection completed' },
  { value: 'complaint_resolved', label: 'Complaint resolved' },
];

export const USER_ROLES = [
  { value: 'citizen', label: 'Citizen', tone: 'neutral' },
  { value: 'inspector', label: 'Inspector', tone: 'info' },
  { value: 'district_officer', label: 'District Officer', tone: 'brand' },
  { value: 'admin', label: 'Admin', tone: 'warning' },
];

function findEntry(list, value) {
  return list.find((entry) => entry.value === value);
}

/** Looks up {value, label, tone} in one of the tables above, falling back to a
 * title-cased label and a neutral tone for any value not in the table. */
export function configFor(list, value) {
  return (
    findEntry(list, value) || {
      value,
      label: formatEnumLabel(value),
      tone: 'neutral',
    }
  );
}

export function formatEnumLabel(value) {
  if (!value) return '';
  return value
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
