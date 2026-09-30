// Distances always use original WGS84 coordinates, never scaled model geometry.
export function distanceMeters(a, b) {
  const rad = Math.PI / 180;
  const dLat = (b.lat - a.lat) * rad, dLon = (b.lon - a.lon) * rad;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLon / 2) ** 2;
  return 6371008.8 * 2 * Math.asin(Math.sqrt(Math.min(1, Math.max(0, h))));
}
export function formatDistance(meters) {
  return meters < 1000 ? `${Math.round(meters)} 米` : `${(meters / 1000).toFixed(2)} 公里`;
}
export function cleanStops(ids, places) {
  if (!Array.isArray(ids)) return [];
  return [...new Set(ids)].filter(id => typeof id === 'string' && Object.hasOwn(places, id));
}
export function routeMetrics(ids, places) {
  const stops = cleanStops(ids, places), legs = [];
  for (let i = 1; i < stops.length; i++) {
    const from = places[stops[i - 1]], to = places[stops[i]];
    legs.push({from, to, meters: distanceMeters(from, to), index: i});
  }
  return {stops, legs, total: legs.reduce((sum, leg) => sum + leg.meters, 0)};
}
export function moveStop(ids, id, delta) {
  const next = [...ids], from = next.indexOf(id), to = from + delta;
  if (from < 0 || to < 0 || to >= next.length) return next;
  [next[from], next[to]] = [next[to], next[from]];
  return next;
}
export function localDay(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}
export function validDay(day) {
  if (typeof day !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(day)) return false;
  const d = new Date(`${day}T12:00:00`);
  return !Number.isNaN(d.getTime()) && localDay(d) === day;
}
export function readPlans(raw, places) {
  try {
    const parsed = JSON.parse(raw), result = {};
    if (!parsed || parsed.version !== 1 || typeof parsed.days !== 'object' || !parsed.days) return result;
    for (const [day, ids] of Object.entries(parsed.days)) if (validDay(day)) result[day] = cleanStops(ids, places);
    return result;
  } catch { return {}; }
}

const LON_ORIGIN = 116.415, LAT_ORIGIN = 39.915;
const X_SCALE = 111320 * Math.cos(LAT_ORIGIN * Math.PI / 180) / 100;
export function toModelPosition(lon, lat) {
  return {x:(lon - LON_ORIGIN) * X_SCALE, y:(lat - LAT_ORIGIN) * 111320 / 100};
}
export function fromModelPosition(x, y) {
  return {lon:x / X_SCALE + LON_ORIGIN, lat:y * 100 / 111320 + LAT_ORIGIN};
}
export function insideMap(lon, lat) {
  return Number.isFinite(lon) && Number.isFinite(lat) && lon >= 116.345 && lon <= 116.485 && lat >= 39.865 && lat <= 39.965;
}
export function customPlace(record) {
  if (!record || typeof record.id !== 'string' || !/^user-[a-zA-Z0-9-]{1,80}$/.test(record.id)) return null;
  if (typeof record.name !== 'string' || !record.name.trim() || record.name.trim().length > 60 || !insideMap(record.lon,record.lat)) return null;
  const note = typeof record.note === 'string' ? record.note.slice(0,100) : '';
  return {id:record.id,name:record.name.trim(),lon:record.lon,lat:record.lat,note,custom:true,
    baiduUid:typeof record.baiduUid==='string'&&/^[a-zA-Z0-9_-]{1,100}$/.test(record.baiduUid)?record.baiduUid:undefined,
    ...toModelPosition(record.lon,record.lat),category:'我的地标',description:note || '这是你手动标记的位置，可与其他景点一起编排当天路线。',
    tip:'位置由你手动标记，可放大地图核对。',source:`https://www.openstreetmap.org/#map=18/${record.lat}/${record.lon}`};
}
export function readCustomPlaces(raw) {
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || parsed.version !== 1 || !Array.isArray(parsed.customPlaces)) return [];
    const unique = new Map();
    for (const record of parsed.customPlaces) { const place = customPlace(record); if (place) unique.set(place.id,place); }
    return [...unique.values()];
  } catch { return []; }
}
