import { useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { ChartSpec } from '@/types';

// Brand-neutral, colorblind-aware categorical palette.
const PALETTE = [
  '#3366ff',
  '#00b8a9',
  '#f6a609',
  '#e8618c',
  '#8b5cf6',
  '#22c55e',
  '#ef4444',
  '#0ea5e9',
];

const AXIS_PROPS = {
  tick: { fontSize: 11, fill: 'currentColor' },
  stroke: 'currentColor',
} as const;

function toArray(value: string | string[] | undefined): string[] {
  if (!value) return [];
  return Array.isArray(value) ? value : [value];
}

interface ChartRendererProps {
  spec: ChartSpec;
  height?: number;
}

export default function ChartRenderer({ spec, height = 300 }: ChartRendererProps) {
  const { type, x, y, data, image_b64 } = spec;
  const yKeys = useMemo(() => toArray(y), [y]);

  // Server pre-rendered image fallback (e.g. heatmap / matplotlib output).
  if (image_b64) {
    return (
      <img
        src={`data:image/png;base64,${image_b64}`}
        alt={spec.title}
        className="max-h-[420px] w-full rounded-lg object-contain"
      />
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-slate-400">
        No chart data.
      </div>
    );
  }

  const tooltipStyle = {
    contentStyle: {
      borderRadius: 8,
      border: '1px solid rgba(148,163,184,0.3)',
      fontSize: 12,
      background: 'rgba(15,23,42,0.92)',
      color: '#fff',
    },
  } as const;

  const commonCartesian = (
    <>
      <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
      <XAxis dataKey={x} {...AXIS_PROPS} />
      <YAxis {...AXIS_PROPS} />
      <Tooltip {...tooltipStyle} />
      {yKeys.length > 1 && <Legend wrapperStyle={{ fontSize: 12 }} />}
    </>
  );

  const render = () => {
    switch (type) {
      case 'line':
        return (
          <LineChart data={data}>
            {commonCartesian}
            {yKeys.map((key, i) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={PALETTE[i % PALETTE.length]}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        );

      case 'area':
        return (
          <AreaChart data={data}>
            {commonCartesian}
            {yKeys.map((key, i) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={PALETTE[i % PALETTE.length]}
                fill={PALETTE[i % PALETTE.length]}
                fillOpacity={0.2}
                strokeWidth={2}
              />
            ))}
          </AreaChart>
        );

      case 'bar':
      case 'histogram':
        return (
          <BarChart data={data}>
            {commonCartesian}
            {(yKeys.length ? yKeys : ['value']).map((key, i) => (
              <Bar
                key={key}
                dataKey={key}
                fill={PALETTE[i % PALETTE.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        );

      case 'pie': {
        const nameKey = x ?? 'name';
        const valueKey = yKeys[0] ?? 'value';
        return (
          <PieChart>
            <Tooltip {...tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Pie
              data={data}
              nameKey={nameKey}
              dataKey={valueKey}
              cx="50%"
              cy="50%"
              outerRadius={110}
              innerRadius={50}
              paddingAngle={2}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
              ))}
            </Pie>
          </PieChart>
        );
      }

      case 'scatter':
        return (
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
            <XAxis dataKey={x} type="number" name={x} {...AXIS_PROPS} />
            <YAxis
              dataKey={yKeys[0] ?? 'y'}
              type="number"
              name={yKeys[0]}
              {...AXIS_PROPS}
            />
            <ZAxis range={[60, 60]} />
            <Tooltip {...tooltipStyle} cursor={{ strokeDasharray: '3 3' }} />
            <Scatter data={data} fill={PALETTE[0]} />
          </ScatterChart>
        );

      case 'heatmap':
      default:
        // Heatmap without server image: render as a simple grid fallback.
        return (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">
            Unsupported inline chart type: {type}
          </div>
        );
    }
  };

  return (
    <div className="text-slate-500 dark:text-slate-400">
      <ResponsiveContainer width="100%" height={height}>
        {render()}
      </ResponsiveContainer>
    </div>
  );
}
