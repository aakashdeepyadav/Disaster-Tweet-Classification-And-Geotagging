import React, { useMemo } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from 'recharts';

const COLORS = ['#ef4444', '#3b82f6', '#22c55e', '#eab308', '#a855f7', '#ec4899'];

function AnalyticsPanel({ results, loading = false }) {
  const disasterStats = useMemo(() => {
    const stats = { Disaster: 0, 'Not Disaster': 0 };
    results.forEach((r) => {
      if (r.disaster_label === 1) stats.Disaster++;
      else stats['Not Disaster']++;
    });
    return Object.entries(stats).map(([name, value]) => ({ name, value }));
  }, [results]);

  const categoryStats = useMemo(() => {
    const counts = {};
    results.forEach((r) => {
      const cat = r.category || 'Unknown';
      counts[cat] = (counts[cat] || 0) + 1;
    });
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10); // Top 10 categories
  }, [results]);

  const severityStats = useMemo(() => {
    const counts = {};
    results.forEach((r) => {
      const sev = r.severity || 'Unknown';
      counts[sev] = (counts[sev] || 0) + 1;
    });
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [results]);

  if (loading) {
    return (
      <div className="card">
        <div className="card-header">
          <h2>📈 Analytics Dashboard</h2>
          <p className="subtitle">Real-time statistics and insights</p>
        </div>
        <div className="empty-state">
          <div className="spinner" style={{ margin: '20px auto' }}></div>
          <p>Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (!results.length) {
    return (
      <div className="card">
        <div className="card-header">
          <h2>📈 Analytics Dashboard</h2>
          <p className="subtitle">Real-time statistics and insights</p>
        </div>
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <p>Analyze some tweets to see analytics.</p>
        </div>
      </div>
    );
  }

  const totalDisasters = disasterStats.find(s => s.name === 'Disaster')?.value || 0;
  const totalSafe = disasterStats.find(s => s.name === 'Not Disaster')?.value || 0;

  return (
    <div className="card">
      <div className="card-header">
        <h2>📈 Analytics Dashboard</h2>
        <p className="subtitle">
          {results.length} tweet{results.length > 1 ? 's' : ''} analyzed
        </p>
      </div>

      {/* Summary Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '12px',
        marginBottom: '24px'
      }}>
        <div style={{
          padding: '16px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: '12px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#ef4444' }}>
            {totalDisasters}
          </div>
          <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '4px' }}>
            Disasters
          </div>
        </div>
        <div style={{
          padding: '16px',
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.2)',
          borderRadius: '12px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#10b981' }}>
            {totalSafe}
          </div>
          <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '4px' }}>
            Safe
          </div>
        </div>
        <div style={{
          padding: '16px',
          background: 'rgba(99, 102, 241, 0.1)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          borderRadius: '12px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#6366f1' }}>
            {results.length}
          </div>
          <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '4px' }}>
            Total
          </div>
        </div>
      </div>

      <div className="charts-row">
        <div className="chart">
          <h3>Disaster vs Non-Disaster</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={disasterStats}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {disasterStats.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.name === 'Disaster' ? '#ef4444' : '#10b981'}
                  />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{
                  background: 'rgba(30, 37, 56, 0.95)',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  borderRadius: '8px',
                  color: '#f8fafc'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="chart">
          <h3>By Category</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={categoryStats} margin={{ top: 5, right: 5, bottom: 60, left: 5 }}>
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={80}
                fontSize={11}
                stroke="#94a3b8"
              />
              <YAxis allowDecimals={false} stroke="#94a3b8" />
              <Tooltip 
                contentStyle={{
                  background: 'rgba(30, 37, 56, 0.95)',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  borderRadius: '8px',
                  color: '#f8fafc'
                }}
              />
              <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                {categoryStats.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        {severityStats.length > 0 && (
          <div className="chart">
            <h3>By Severity</h3>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={severityStats}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {severityStats.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    background: 'rgba(30, 37, 56, 0.95)',
                    border: '1px solid rgba(99, 102, 241, 0.3)',
                    borderRadius: '8px',
                    color: '#f8fafc'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}

export default AnalyticsPanel;




