const STATUSES = [
  'submitted',
  'under_review',
  'needs_information',
  'verified',
  'rejected',
  'assigned',
  'inspection_scheduled',
  'under_inspection',
  'inspection_completed',
  'action_in_progress',
  'resolved',
  'closed',
];
const PRIORITIES = ['low', 'medium', 'high', 'critical'];

function MapFilters({ categories, value, onChange }) {
  function update(field) {
    return (event) => onChange({ ...value, [field]: event.target.value });
  }

  return (
    <div className="filter-row map-filters">
      <label htmlFor="map-status-filter">
        Status
        <select id="map-status-filter" value={value.status} onChange={update('status')}>
          <option value="">All</option>
          {STATUSES.map((status) => (
            <option key={status} value={status}>
              {status.replaceAll('_', ' ')}
            </option>
          ))}
        </select>
      </label>

      <label htmlFor="map-priority-filter">
        Priority
        <select id="map-priority-filter" value={value.priority} onChange={update('priority')}>
          <option value="">All</option>
          {PRIORITIES.map((priority) => (
            <option key={priority} value={priority}>
              {priority}
            </option>
          ))}
        </select>
      </label>

      <label htmlFor="map-category-filter">
        Category
        <select id="map-category-filter" value={value.categoryId} onChange={update('categoryId')}>
          <option value="">All</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </label>

      <label htmlFor="map-date-from-filter">
        From
        <input id="map-date-from-filter" type="date" value={value.dateFrom} onChange={update('dateFrom')} />
      </label>

      <label htmlFor="map-date-to-filter">
        To
        <input id="map-date-to-filter" type="date" value={value.dateTo} onChange={update('dateTo')} />
      </label>
    </div>
  );
}

export default MapFilters;
