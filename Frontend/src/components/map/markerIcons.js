import { divIcon } from 'leaflet';
import { PRIORITY_COLORS } from '../../utils/statusConfig';

// Colored CSS dots via L.divIcon rather than Leaflet's default marker image
// (which needs its icon assets patched separately in a Vite build). Color
// communicates priority since that is the officer's primary triage signal;
// the popup carries status/category detail.

const DOT_STYLE =
  'display:block;width:16px;height:16px;border-radius:50%;border:2px solid #ffffff;box-shadow:0 0 2px rgba(0,0,0,0.6);';
const PIN_STYLE =
  'display:block;width:18px;height:18px;border-radius:50% 50% 50% 0;border:2px solid #ffffff;' +
  'transform:rotate(-45deg);box-shadow:0 0 2px rgba(0,0,0,0.6);background:#33587a;';

export function priorityMarkerIcon(priority) {
  const color = PRIORITY_COLORS[priority] || '#6b7280';
  return divIcon({
    className: 'complaint-marker-icon',
    html: `<span style="${DOT_STYLE}background:${color}"></span>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
    popupAnchor: [0, -8],
  });
}

export function locationPinIcon() {
  return divIcon({
    className: 'location-marker-icon',
    html: `<span style="${PIN_STYLE}"></span>`,
    iconSize: [18, 18],
    iconAnchor: [9, 18],
    popupAnchor: [0, -18],
  });
}
