import React, { useState } from 'react';
import { ShieldAlert, AlertTriangle, Droplets, CheckCircle, ExternalLink } from 'lucide-react';

const mockAlerts = [
    {
        id: 'ALT-1092',
        busId: 'BUS-104',
        type: 'ANPR Violation',
        desc: 'Hit-and-Run / Rash Driving',
        plate: 'KA-01-MJ-9821',
        confidence: '96.8%',
        time: 'Just now',
        severity: 'critical',
        location: '12.9716° N, 77.5946° E'
    },
    {
        id: 'ALT-1091',
        busId: 'BUS-212',
        type: 'Road Defect',
        desc: 'Severe Pothole Cluster',
        plate: 'N/A',
        confidence: '91.2%',
        time: '2 mins ago',
        severity: 'warning',
        location: '12.9352° N, 77.6245° E'
    },
    {
        id: 'ALT-1090',
        busId: 'BUS-088',
        type: 'Hazard',
        desc: 'Waterlogging / Drain Overflow',
        plate: 'N/A',
        confidence: '88.5%',
        time: '5 mins ago',
        severity: 'info',
        location: '12.9226° N, 77.5811° E'
    }
];

export default function LiveAlertFeed() {
    const [alerts, setAlerts] = useState(mockAlerts);

    return (
        <div className="w-80 bg-[#161C28] border-l border-gray-800 flex flex-col h-full text-white">
            <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 text-[#00E5FF]" />
                    <h2 className="font-semibold text-sm">Live Edge Incidents</h2>
                </div>
                <span className="text-xs bg-red-500/20 text-red-400 border border-red-500/40 px-2 py-0.5 rounded-full animate-pulse">
                    Live Stream
                </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-3">
                {alerts.map((alert) => (
                    <div
                        key={alert.id}
                        className="p-3 bg-[#0B0F17] rounded-lg border border-gray-800 hover:border-gray-700 transition-all space-y-2"
                    >
                        <div className="flex items-center justify-between">
                            <span
                                className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${alert.severity === 'critical'
                                        ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                                        : alert.severity === 'warning'
                                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                            : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                                    }`}
                            >
                                {alert.type}
                            </span>
                            <span className="text-[11px] text-gray-500">{alert.time}</span>
                        </div>

                        <div>
                            <p className="text-xs font-semibold text-gray-200">{alert.desc}</p>
                            <p className="text-[11px] text-gray-400">Reporter: {alert.busId}</p>
                        </div>

                        {alert.plate !== 'N/A' && (
                            <div className="p-2 bg-gray-900 rounded border border-gray-800 text-xs flex items-center justify-between">
                                <span className="font-mono text-[#00E5FF] font-bold">{alert.plate}</span>
                                <span className="text-[10px] text-gray-400">Conf: {alert.confidence}</span>
                            </div>
                        )}

                        <div className="flex items-center justify-between pt-1 text-[10px] text-gray-500">
                            <span className="truncate">{alert.location}</span>
                            <button className="text-[#00E5FF] hover:underline flex items-center gap-1">
                                Action <ExternalLink className="w-2.5 h-2.5" />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

