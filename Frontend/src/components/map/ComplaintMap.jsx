import { MapContainer, TileLayer, useMapEvents } from 'react-leaflet';
import ComplaintMarker from './ComplaintMarker';

const OSM_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const OSM_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

const DEFAULT_CENTER = [19.7515, 75.7139]; // Maharashtra, used until a district centroid is known
const DEFAULT_ZOOM = 7;

function BoundsWatcher({ onBoundsChange }) {
  const map = useMapEvents({
    moveend() {
      if (!onBoundsChange) return;
      const bounds = map.getBounds();
      onBoundsChange({
        minLat: bounds.getSouth(),
        maxLat: bounds.getNorth(),
        minLng: bounds.getWest(),
        maxLng: bounds.getEast(),
      });
    },
  });
  return null;
}

function ComplaintMap({ markers, center, zoom = 12, onBoundsChange }) {
  return (
    <div className="h-72 w-full overflow-hidden rounded-lg border border-slate-200 sm:h-96 lg:h-120">
      <MapContainer
        center={center || DEFAULT_CENTER}
        zoom={center ? zoom : DEFAULT_ZOOM}
        scrollWheelZoom
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer url={OSM_TILE_URL} attribution={OSM_ATTRIBUTION} />
        <BoundsWatcher onBoundsChange={onBoundsChange} />
        {markers.map((marker) => (
          <ComplaintMarker key={marker.id} marker={marker} />
        ))}
      </MapContainer>
    </div>
  );
}

export default ComplaintMap;
