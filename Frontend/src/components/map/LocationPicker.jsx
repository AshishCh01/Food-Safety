import { useState } from 'react';
import { LocateFixed } from 'lucide-react';
import { MapContainer, Marker, TileLayer, useMapEvents } from 'react-leaflet';
import { locationPinIcon } from './markerIcons';
import Alert from '../ui/Alert';
import Button from '../ui/Button';

const OSM_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const OSM_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
const DEFAULT_CENTER = [19.7515, 75.7139]; // Maharashtra
const DEFAULT_ZOOM = 6;
const PICKED_ZOOM = 14;

function ClickHandler({ onPick }) {
  useMapEvents({
    click(event) {
      onPick(event.latlng.lat, event.latlng.lng);
    },
  });
  return null;
}

function LocationPicker({ latitude, longitude, onChange }) {
  const [locationError, setLocationError] = useState(null);
  const hasPoint = latitude !== null && latitude !== undefined && longitude !== null && longitude !== undefined;

  function useMyLocation() {
    if (!navigator.geolocation) {
      setLocationError('Location is not available in this browser.');
      return;
    }
    setLocationError(null);
    navigator.geolocation.getCurrentPosition(
      (position) => onChange(position.coords.latitude, position.coords.longitude),
      () => setLocationError('Could not access your location.'),
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="h-64 w-full overflow-hidden rounded-lg border border-slate-200 sm:h-80">
        <MapContainer
          center={hasPoint ? [latitude, longitude] : DEFAULT_CENTER}
          zoom={hasPoint ? PICKED_ZOOM : DEFAULT_ZOOM}
          scrollWheelZoom
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer url={OSM_TILE_URL} attribution={OSM_ATTRIBUTION} />
          <ClickHandler onPick={onChange} />
          {hasPoint && (
            <Marker
              position={[latitude, longitude]}
              icon={locationPinIcon()}
              draggable
              eventHandlers={{
                dragend(event) {
                  const { lat, lng } = event.target.getLatLng();
                  onChange(lat, lng);
                },
              }}
            />
          )}
        </MapContainer>
      </div>
      <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
        <Button type="button" variant="secondary" size="sm" onClick={useMyLocation}>
          <LocateFixed className="size-4" aria-hidden="true" />
          Use my current location
        </Button>
        <span>Or click the map to drop a pin</span>
        {hasPoint && (
          <span className="font-mono text-xs text-slate-500">
            {Number(latitude).toFixed(5)}, {Number(longitude).toFixed(5)}
          </span>
        )}
      </div>
      {locationError && <Alert tone="danger">{locationError}</Alert>}
    </div>
  );
}

export default LocationPicker;
