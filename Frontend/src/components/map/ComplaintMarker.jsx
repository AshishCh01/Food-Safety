import { Link } from 'react-router-dom';
import { Marker, Popup } from 'react-leaflet';
import { priorityMarkerIcon } from './markerIcons';
import Badge from '../ui/Badge';
import { PRIORITIES, configFor } from '../../utils/statusConfig';

function ComplaintMarker({ marker }) {
  const priority = configFor(PRIORITIES, marker.priority);
  return (
    <Marker position={[marker.latitude, marker.longitude]} icon={priorityMarkerIcon(marker.priority)}>
      <Popup>
        <div className="min-w-44 text-left">
          <p className="font-mono text-xs text-slate-500">{marker.complaint_number}</p>
          <p className="mt-0.5 font-medium text-slate-900">{marker.title}</p>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-slate-600">
            <span>{marker.category_name}</span>
            <Badge tone={priority.tone}>{priority.label}</Badge>
          </div>
          {marker.business_name && <p className="mt-1 text-xs text-slate-500">{marker.business_name}</p>}
          <Link to={`/officer/complaints/${marker.id}`} className="mt-2 inline-block text-xs font-medium text-brand-700 hover:underline">
            View complaint
          </Link>
        </div>
      </Popup>
    </Marker>
  );
}

export default ComplaintMarker;
