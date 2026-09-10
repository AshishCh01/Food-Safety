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
  subCategoryId: '',
  foodType: '',
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

  const selectedCategory = categories.find((c) => c.id === form.categoryId);
  const isOthers = selectedCategory?.key === 'others';
  const subcategories = selectedCategory?.subcategories || [];

  function updateField(field) {
    return (event) => setForm((prev) => ({ ...prev, [field]: event.target.value }));
  }

  function handleCategoryChange(event) {
    setForm((prev) => ({
      ...prev,
      categoryId: event.target.value,
      subCategoryId: '',
      foodType: '',
    }));
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
      subcategory_id: isOthers ? null : form.subCategoryId,
      food_type: isOthers ? form.foodType : null,
      district_id: form.districtId,
      title: `Complaint regarding ${form.businessName}`,
      description: form.description,
      priority: form.priority,
      address_line: form.addressLine || null,
      latitude: form.latitude,
      longitude: form.longitude,
      business: {
        business_name: form.businessName,
        business_type: form.businessType || null,
        address: form.addressLine || 'Not provided',
        contact_phone: form.businessPhone || null,
        license_number: form.businessLicense || null,
      },
    });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <Card className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField label="Category" htmlFor="complaint-category" required>
          <Select id="complaint-category" value={form.categoryId} onChange={handleCategoryChange} required>
            <option value="">Select a category</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </Select>
        </FormField>

        {isOthers ? (
          <FormField label="Enter Food Type" htmlFor="complaint-food-type" required>
            <Input id="complaint-food-type" value={form.foodType} onChange={updateField('foodType')} required />
          </FormField>
        ) : (
          <FormField label="Sub Category" htmlFor="complaint-subcategory" required>
            <Select
              id="complaint-subcategory"
              value={form.subCategoryId}
              onChange={updateField('subCategoryId')}
              required
              disabled={!form.categoryId}
            >
              <option value="">Select a sub category</option>
              {subcategories.map((sub) => (
                <option key={sub.id} value={sub.id}>
                  {sub.name}
                </option>
              ))}
            </Select>
          </FormField>
        )}

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
          <FormField label="Concern" htmlFor="concern" required>
            <Select id="concern" value={form.businessType} onChange={updateField('businessType')} required>
              <option value="">Select Concern</option>
              <option value="Rotten food">Rotten food</option>
              <option value="Foreign material present">Foreign material present</option>
              <option value="Non-veg food delivered instead of veg food">Non-veg food delivered instead of veg food</option>
              <option value="Expired product delivered">Expired product delivered</option>
              <option value="Issue with labelling of food products">Issue with labelling of food products</option>
              <option value="Damaged/puffed pack">Damaged/puffed pack</option>
              <option value="Delivery issues">Delivery issues</option>
              <option value="Others">Others</option>
            </Select>
          </FormField>
          <FormField label="License number" htmlFor="business-license" hint="Optional">
            <Input id="business-license" value={form.businessLicense} onChange={updateField('businessLicense')} />
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
