import { COMPLAINT_STATUSES, PRIORITIES } from '../../utils/statusConfig';
import FormField from '../ui/FormField';
import Input from '../ui/Input';
import Select from '../ui/Select';

function MapFilters({ categories, value, onChange }) {
  function update(field) {
    return (event) => onChange({ ...value, [field]: event.target.value });
  }

  return (
    <div className="flex flex-wrap items-end gap-3">
      <FormField label="Status" htmlFor="map-status-filter">
        <Select id="map-status-filter" value={value.status} onChange={update('status')}>
          <option value="">All</option>
          {COMPLAINT_STATUSES.map((status) => (
            <option key={status.value} value={status.value}>
              {status.label}
            </option>
          ))}
        </Select>
      </FormField>

      <FormField label="Priority" htmlFor="map-priority-filter">
        <Select id="map-priority-filter" value={value.priority} onChange={update('priority')}>
          <option value="">All</option>
          {PRIORITIES.map((priority) => (
            <option key={priority.value} value={priority.value}>
              {priority.label}
            </option>
          ))}
        </Select>
      </FormField>

      <FormField label="Category" htmlFor="map-category-filter">
        <Select id="map-category-filter" value={value.categoryId} onChange={update('categoryId')}>
          <option value="">All</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </Select>
      </FormField>

      <FormField label="From" htmlFor="map-date-from-filter">
        <Input id="map-date-from-filter" type="date" value={value.dateFrom} onChange={update('dateFrom')} />
      </FormField>

      <FormField label="To" htmlFor="map-date-to-filter">
        <Input id="map-date-to-filter" type="date" value={value.dateTo} onChange={update('dateTo')} />
      </FormField>
    </div>
  );
}

export default MapFilters;
