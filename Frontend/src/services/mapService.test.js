import { afterEach, describe, expect, it, vi } from 'vitest';
import { getComplaintsMap, getNearbyComplaints, reverseGeocode } from './mapService';

afterEach(() => {
  vi.unstubAllGlobals();
});

function stubFetch() {
  const fetchMock = vi.fn(() =>
    Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ items: [], total: 0 }),
    })
  );
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

describe('getComplaintsMap', () => {
  it('builds a query string with only the provided filters', async () => {
    const fetchMock = stubFetch();

    await getComplaintsMap('token123', { status: 'verified', priority: 'high' });

    const calledUrl = fetchMock.mock.calls[0][0].toString();
    expect(calledUrl).toContain('/officer/complaints/map?');
    expect(calledUrl).toContain('status=verified');
    expect(calledUrl).toContain('priority=high');
    expect(calledUrl).not.toContain('category_id');
    expect(calledUrl).not.toContain('min_lat');
  });

  it('includes bounding box params when supplied', async () => {
    const fetchMock = stubFetch();

    await getComplaintsMap('token123', { minLat: 18.4, minLng: 73.7, maxLat: 18.6, maxLng: 73.9 });

    const calledUrl = fetchMock.mock.calls[0][0].toString();
    expect(calledUrl).toContain('min_lat=18.4');
    expect(calledUrl).toContain('max_lng=73.9');
  });

  it('attaches the bearer token', async () => {
    const fetchMock = stubFetch();

    await getComplaintsMap('token123', {});

    const options = fetchMock.mock.calls[0][1];
    expect(options.headers.Authorization).toBe('Bearer token123');
  });
});

describe('getNearbyComplaints', () => {
  it('sends latitude, longitude and radius_km', async () => {
    const fetchMock = stubFetch();

    await getNearbyComplaints('token123', { latitude: 18.52, longitude: 73.86, radiusKm: 5 });

    const calledUrl = fetchMock.mock.calls[0][0].toString();
    expect(calledUrl).toContain('/officer/complaints/nearby?');
    expect(calledUrl).toContain('latitude=18.52');
    expect(calledUrl).toContain('longitude=73.86');
    expect(calledUrl).toContain('radius_km=5');
  });
});

describe('reverseGeocode', () => {
  it('requests the reverse-geocode endpoint with lat/lon', async () => {
    const fetchMock = stubFetch();

    await reverseGeocode('token123', { lat: 18.52, lon: 73.86 });

    const calledUrl = fetchMock.mock.calls[0][0].toString();
    expect(calledUrl).toContain('/reverse-geocode?lat=18.52&lon=73.86');
  });
});
