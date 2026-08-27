import { divIcon } from 'leaflet';

// Colored CSS dots via L.divIcon rather than Leaflet's default marker image
// (which needs its icon assets patched separately in a Vite build). Color
// communicates priority since that is the officer's primary triage signal;
// the popup carries status/category detail.
const PRIORITY_COLORS = {
  low: '#2563eb',
  medium: '#d97706',
  high: '#ea580c',
  critical: '#dc2626',
};

export function priorityMarkerIcon(priority) {
  const color = PRIORITY_COLORS[priority] || '#6b7280';
  return divIcon({
    className: 'complaint-marker-icon',
    html: `<span class="complaint-marker-dot" style="background:${color}"></span>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
    popupAnchor: [0, -8],
  });
}

export function locationPinIcon() {
  return divIcon({
    className: 'location-marker-icon',
    html: '<span class="location-marker-pin"></span>',
    iconSize: [18, 18],
    iconAnchor: [9, 18],
    popupAnchor: [0, -18],
  });
}
