import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, ZoomControl } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { issueService } from '../services/api';
import { MapPoint, IssueType, IssueStatus } from '../types';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { MapPin, Search, Eye, RefreshCw, Filter, Layers, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

// Custom Marker Icons by Category
const createCustomIcon = (color: string) => {
  return L.divIcon({
    className: 'custom-map-marker bg-transparent border-0',
    html: `<div style="background-color: ${color}; width: 16px; height: 16px; border-radius: 50%; border: 2px solid #111827; box-shadow: 0 0 12px ${color}99, inset 0 0 4px rgba(255,255,255,0.6);"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
};

const categoryColors: Record<string, string> = {
  // Road defects
  'Pothole': '#ef4444',              // Red
  'Longitudinal Crack': '#f97316',   // Orange
  'Transverse Crack': '#fb923c',     // Light Orange
  'Alligator Crack': '#f59e0b',      // Amber
  'Damaged Road Surface': '#e11d48', // Crimson
  'Road Damage': '#f43f5e',          // Rose

  // Sanitation defects
  'Garbage Accumulation': '#10b981', // Emerald
  'Illegal Dumping': '#059669',      // Dark Emerald
  'Overflowing Garbage Bins': '#84cc16', // Lime

  // Drainage defects
  'Blocked Drains': '#0284c7',       // Sky
  'Overflowing Drains': '#0ea5e9',   // Light Sky
  'Waterlogging': '#3b82f6',         // Blue
  'Damaged Drainage Covers': '#06b6d4', // Cyan

  // Utility defects
  'Open Manhole': '#d946ef',         // Magenta
  'Broken Streetlight': '#eab308',   // Yellow
};

const defaultColor = '#10b981'; // Emerald

// Controller component to handle size invalidation and auto-fitting bounds
const MapController: React.FC<{ points: MapPoint[] }> = ({ points }) => {
  const map = useMap();

  useEffect(() => {
    // Invalidate map size to prevent gray tiles on initialization
    map.invalidateSize();
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 250);
    return () => clearTimeout(timer);
  }, [map]);

  useEffect(() => {
    if (points.length > 0) {
      const validCoords: L.LatLngTuple[] = points
        .filter(
          (pt) =>
            typeof pt.latitude === 'number' &&
            typeof pt.longitude === 'number' &&
            !isNaN(pt.latitude) &&
            !isNaN(pt.longitude) &&
            pt.latitude >= -90 &&
            pt.latitude <= 90 &&
            pt.longitude >= -180 &&
            pt.longitude <= 180
        )
        .map((pt) => [pt.latitude, pt.longitude]);

      if (validCoords.length > 0) {
        const bounds = L.latLngBounds(validCoords);
        map.fitBounds(bounds, { padding: [60, 60], maxZoom: 15 });
      }
    }
  }, [points, map]);

  return null;
};

export const PublicIssueMapPage: React.FC = () => {
  const [points, setPoints] = useState<MapPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Filters
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const loadMapData = async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const data = await issueService.getMapData();
      setPoints(Array.isArray(data) ? data : []);
    } catch (err: any) {
      console.error('Failed to load map data:', err);
      setFetchError(err?.response?.data?.detail || 'Unable to connect to municipal map service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMapData();
  }, []);

  const filteredPoints = points.filter((pt) => {
    // Strict coordinate validation
    if (
      typeof pt.latitude !== 'number' ||
      typeof pt.longitude !== 'number' ||
      isNaN(pt.latitude) ||
      isNaN(pt.longitude) ||
      pt.latitude < -90 ||
      pt.latitude > 90 ||
      pt.longitude < -180 ||
      pt.longitude > 180
    ) {
      return false;
    }
    if (selectedType !== 'ALL' && pt.issue_type !== selectedType) return false;
    if (selectedStatus !== 'ALL' && pt.status !== selectedStatus) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = pt.title?.toLowerCase().includes(q) || false;
      const matchAddress = pt.address?.toLowerCase().includes(q) || false;
      const matchType = pt.issue_type?.toLowerCase().includes(q) || false;
      if (!matchTitle && !matchAddress && !matchType) return false;
    }
    return true;
  });

  return (
    <div className="h-[calc(100vh-64px)] w-full flex flex-col relative overflow-hidden bg-civic-bg">
      {/* Floating Header & Filters */}
      <div className="absolute top-4 left-4 right-4 z-[400] pointer-events-none flex flex-col items-end gap-2">
        <motion.div 
          initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-7xl mx-auto flex items-center justify-between pointer-events-auto"
        >
          {/* Logo / Title area inside map */}
          <div className="bg-civic-card/90 backdrop-blur-md border border-civic-border p-3 rounded-2xl flex items-center gap-3 shadow-xl shadow-black/20">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-400">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white leading-tight">CivicVision Map</h1>
              <p className="text-[10px] text-slate-400 font-mono uppercase tracking-wider">
                Live Infrastructure Intel • {filteredPoints.length} Markers
              </p>
            </div>
          </div>

          {/* Controls toggle */}
          <div className="flex items-center gap-2">
            <button
              onClick={loadMapData}
              className="p-3 rounded-xl bg-civic-card/90 backdrop-blur-md hover:bg-slate-800 text-slate-300 border border-civic-border transition-colors shadow-lg shadow-black/20"
              title="Refresh Data"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-3 rounded-xl backdrop-blur-md border transition-all shadow-lg shadow-black/20 ${
                showFilters 
                  ? 'bg-cyan-500/20 border-cyan-500/30 text-cyan-300' 
                  : 'bg-civic-card/90 border-civic-border text-slate-300 hover:bg-slate-800'
              }`}
            >
              <Filter className="w-4 h-4" />
              <span className="text-sm font-semibold hidden sm:inline">Filters</span>
            </button>
          </div>
        </motion.div>

        {/* Expandable Filter Panel */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              className="w-full max-w-sm pointer-events-auto bg-civic-card/95 backdrop-blur-xl border border-civic-border p-4 rounded-2xl shadow-2xl shadow-black/40 mt-2 mr-auto sm:mr-0 sm:ml-auto"
            >
              <div className="space-y-4">
                <div>
                  <label className="text-[10px] font-mono text-slate-500 uppercase mb-1.5 block">Search Location / Category</label>
                  <div className="relative">
                    <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      placeholder="Search area, defect type..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-civic-bg border border-civic-border rounded-xl pl-9 pr-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50 transition-colors"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-[10px] font-mono text-slate-500 uppercase mb-1.5 block">Defect Category</label>
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    className="w-full bg-civic-bg border border-civic-border rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50 transition-colors"
                  >
                    <option value="ALL">All Categories ({Object.keys(IssueType).length})</option>
                    {Object.values(IssueType).map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[10px] font-mono text-slate-500 uppercase mb-1.5 block">Issue Status</label>
                  <select
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value)}
                    className="w-full bg-civic-bg border border-civic-border rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50 transition-colors"
                  >
                    <option value="ALL">All Statuses</option>
                    {Object.values(IssueStatus).map((s) => (
                      <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-civic-border flex justify-between items-center text-[10px] font-mono text-slate-500">
                <span>Showing {filteredPoints.length} of {points.length} records</span>
                {(selectedType !== 'ALL' || selectedStatus !== 'ALL' || searchQuery) && (
                  <button 
                    onClick={() => { setSelectedType('ALL'); setSelectedStatus('ALL'); setSearchQuery(''); }}
                    className="text-cyan-400 hover:underline"
                  >
                    Clear Filters
                  </button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Map Canvas Container */}
      <div className="flex-1 w-full h-full min-h-[400px] relative z-10 bg-[#090d16]">
        {fetchError && (
          <div className="absolute top-20 left-1/2 -translate-x-1/2 z-[450] bg-rose-500/20 border border-rose-500/40 text-rose-300 px-4 py-2 rounded-xl text-xs flex items-center gap-2 backdrop-blur-md">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{fetchError}</span>
          </div>
        )}

        {filteredPoints.length === 0 && !loading && !fetchError && (
          <div className="absolute top-24 left-1/2 -translate-x-1/2 z-[450] bg-slate-900/90 border border-slate-700/60 text-slate-300 px-5 py-2.5 rounded-xl text-xs flex items-center gap-2 shadow-2xl backdrop-blur-md">
            <MapPin className="w-4 h-4 text-cyan-400" />
            <span>
              {points.length === 0
                ? 'No infrastructure issues currently logged on the map.'
                : 'No issues match the selected filter criteria.'}
            </span>
          </div>
        )}

        <MapContainer
          center={[28.6139, 77.2090]}
          zoom={13}
          scrollWheelZoom={true}
          style={{ width: '100%', height: '100%', minHeight: '400px', background: '#090d16' }}
          className="dark-tiles"
          zoomControl={false}
        >
          <ZoomControl position="bottomright" />
          <MapController points={filteredPoints} />

          {/* OpenStreetMap Tile Layer */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
          />

          {filteredPoints.map((pt) => {
            const markerColor = categoryColors[pt.issue_type] || defaultColor;
            return (
              <Marker
                key={pt.id}
                position={[pt.latitude, pt.longitude]}
                icon={createCustomIcon(markerColor)}
              >
                <Popup minWidth={280} maxWidth={340} className="civic-popup">
                  <div className="p-1 space-y-3">
                    {pt.image_url && (
                      <div className="relative rounded-xl overflow-hidden h-36 bg-slate-900 border border-civic-border">
                        <img 
                          src={pt.image_url} 
                          alt={pt.title} 
                          className="w-full h-full object-cover" 
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                        <div className="absolute top-2 right-2">
                          <StatusBadge status={pt.status} />
                        </div>
                      </div>
                    )}
                    
                    <div>
                      <div className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wide mb-1">
                        {pt.issue_type}
                      </div>
                      <h4 className="text-sm font-bold text-white line-clamp-2 leading-tight">{pt.title}</h4>
                      <p className="text-[11px] text-slate-400 line-clamp-2 mt-1.5 flex items-start gap-1">
                        <MapPin className="w-3 h-3 shrink-0 mt-0.5 text-slate-500" /> 
                        {pt.address || `${pt.latitude.toFixed(4)}, ${pt.longitude.toFixed(4)}`}
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-2 p-2 bg-civic-bg rounded-lg border border-civic-border">
                      <div>
                        <div className="text-[9px] text-slate-500 uppercase font-mono">Reported</div>
                        <div className="text-xs text-slate-300 mt-0.5">{new Date(pt.created_at).toLocaleDateString()}</div>
                      </div>
                      <div>
                        <div className="text-[9px] text-slate-500 uppercase font-mono">Department</div>
                        <div className="text-xs text-slate-300 mt-0.5 truncate">{pt.department || 'Pending'}</div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-civic-border">
                      <PriorityBadge score={pt.priority_score} severity={pt.severity} />
                      <Link
                        to={`/issue/${pt.id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 text-[11px] font-semibold transition-colors"
                      >
                        Inspect <Eye className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>

        {/* Floating Map Legend */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.5 }}
          className="absolute bottom-6 left-4 z-[400] pointer-events-auto bg-civic-card/90 backdrop-blur-md p-4 rounded-2xl border border-civic-border shadow-xl shadow-black/20 hidden md:block w-72 max-h-64 overflow-y-auto"
        >
          <div className="flex items-center gap-2 mb-3">
            <Layers className="w-4 h-4 text-slate-400" />
            <h4 className="text-xs font-bold text-slate-200">Category Legend</h4>
          </div>
          <div className="grid grid-cols-1 gap-2 text-[11px] font-medium text-slate-400">
            {Object.entries(categoryColors).map(([cat, col]) => (
              <div key={cat} className="flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 rounded-full border border-civic-card ring-1 ring-slate-700 shrink-0" style={{ backgroundColor: col, boxShadow: `0 0 6px ${col}80` }} />
                <span className="truncate">{cat}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};
