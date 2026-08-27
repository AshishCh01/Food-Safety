import { Link } from 'react-router-dom';
import { Marker, Popup } from 'react-leaflet';
import { priorityMarkerIcon } from './markerIcons';

function ComplaintMarker({ marker }) {
  return (
    <Marker position={[marker.latitude, marker.longitude]} icon={priorityMarkerIcon(marker.priority)}>
      <Popup>
        <div className="marker-popup">
          <p className="complaint-number">{marker.complaint_number}</p>
          <p className="marker-popup-title">{marker.title}</p>
          <p className="marker-popup-meta">
            {marker.category_name} &middot; <span className={`priority-tag priority-${marker.priority}`}>{marker.priority}</span>
          </p>
          {marker.business_name && <p className="marker-popup-meta">{marker.business_name}</p>}
          <Link to={`/officer/complaints/${marker.id}`}>View complaint</Link>
        </div>
      </Popup>
    </Marker>
  );
}

export default ComplaintMarker;
