import React, { useState } from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { BloomDistributionItem } from '../../types/analytics';
import { getBloomConfig } from '../../config/bloomConfig';
import { CustomTooltip } from './CustomTooltip';
import { CustomLegend } from './CustomLegend';
import { useTheme } from '../../context/ThemeContext';

interface BloomDonutChartProps {
  data: BloomDistributionItem[];
  totalQuestions: number;
}

export const BloomDonutChart: React.FC<BloomDonutChartProps> = ({
  data,
  totalQuestions,
}) => {
  const [hoveredLevel, setHoveredLevel] = useState<string | null>(null);
  const { theme } = useTheme();

  const formattedChartData = data.map((item) => {
    const config = getBloomConfig(item.name || item.bloom_level);
    return {
      ...item,
      name: config.label,
      value: item.question_count,
      color: config.chartColor,
    };
  });

  const cellStroke = theme === 'dark' ? '#0f172a' : '#ffffff';

  return (
    <div className="space-y-4">
      <div className="relative h-64 w-full flex items-center justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Tooltip content={<CustomTooltip />} wrapperStyle={{ zIndex: 1000 }} />
            <Pie
              data={formattedChartData}
              cx="50%"
              cy="50%"
              innerRadius={65}
              outerRadius={95}
              paddingAngle={3}
              dataKey="value"
              animationDuration={800}
            >
              {formattedChartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color}
                  stroke={cellStroke}
                  strokeWidth={2}
                  opacity={hoveredLevel && hoveredLevel !== entry.name ? 0.4 : 1}
                />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        {/* Center Metric Text inside Donut Chart */}
        <div className="absolute inset-0 z-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-3xl font-extrabold font-mono text-slate-900 dark:text-white tracking-tight">
            {totalQuestions}
          </span>
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Questions
          </span>
        </div>
      </div>

      {/* Explicit Structured Legend */}
      <CustomLegend data={data} onHoverItem={setHoveredLevel} />
    </div>
  );
};
