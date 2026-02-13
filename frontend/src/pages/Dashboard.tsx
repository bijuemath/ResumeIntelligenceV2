import React from 'react';
import { motion } from 'framer-motion';
import {
    Users,
    FileCheck,
    AlertCircle,
    CheckCircle2,
    ArrowUpRight
} from 'lucide-react';

const StatCard = ({ title, value, icon: Icon, color, trend }: any) => (
    <div className="glass-card p-6 p-relative group hover:border-primary-200 transition-all hover:shadow-md">
        <div className="flex justify-between items-start mb-4">
            <div className={`p-3 rounded-xl bg-${color}-50 border border-${color}-100`}>
                <Icon className={`text-${color}-600 w-6 h-6`} />
            </div>
            <button className="text-slate-300 hover:text-primary-500 transition-colors">
                <ArrowUpRight className="w-5 h-5" />
            </button>
        </div>
        <div>
            <h3 className="text-slate-500 text-sm font-semibold mb-1 uppercase tracking-tight">{title}</h3>
            <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-slate-900">{value}</span>
                {trend && <span className="text-emerald-600 text-xs font-bold bg-emerald-50 px-1.5 py-0.5 rounded">{trend}</span>}
            </div>
        </div>
    </div>
);

const Dashboard = () => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');

    return (
        <div className="space-y-8">
            <header>
                <h1 className="text-3xl font-bold mb-2 text-slate-900 tracking-tight">Welcome back, {user.name?.split(' ')[0] || 'User'}</h1>
                <p className="text-slate-500 font-medium">Here's what's happening with your recruitment pipeline today.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Total Resumes" value="128" icon={Users} color="primary" trend="+12% this week" />
                <StatCard title="Auto Screened" value="45" icon={FileCheck} color="emerald" trend="+5%" />
                <StatCard title="High Match" value="18" icon={CheckCircle2} color="blue" />
                <StatCard title="Skill Gaps" value="32" icon={AlertCircle} color="amber" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 glass-card p-8">
                    <h2 className="text-xl font-bold mb-6 text-slate-800">Recent Activity</h2>
                    <div className="space-y-6">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="flex gap-4 items-start pb-6 border-b border-slate-100 last:border-0 last:pb-0">
                                <div className="w-10 h-10 rounded-full bg-slate-100 flex-shrink-0 border border-slate-200" />
                                <div className="flex-1">
                                    <p className="text-sm font-semibold text-slate-700">Candidate <span className="text-primary-600">John Doe</span> was auto-screened</p>
                                    <p className="text-xs text-slate-500 mt-1 font-medium">2 hours ago • Overall Score: 85%</p>
                                </div>
                                <div className="text-emerald-600 text-[10px] font-black tracking-widest px-2 py-1 bg-emerald-50 border border-emerald-100 rounded underline decoration-2 underline-offset-2">SELECTED</div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="glass-card p-8">
                    <h2 className="text-xl font-bold mb-6 text-slate-800">Upcoming Actions</h2>
                    <div className="space-y-4">
                        <div className="p-4 bg-white rounded-lg border border-slate-200 border-l-primary-500 border-l-4 shadow-sm">
                            <p className="text-sm font-bold text-slate-800">Review Skill Analysis</p>
                            <p className="text-xs text-slate-500 mt-1 font-medium">Java Developer position</p>
                        </div>
                        <div className="p-4 bg-white rounded-lg border border-slate-200 border-l-amber-500 border-l-4 shadow-sm">
                            <p className="text-sm font-bold text-slate-800">Generate New Batch</p>
                            <p className="text-xs text-slate-500 mt-1 font-medium">Product Design roles</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
