import { useState } from 'react';
import { PRIORITIES } from '../../utils/statusConfig';
import { reverseGeocode } from '../../services/mapService';
import LocationPicker from '../map/LocationPicker';
import Alert from '../ui/Alert';
import Button from '../ui/Button';
import Card from '../ui/Card';
import FormField from '../ui/FormField';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Textarea from '../ui/Textarea';

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
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <Card className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField label="Category" htmlFor="complaint-category" required>
          <Select id="complaint-category" value={form.categoryId} onChange={updateField('categoryId')} required>
            <option value="">Select a category</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField label="District" htmlFor="complaint-district" required>
          <Select id="complaint-district" value={form.districtId} onChange={updateField('districtId')} required>
            <option value="">Select a district</option>
            {districts.map((district) => (
              <option key={district.id} value={district.id}>
                {district.name}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField label="Title" htmlFor="complaint-title" required className="sm:col-span-2">
          <Input id="complaint-title" value={form.title} onChange={updateField('title')} minLength={3} required />
        </FormField>

        <FormField label="Description" htmlFor="complaint-description" required className="sm:col-span-2">
          <Textarea
            id="complaint-description"
            value={form.description}
            onChange={updateField('description')}
            minLength={10}
            rows={5}
            required
          />
        </FormField>

        <FormField label="Priority" htmlFor="complaint-priority">
          <Select id="complaint-priority" value={form.priority} onChange={updateField('priority')}>
            {PRIORITIES.map((priority) => (
              <option key={priority.value} value={priority.value}>
                {priority.label}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField label="Location description" htmlFor="complaint-address">
          <Input id="complaint-address" value={form.addressLine} onChange={updateField('addressLine')} />
        </FormField>

        <FormField
          label="Pin the location on the map (optional)"
          htmlFor="complaint-location-picker"
          hint="If you pin a location, the district above is confirmed automatically from it."
          className="sm:col-span-2"
        >
          <LocationPicker
            id="complaint-location-picker"
            latitude={form.latitude}
            longitude={form.longitude}
            onChange={handleLocationChange}
          />
        </FormField>
      </Card>

      <Card>
        <Card.Header>
          <Card.Title>Business / shop details</Card.Title>
        </Card.Header>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormField label="Business name" htmlFor="business-name" required className="sm:col-span-2">
            <Input id="business-name" value={form.businessName} onChange={updateField('businessName')} required />
          </FormField>
          <FormField label="Business type" htmlFor="business-type" hint="Optional">
            <Input id="business-type" value={form.businessType} onChange={updateField('businessType')} />
          </FormField>
          <FormField label="License number" htmlFor="business-license" hint="Optional">
            <Input id="business-license" value={form.businessLicense} onChange={updateField('businessLicense')} />
          </FormField>
          <FormField label="Business address" htmlFor="business-address" required className="sm:col-span-2">
            <Input
              id="business-address"
              value={form.businessAddress}
              onChange={updateField('businessAddress')}
              required
            />
          </FormField>
          <FormField label="Business phone" htmlFor="business-phone" hint="Optional">
            <Input id="business-phone" value={form.businessPhone} onChange={updateField('businessPhone')} />
          </FormField>
        </div>
      </Card>

      {error && <Alert tone="danger">{error}</Alert>}

      <Button type="submit" loading={isSubmitting} className="self-start">
        {isSubmitting ? 'Submitting…' : 'Submit complaint'}
      </Button>
    </form>
  );
}

export default ComplaintForm;
