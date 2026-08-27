import { useState } from 'react';
import { MapContainer, Marker, TileLayer, useMapEvents } from 'react-leaflet';
import { locationPinIcon } from './markerIcons';

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
      () => setLocationError('Could not access your location.')
    );
  }

  return (
    <div className="location-picker">
      <div className="map-container map-container-picker">
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
      <div className="location-row">
        <button type="button" onClick={useMyLocation}>
          Use my current location
        </button>
        <span>Or click the map to drop a pin</span>
        {hasPoint && (
          <span>
            {Number(latitude).toFixed(5)}, {Number(longitude).toFixed(5)}
          </span>
        )}
      </div>
      {locationError && <p className="form-error">{locationError}</p>}
    </div>
  );
}

export default LocationPicker;
