import React from 'react';
import { MapPin, AlertTriangle, ShieldCheck, BarChart3, Settings } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
    const menuItems = [
        { id: 'map', label: 'GIS Fleet Map', icon: MapPin },
        { id: 'alerts', label: 'ANPR Violations', icon: ShieldCheck },
        { id: 'hazards', label: 'Road Hazards', icon: AlertTriangle },
        { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    ];

    return (
        <aside className="w-64 bg-[#161C28] border-r border-gray-800 flex flex-col justify-between p-4 text-gray-300">
            <div className="space-y-6">
                <div className="px-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Command Controls
                </div>
                <nav className="space-y-1">
                    {menuItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = activeTab === item.id;
                        return (
                            <button
                                key={item.id}
                                onClick={() => setActiveTab(item.id)}
                                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${isActive
                                        ? 'bg-[#00E5FF]/10 text-[#00E5FF] border border-[#00E5FF]/30'
                                        : 'hover:bg-gray-800/60 text-gray-400 hover:text-gray-200'
                                    }`}
                            >
                                <Icon className="w-4 h-4" />
                                {item.label}
                            </button>
                        );
                    })}
                </nav>
            </div>

            <div className="border-t border-gray-800 pt-4">
                <button className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-400 hover:text-white rounded-lg hover:bg-gray-800/60">
                    <Settings className="w-4 h-4" />
                    System Settings
                </button>
            </div>
        </aside>
    );
}

