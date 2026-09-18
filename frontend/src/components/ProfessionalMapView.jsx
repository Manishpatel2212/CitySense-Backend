import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { motion } from 'framer-motion';

// Custom Map Markers Icons
const busIcon = L.divIcon({
    className: 'custom-bus-icon',
    html: `<div style="background-color:#00A3FF; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-weight:bold; font-size:12px; border:2px solid white; box-shadow:0 0 12px rgba(0,163,255,0.6);">B</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14]
});

const hazardIcon = L.divIcon({
    className: 'custom-hazard-icon',
    html: `<div style="width:0; height:0; border-left:11px solid transparent; border-right:11px solid transparent; border-bottom:20px solid #EF4444; filter:drop-shadow(0 0 6px rgba(239,68,68,0.7));"></div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11]
});

// Fleet positions remain local because this endpoint only provides potholes.
const mockData = [
    // --- BUSES (Blue Circular Markers) ---
    { id: 'BUS-104', type: 'bus', position: [22.7196, 75.8577], speed: '42 km/h', route: 'AB Road Corridor', driver: 'Rajesh Kumar', status: 'On Time' },
    { id: 'BUS-208', type: 'bus', position: [22.7250, 75.8650], speed: '38 km/h', route: 'Vijay Nagar Square', driver: 'Amit Singh', status: 'On Time' },
    { id: 'BUS-312', type: 'bus', position: [22.7310, 75.8800], speed: '45 km/h', route: 'Palasia Junction Line', driver: 'Vikram Sharma', status: 'On Time' },
    { id: 'BUS-405', type: 'bus', position: [22.7050, 75.8450], speed: '29 km/h', route: 'Bhawarkuan BRTS Route', driver: 'Sunil Verma', status: 'Slight Delay' },
    { id: 'BUS-519', type: 'bus', position: [22.7400, 75.8950], speed: '50 km/h', route: 'Dewas Naka Ring Road', driver: 'Ravi Patel', status: 'On Time' },
    { id: 'BUS-622', type: 'bus', position: [22.6920, 75.8320], speed: '33 km/h', route: 'Rau Circle Express', driver: 'Deepak Joshi', status: 'On Time' },
    { id: 'BUS-734', type: 'bus', position: [22.7550, 75.8900], speed: '41 km/h', route: 'MR-10 Bypass Corridor', driver: 'Anil Yadav', status: 'On Time' },

];

export default function ProfessionalMapView({ potholes, loading, error }) {
    const [filter, setFilter] = useState('All');
    const potholePoints = potholes.map((pothole) => ({
        id: pothole.potholeId,
        type: 'defect',
        position: [pothole.location.latitude, pothole.location.longitude],
        desc: `${pothole.severity} Pothole`,
        confidence: `${(Number(pothole.averageConfidence || 0) * 100).toFixed(1)}%`,
        area: `${pothole.location.latitude.toFixed(5)}, ${pothole.location.longitude.toFixed(5)}`,
        severity: pothole.severity,
        uniqueBusCount: pothole.uniqueBusCount,
        confirmationPercentage: pothole.confirmationPercentage,
        status: pothole.status
    }));
    const points = [...mockData, ...potholePoints];

    const filteredPoints = points.filter(item => {
        if (filter === 'Live Fleet') return item.type === 'bus';
        if (filter === 'Road Defects') return item.type === 'defect';
        return true;
    });

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm flex flex-col h-[540px]"
        >
            {/* Header & Filter Controls */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h2 className="font-bold text-gray-900 text-base">Live Fleet & City Intelligence Map</h2>
                    <p className="text-[11px] text-gray-400">7 Active Buses • {loading ? 'Loading' : potholes.length} AI Detected Defects</p>
                </div>
                <div className="flex gap-2 text-xs font-medium bg-gray-100 p-1 rounded-xl">
                    {['All', 'Live Fleet', 'Road Defects'].map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setFilter(tab)}
                            className={`px-3 py-1.5 rounded-lg transition-all ${filter === tab ? 'bg-[#00A3FF] text-white shadow-sm font-semibold' : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            {tab}
                        </button>
                    ))}
                </div>
            </div>

            {/* Map View Frame */}
            <div className="flex-1 rounded-xl overflow-hidden border border-gray-200 relative z-0">
                {error && <div className="absolute top-2 left-2 right-2 z-[1000] rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700 border border-red-200">{error}</div>}
                <MapContainer center={[22.7196, 75.8577]} zoom={12.5} style={{ height: '100%', width: '100%' }}>
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    {filteredPoints.map((point) => (
                        <Marker
                            key={point.id}
                            position={point.position}
                            icon={point.type === 'bus' ? busIcon : hazardIcon}
                        >
                            <Popup>
                                <div className="p-1 font-sans min-w-[150px]">
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="font-bold text-gray-900 text-xs">{point.id}</span>
                                        <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${point.type === 'bus' ? 'bg-sky-100 text-sky-700' : 'bg-red-100 text-red-700'
                                            }`}>
                                            {point.type === 'bus' ? 'BUS' : 'DEFECT'}
                                        </span>
                                    </div>

                                    {point.type === 'bus' ? (
                                        <div className="space-y-0.5 text-[11px]">
                                            <p className="text-gray-600"><span className="font-semibold text-gray-800">Route:</span> {point.route}</p>
                                            <p className="text-[#00A3FF] font-bold"><span className="text-gray-600 font-normal">Speed:</span> {point.speed}</p>
                                            <p className="text-gray-500 text-[10px]">Driver: {point.driver}</p>
                                        </div>
                                    ) : (
                                        <div className="space-y-0.5 text-[11px]">
                                            <p className="text-red-600 font-bold">{point.desc}</p>
                                            <p className="text-gray-600"><span className="font-semibold text-gray-800">Loc:</span> {point.area}</p>
                                            <p className="text-gray-500 text-[10px]">AI Confidence: <span className="font-semibold text-gray-700">{point.confidence}</span></p>
                                            <p className="text-gray-500 text-[10px]">Severity: <span className="font-semibold text-gray-700">{point.severity}</span></p>
                                            <p className="text-gray-500 text-[10px]">Buses: <span className="font-semibold text-gray-700">{point.uniqueBusCount}</span> | Confirmation: <span className="font-semibold text-gray-700">{point.confirmationPercentage}%</span></p>
                                            <p className="text-gray-500 text-[10px]">Status: <span className="font-semibold text-gray-700">{point.status}</span></p>
                                        </div>
                                    )}
                                </div>
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>
            </div>
        </motion.div>
    );
}