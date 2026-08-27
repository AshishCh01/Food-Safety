import { useState } from 'react';
import LocationPicker from '../map/LocationPicker';
import { reverseGeocode } from '../../services/mapService';

const PRIORITIES = ['low', 'medium', 'high', 'critical'];

const INITIAL_FORM = {
  categoryId: '',
  districtId: '',
  title: '',
  description: '',
  priority: 'medium',
  addressLine: '',
  latitude: null,
  longitude: null,
  businessName: '',
  businessType: '',
  businessAddress: '',
  businessPhone: '',
  businessLicense: '',
};

function ComplaintForm({ categories, districts, onSubmit, isSubmitting, error, token }) {
  const [form, setForm] = useState(INITIAL_FORM);

  function updateField(field) {
    return (event) => setForm((prev) => ({ ...prev, [field]: event.target.value }));
  }

  function handleLocationChange(latitude, longitude) {
    setForm((prev) => ({ ...prev, latitude, longitude }));
    // Best-effort address prefill - never blocks the form if it fails, and
    // never overwrites something the citizen already typed themselves.
    if (token) {
      reverseGeocode(token, { lat: latitude, lon: longitude })
        .then((result) => {
          if (result?.address) {
            setForm((prev) => (prev.addressLine ? prev : { ...prev, addressLine: result.address }));
          }
        })
        .catch(() => {});
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit({
      category_id: form.categoryId,
      district_id: form.districtId,
      title: form.title,
      description: form.description,
      priority: form.priority,
      address_line: form.addressLine || null,
      latitude: form.latitude,
      longitude: form.longitude,
      business: {
        business_name: form.businessName,
        business_type: form.businessType || null,
        address: form.businessAddress,
        contact_phone: form.businessPhone || null,
        license_number: form.businessLicense || null,
      },
    });
  }

  return (
    <form onSubmit={handleSubmit} className="complaint-form">
      <label htmlFor="complaint-category">
        Category
        <select id="complaint-category" value={form.categoryId} onChange={updateField('categoryId')} required>
          <option value="">Select a category</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </label>

      <label htmlFor="complaint-district">
        District
        <select id="complaint-district" value={form.districtId} onChange={updateField('districtId')} required>
          <option value="">Select a district</option>
          {districts.map((district) => (
            <option key={district.id} value={district.id}>
              {district.name}
            </option>
          ))}
        </select>
      </label>

      <label htmlFor="complaint-title">
        Title
        <input id="complaint-title" value={form.title} onChange={updateField('title')} minLength={3} required />
      </label>

      <label htmlFor="complaint-description">
        Description
        <textarea
          id="complaint-description"
          value={form.description}
          onChange={updateField('description')}
          minLength={10}
          rows={5}
          required
        />
      </label>

      <label htmlFor="complaint-priority">
        Priority
        <select id="complaint-priority" value={form.priority} onChange={updateField('priority')}>
          {PRIORITIES.map((priority) => (
            <option key={priority} value={priority}>
              {priority}
            </option>
          ))}
        </select>
      </label>

      <label htmlFor="complaint-address">
        Location description
        <input id="complaint-address" value={form.addressLine} onChange={updateField('addressLine')} />
      </label>

      <label>
        Pin the location on the map (optional)
        <LocationPicker latitude={form.latitude} longitude={form.longitude} onChange={handleLocationChange} />
        <span className="field-hint">
          If you pin a location, the district above is confirmed automatically from it.
        </span>
      </label>

      <fieldset>
        <legend>Business / shop details</legend>
        <label htmlFor="business-name">
          Business name
          <input id="business-name" value={form.businessName} onChange={updateField('businessName')} required />
        </label>
        <label htmlFor="business-type">
          Business type (optional)
          <input id="business-type" value={form.businessType} onChange={updateField('businessType')} />
        </label>
        <label htmlFor="business-address">
          Business address
          <input
            id="business-address"
            value={form.businessAddress}
            onChange={updateField('businessAddress')}
            required
          />
        </label>
        <label htmlFor="business-phone">
          Business phone (optional)
          <input id="business-phone" value={form.businessPhone} onChange={updateField('businessPhone')} />
        </label>
        <label htmlFor="business-license">
          License number (optional)
          <input id="business-license" value={form.businessLicense} onChange={updateField('businessLicense')} />
        </label>
      </fieldset>

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : 'Submit complaint'}
      </button>
    </form>
  );
}

export default ComplaintForm;
