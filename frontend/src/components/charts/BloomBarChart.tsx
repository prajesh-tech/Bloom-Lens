import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from 'recharts';
import { BloomDistributionItem } from '../../types/analytics';
import { getBloomConfig } from '../../config/bloomConfig';
import { CustomTooltip } from './CustomTooltip';
import { useTheme } from '../../context/ThemeContext';

interface BloomBarChartProps {
  data: BloomDistributionItem[];
  metricType?: 'count' | 'marks_weighted';
}

export const BloomBarChart: React.FC<BloomBarChartProps> = ({
  data,
  metricType = 'marks_weighted',
}) => {
  const { theme } = useTheme();

  const chartData = data.map((item) => {
    const config = getBloomConfig(item.name || item.bloom_level);
    return {
      name: config.label,
      code: config.code,
      value: metricType === 'marks_weighted' ? item.marks_percentage : item.question_count_percentage,
      question_count: item.question_count,
      total_marks: item.total_marks,
      color: config.chartColor,
    };
  });

  const gridColor = theme === 'dark' ? '#334155' : '#e2e8f0';
  const axisColor = theme === 'dark' ? '#475569' : '#cbd5e1';
  const tickColor = theme === 'dark' ? '#94a3b8' : '#64748b';

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridColor} />
          <XAxis
            dataKey="code"
            tickLine={false}
            axisLine={{ stroke: axisColor }}
            tick={{ fill: tickColor, fontSize: 12, fontFamily: 'JetBrains Mono' }}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tick={{ fill: tickColor, fontSize: 11, fontFamily: 'JetBrains Mono' }}
            unit="%"
          />
          <Tooltip content={<CustomTooltip />} wrapperStyle={{ zIndex: 1000 }} />
          <Bar dataKey="value" radius={[6, 6, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`bar-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
