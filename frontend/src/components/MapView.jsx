import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// Custom Map Marker Icons Setup
const busIcon = L.divIcon({
    className: 'custom-bus-icon',
    html: `<div style="background-color:#00A3FF; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-weight:bold; border:2px solid white; box-shadow:0 2px 8px rgba(0,0,0,0.3);">B</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14]
});

const hazardIcon = L.divIcon({
    className: 'custom-hazard-icon',
    html: `<div style="width:0; height:0; border-left:10px solid transparent; border-right:10px solid transparent; border-bottom:18px solid #EF4444; filter:drop-shadow(0 2px 4px rgba(0,0,0,0.3));"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10]
});

const mockData = [
    { id: 'BUS-104', type: 'bus', position: [22.7196, 75.8577], speed: '42 km/h', route: 'AB Road Corridor' },
    { id: 'BUS-208', type: 'bus', position: [22.7250, 75.8650], speed: '38 km/h', route: 'Vijay Nagar Square' },
    { id: 'DEFECT-01', type: 'defect', position: [22.7150, 75.8600], desc: 'Severe Pothole Detected', confidence: '94.2%' }
];

export default function ProfessionalMapView() {
    const [filter, setFilter] = useState('All');

    const filteredPoints = mockData.filter(item => {
        if (filter === 'Live Fleet') return item.type === 'bus';
        if (filter === 'Road Defects') return item.type === 'defect';
        return true;
    });

    return (
        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm flex flex-col h-[520px]">
            <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-gray-900 text-base">Live Fleet & City Intelligence Map</h2>
                <div className="flex gap-2 text-xs font-medium bg-gray-100 p-1 rounded-xl">
                    {['All', 'Live Fleet', 'Road Defects'].map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setFilter(tab)}
                            className={`px-3 py-1.5 rounded-lg transition-all ${filter === tab ? 'bg-[#00A3FF] text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            {tab}
                        </button>
                    ))}
                </div>
            </div>

            <div className="flex-1 rounded-xl overflow-hidden border border-gray-200 relative">
                <MapContainer center={[22.7196, 75.8577]} zoom={13} style={{ height: '100%', width: '100%' }}>
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
                                <div className="p-1 font-sans">
                                    <p className="font-bold text-gray-900 text-xs">{point.id}</p>
                                    {point.type === 'bus' ? (
                                        <>
                                            <p className="text-[11px] text-gray-600">Route: {point.route}</p>
                                            <p className="text-[11px] text-[#00A3FF] font-bold">Speed: {point.speed}</p>
                                        </>
                                    ) : (
                                        <>
                                            <p className="text-[11px] text-red-600 font-semibold">{point.desc}</p>
                                            <p className="text-[10px] text-gray-500">AI Conf: {point.confidence}</p>
                                        </>
                                    )}
                                </div>
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>
            </div>
        </div>
    );
}

