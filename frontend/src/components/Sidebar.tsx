import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
    BarChart3,
    Search,
    Upload,
    BrainCircuit,
    ShieldCheck,
    FileText,
    Linkedin,
    LogOut,
    LayoutDashboard
} from 'lucide-react';

import SettingsSidebar from './SettingsSidebar';

const Sidebar = () => {
    const navigate = useNavigate();
    const user = JSON.parse(localStorage.getItem('user') || '{}');

    const menuItems = [
        { name: 'Dashboard', icon: LayoutDashboard, path: '/' },
        { name: 'Upload', icon: Upload, path: '/upload' },
        { name: 'Semantic Search', icon: Search, path: '/search' },
        { name: 'Scoring', icon: BarChart3, path: '/scoring' },
        { name: 'Skill Gap', icon: BrainCircuit, path: '/skill-gap' },
        { name: 'Auto Screen', icon: ShieldCheck, path: '/screen' },
        { name: 'Resume Gen', icon: FileText, path: '/generate' },
        { name: 'LinkedIn', icon: Linkedin, path: '/linkedin' },
    ];

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/login');
    };

    return (
        <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen sticky top-0 shadow-sm z-10">
            <div className="p-6 border-b border-slate-100">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center shadow-md shadow-primary-500/20">
                        <BarChart3 className="text-white w-5 h-5" />
                    </div>
                    <span className="font-bold text-lg tracking-tight text-slate-900">ResumeAI</span>
                </div>
            </div>

            <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                {menuItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${isActive
                                ? 'bg-primary-50 text-primary-600 font-semibold border border-primary-100 shadow-sm'
                                : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
                            }`
                        }
                    >
                        <item.icon className={`w-5 h-5 ${location.pathname === item.path ? 'text-primary-600' : ''}`} />
                        <span className="text-sm">{item.name}</span>
                    </NavLink>
                ))}
            </nav>

            <SettingsSidebar />

            <div className="p-4 border-t border-slate-100 bg-slate-50/50">
                <div className="mb-4 px-3 py-2 bg-white rounded-lg border border-slate-200">
                    <p className="text-[10px] text-slate-400 uppercase tracking-widest font-black mb-1">Authenticated as</p>
                    <p className="text-sm font-semibold text-slate-700 truncate">{user.name || 'User'}</p>
                </div>
                <button
                    onClick={handleLogout}
                    className="flex items-center gap-3 px-3 py-2 w-full text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                >
                    <LogOut className="w-5 h-5" />
                    <span className="text-sm font-semibold">Logout</span>
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
