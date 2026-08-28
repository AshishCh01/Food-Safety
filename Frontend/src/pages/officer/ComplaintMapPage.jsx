import { useEffect, useState } from 'react';
import ComplaintMap from '../../components/map/ComplaintMap';
import MapFilters from '../../components/map/MapFilters';
import { useAuth } from '../../hooks/useAuth';
import { apiRequest } from '../../services/api';
import { listComplaintCategories, listDistricts } from '../../services/complaintService';
import { getComplaintsMap } from '../../services/mapService';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import ErrorState from '../../components/ui/ErrorState';

const INITIAL_FILTERS = { status: '', priority: '', categoryId: '', dateFrom: '', dateTo: '' };

function ComplaintMapPage() {
  const { getAccessToken } = useAuth();
  const [categories, setCategories] = useState([]);
  const [center, setCenter] = useState(null);
  const [filters, setFilters] = useState(INITIAL_FILTERS);
  const [bounds, setBounds] = useState(null);
  const [markers, setMarkers] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = getAccessToken();
    Promise.all([listComplaintCategories(token), apiRequest('/officer/dashboard', { token }), listDistricts(token)])
      .then(([categoryList, dashboard, districts]) => {
        setCategories(categoryList);
        const district = districts.find((item) => item.id === dashboard.district_id);
        if (district?.centroid_latitude && district?.centroid_longitude) {
          setCenter([district.centroid_latitude, district.centroid_longitude]);
        }
      })
      .catch((err) => setError(err.message));
  }, [getAccessToken]);

  useEffect(() => {
    const token = getAccessToken();
    getComplaintsMap(token, {
      minLat: bounds?.minLat,
      minLng: bounds?.minLng,
      maxLat: bounds?.maxLat,
      maxLng: bounds?.maxLng,
      status: filters.status || undefined,
      priority: filters.priority || undefined,
      categoryId: filters.categoryId || undefined,
      dateFrom: filters.dateFrom || undefined,
      dateTo: filters.dateTo || undefined,
    })
      .then((data) => setMarkers(data.items))
      .catch((err) => setError(err.message));
  }, [getAccessToken, bounds, filters]);

  return (
    <ContentContainer className="max-w-none">
      <PageHeader
        title="Complaint Map"
        description="Complaints in your district plotted by reported location. Colors indicate priority."
      />

      <MapFilters categories={categories} value={filters} onChange={setFilters} />

      {error && <ErrorState message={error} />}

      <ComplaintMap markers={markers} center={center} onBoundsChange={setBounds} />

      <p className="text-sm text-slate-500">{markers.length} complaint(s) shown on the current map view.</p>
    </ContentContainer>
  );
}

export default ComplaintMapPage;
