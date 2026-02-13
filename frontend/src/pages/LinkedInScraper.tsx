import React, { useState } from 'react';
import { Linkedin, Loader2, Link as LinkIcon, Download, RefreshCw, FileCheck } from 'lucide-react';
import api from '../api';
import { motion } from 'framer-motion';

const LinkedInScraper = () => {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [resume, setResume] = useState<any | null>(null);

    const handleScrape = async () => {
        if (!url.trim()) return;
        setLoading(true);
        setResume(null);
        try {
            const response = await api.post('/linkedin/scrape', { query: url });
            setResume(response.data.resume);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadWord = async () => {
        if (!resume) return;
        try {
            const response = await api.post('/generate/export', resume, {
                responseType: 'blob',
            });
            const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.setAttribute('download', `${resume.contact?.name || 'resume'}.docx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error('Export failed:', err);
        }
    };

    return (
        <div className="space-y-8">
            <header>
                <h1 className="text-3xl font-bold mb-2 text-slate-900 tracking-tight">LinkedIn Scraper</h1>
                <p className="text-slate-500 font-medium tracking-tight">Convert public LinkedIn profiles into structured professional resumes instantly.</p>
            </header>

            <div className="glass-card p-12 max-w-4xl mx-auto border-blue-100 bg-white/80 shadow-lg shadow-blue-500/5">
                <div className="flex flex-col items-center gap-8">
                    <div className="w-24 h-24 bg-[#0077b5] rounded-[2rem] flex items-center justify-center shadow-xl shadow-[#0077b5]/20 rotate-12 hover:rotate-0 transition-transform cursor-pointer">
                        <Linkedin className="text-white w-12 h-12" />
                    </div>

                    <div className="text-center">
                        <h3 className="text-xl font-bold text-slate-800 mb-2">Social Profile Import</h3>
                        <p className="text-sm text-slate-500 font-medium">Paste the LinkedIn URL below to begin the extraction process.</p>
                    </div>

                    <div className="w-full relative group">
                        <LinkIcon className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-[#0077b5] transition-colors" />
                        <input
                            type="text"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            placeholder="https://www.linkedin.com/in/username"
                            className="w-full bg-white border border-slate-200 rounded-2xl py-5 pl-14 pr-4 focus:border-[#0077b5] outline-none text-lg transition-all shadow-sm focus:ring-4 focus:ring-[#0077b5]/5 text-slate-800 placeholder:text-slate-300"
                        />
                    </div>

                    <button
                        onClick={handleScrape}
                        disabled={loading || !url.trim()}
                        className="bg-[#0077b5] hover:bg-[#006396] text-white px-12 py-5 rounded-2xl font-black uppercase tracking-widest text-sm transition-all disabled:opacity-50 shadow-xl shadow-[#0077b5]/20 active:scale-95 flex items-center gap-3"
                    >
                        {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <RefreshCw className="w-5 h-5 shadow-sm" />}
                        {loading ? 'AI Scraper Active...' : 'Convert Profile'}
                    </button>
                </div>
            </div>

            {resume && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-4xl mx-auto space-y-4">
                    <div className="flex justify-between items-center px-4">
                        <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                            <FileCheck className="w-4 h-4 text-emerald-500" />
                            Generated Intelligence Output
                        </h3>
                        <button
                            onClick={handleDownloadWord}
                            className="text-[10px] font-black text-slate-600 hover:text-slate-900 transition-colors bg-white border border-slate-200 px-4 py-2 rounded-xl flex items-center gap-2 shadow-sm hover:shadow-md active:bg-slate-50"
                        >
                            <Download className="w-3.5 h-3.5" /> Download .docx
                        </button>
                    </div>

                    <div className="glass-card p-12 bg-white border-slate-100 shadow-2xl space-y-8 font-sans">
                        <div className="text-center space-y-2 border-b border-slate-100 pb-8">
                            <h2 className="text-4xl font-black text-slate-900">{resume.contact?.name}</h2>
                            <p className="text-slate-500 font-bold tracking-widest uppercase text-xs">
                                {resume.contact?.location} {resume.contact?.location && resume.contact?.email ? ' | ' : ''} {resume.contact?.email}
                            </p>
                        </div>

                        {resume.summary && (
                            <section className="space-y-3">
                                <h4 className="text-[10px] font-black text-[#0077b5] uppercase tracking-widest px-2 py-1 bg-blue-50 w-fit rounded-lg">Summary</h4>
                                <p className="text-slate-600 leading-relaxed text-sm font-medium">{resume.summary}</p>
                            </section>
                        )}

                        {resume.skills && resume.skills.length > 0 && (
                            <section className="space-y-3">
                                <h4 className="text-[10px] font-black text-[#0077b5] uppercase tracking-widest px-2 py-1 bg-blue-50 w-fit rounded-lg">Technical Expertise</h4>
                                <div className="flex flex-wrap gap-2">
                                    {resume.skills.map((skill: string, i: number) => (
                                        <span key={i} className="px-3 py-1.5 bg-slate-50 text-slate-600 rounded-full text-[11px] font-bold border border-slate-100">
                                            {skill}
                                        </span>
                                    ))}
                                </div>
                            </section>
                        )}

                        {resume.experience && resume.experience.length > 0 && (
                            <section className="space-y-6">
                                <h4 className="text-[10px] font-black text-[#0077b5] uppercase tracking-widest px-2 py-1 bg-blue-50 w-fit rounded-lg">Professional Experience</h4>
                                <div className="space-y-8">
                                    {resume.experience.map((exp: any, i: number) => (
                                        <div key={i} className="relative pl-6 border-l-2 border-slate-100 space-y-2">
                                            <div className="absolute -left-[9px] top-1 w-4 h-4 bg-white border-2 border-blue-500 rounded-full" />
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <h5 className="font-bold text-slate-900">{exp.title}</h5>
                                                    <p className="text-sm text-[#0077b5] font-black">{exp.company}</p>
                                                </div>
                                                <span className="text-[10px] font-black text-slate-400 bg-slate-50 px-3 py-1 rounded-full uppercase">{exp.period}</span>
                                            </div>
                                            <ul className="space-y-1.5 list-disc list-inside">
                                                {exp.bullets?.map((bullet: string, j: number) => (
                                                    <li key={j} className="text-sm text-slate-500 font-medium leading-relaxed marker:text-blue-500">{bullet}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )}

                        {resume.education && resume.education.length > 0 && (
                            <section className="space-y-4">
                                <h4 className="text-[10px] font-black text-[#0077b5] uppercase tracking-widest px-2 py-1 bg-blue-50 w-fit rounded-lg">Education</h4>
                                {resume.education.map((edu: any, i: number) => (
                                    <div key={i} className="flex justify-between items-center text-sm">
                                        <div>
                                            <span className="font-bold text-slate-900">{edu.degree}</span>
                                            <span className="mx-2 text-slate-300">•</span>
                                            <span className="text-slate-500 font-medium">{edu.school}</span>
                                        </div>
                                        <span className="text-[10px] font-black text-slate-400">{edu.year}</span>
                                    </div>
                                ))}
                            </section>
                        )}
                    </div>
                </motion.div>
            )}

            {!resume && !loading && (
                <div className="text-center py-20">
                    <p className="max-w-sm mx-auto text-xs text-slate-400 font-bold uppercase tracking-widest leading-relaxed">
                        Note: This feature uses automated browser agents to parse profile data and structure it into standardized blocks.
                    </p>
                </div>
            )}
        </div>
    );
};

export default LinkedInScraper;
