import React from 'react';
import { Bus, Activity, Wifi, Bell, ShieldAlert } from 'lucide-react';

export default function Header() {
    return (
        <header className="bg-[#161C28] border-b border-gray-800 px-6 py-3 flex items-center justify-between text-white">
            <div className="flex items-center gap-3">
                <ShieldAlert className="w-7 h-7 text-[#00E5FF]" />
                <div>
                    <h1 className="font-bold text-lg tracking-wide text-gray-100">
                        BHARAT ELECTRONICS LIMITED
                    </h1>
                    <p className="text-xs text-gray-400">AI Mobile Urban Intelligence Platform</p>
                </div>
            </div>

            <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-2 bg-[#0B0F17] px-3 py-1.5 rounded-full border border-gray-700">
                    <Bus className="w-4 h-4 text-[#00E5FF]" />
                    <span>Active Buses: <strong className="text-white">48/50</strong></span>
                </div>

                <div className="flex items-center gap-2 bg-[#0B0F17] px-3 py-1.5 rounded-full border border-gray-700">
                    <Activity className="w-4 h-4 text-green-400" />
                    <span>Health: <strong className="text-white">99.4%</strong></span>
                </div>

                <div className="flex items-center gap-2 bg-[#0B0F17] px-3 py-1.5 rounded-full border border-gray-700">
                    <Wifi className="w-4 h-4 text-[#00E5FF]" />
                    <span className="text-green-400">5G Edge Connected</span>
                </div>

                <button className="p-2 bg-[#0B0F17] hover:bg-gray-800 rounded-full border border-gray-700 relative">
                    <Bell className="w-4 h-4 text-gray-300" />
                    <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-ping"></span>
                </button>
            </div>
        </header>
    );
}