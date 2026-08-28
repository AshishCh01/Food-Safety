import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';
import { locationPinIcon } from './markerIcons';

const OSM_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const OSM_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

// Read-only single-marker map used to display a business/complaint
// location on detail pages - not interactive, unlike LocationPicker.
function LocationMap({ latitude, longitude, label }) {
  if (latitude === null || latitude === undefined || longitude === null || longitude === undefined) {
    return null;
  }

  return (
    <div className="h-48 w-full overflow-hidden rounded-lg border border-slate-200 sm:h-60">
      <MapContainer
        center={[latitude, longitude]}
        zoom={15}
        scrollWheelZoom={false}
        dragging={false}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer url={OSM_TILE_URL} attribution={OSM_ATTRIBUTION} />
        <Marker position={[latitude, longitude]} icon={locationPinIcon()}>
          {label && <Popup>{label}</Popup>}
        </Marker>
      </MapContainer>
    </div>
  );
}

export default LocationMap;
