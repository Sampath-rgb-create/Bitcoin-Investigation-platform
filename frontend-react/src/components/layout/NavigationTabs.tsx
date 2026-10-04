import React from 'react';
import { UploadCloud, AlertTriangle, Network, FileText } from 'lucide-react';

export type TabType = 'ingestion' | 'alerts' | 'graph' | 'reports';

interface NavigationTabsProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  alertCount?: number;
}

export const NavigationTabs: React.FC<NavigationTabsProps> = ({
  activeTab,
  onTabChange,
  alertCount = 42,
}) => {
  const tabs = [
    {
      id: 'ingestion' as TabType,
      label: 'Dataset Ingestion',
      icon: UploadCloud,
      badge: null,
    },
    {
      id: 'alerts' as TabType,
      label: 'Alerts & Evidence',
      icon: AlertTriangle,
      badge: alertCount > 0 ? alertCount : null,
      badgeColor: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
    },
    {
      id: 'graph' as TabType,
      label: 'Graph Canvas',
      icon: Network,
      badge: 'Live',
      badgeColor: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40',
    },
    {
      id: 'reports' as TabType,
      label: 'Forensic Reports',
      icon: FileText,
      badge: null,
    },
  ];

  return (
    <nav className="border-b border-slate-800 bg-[#090e17] px-4 flex space-x-1 select-none overflow-x-auto">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center space-x-2 py-3 px-4 text-xs font-medium border-b-2 transition-all duration-150 whitespace-nowrap ${
              isActive
                ? 'border-cyan-400 text-cyan-300 bg-cyan-950/20 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
            }`}
          >
            <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
            <span>{tab.label}</span>
            {tab.badge !== null && (
              <span
                className={`ml-1.5 px-1.5 py-0.2 text-[10px] font-mono rounded border ${
                  tab.badgeColor || 'bg-slate-800 text-slate-400 border-slate-700'
                }`}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
};
