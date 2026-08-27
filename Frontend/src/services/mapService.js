import { apiRequest } from './api';

function withQuery(path, params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, value);
    }
  });
  const query = search.toString();
  return query ? `${path}?${query}` : path;
}

export function getComplaintsMap(
  token,
  { minLat, minLng, maxLat, maxLng, status, priority, categoryId, dateFrom, dateTo } = {}
) {
  return apiRequest(
    withQuery('/officer/complaints/map', {
      min_lat: minLat,
      min_lng: minLng,
      max_lat: maxLat,
      max_lng: maxLng,
      status,
      priority,
      category_id: categoryId,
      date_from: dateFrom,
      date_to: dateTo,
    }),
    { token }
  );
}

export function getNearbyComplaints(token, { latitude, longitude, radiusKm } = {}) {
  return apiRequest(
    withQuery('/officer/complaints/nearby', { latitude, longitude, radius_km: radiusKm }),
    { token }
  );
}

export function reverseGeocode(token, { lat, lon }) {
  return apiRequest(withQuery('/reverse-geocode', { lat, lon }), { token });
}
