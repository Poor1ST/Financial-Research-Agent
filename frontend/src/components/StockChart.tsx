import { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  LineChart,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Line,
  Bar,
  Area,
  ReferenceLine,
  Legend,
  Cell,
} from "recharts";
import { fetchChartData, type DataPoint, type ChartPeriod } from "../api/client";

interface Props {
  ticker: string;
  period: ChartPeriod;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

const C = {
  close: "#22d3ee",
  sma20: "#f59e0b",
  sma50: "#a78bfa",
  bb: "rgba(34, 211, 238, 0.08)",
  volUp: "#22c55e",
  volDown: "#ef4444",
  macd: "#6366f1",
  macdSig: "#f59e0b",
  macdHistUp: "#22c55e",
  macdHistDown: "#ef4444",
  rsi: "#a78bfa",
  grid: "rgba(148, 163, 184, 0.12)",
  text: "#94a3b8",
};

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 12px", fontSize: 13 }}>
      <div style={{ fontWeight: 600, marginBottom: 4, color: "var(--text)" }}>{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ display: "flex", justifyContent: "space-between", gap: 16, color: p.color }}>
          <span>{p.name}</span>
          <span style={{ fontFamily: '"JetBrains Mono", monospace', fontWeight: 600 }}>
            {typeof p.value === "number" ? p.value.toFixed(2) : p.value}
          </span>
        </div>
      ))}
    </div>
  );
}

function formatVol(v: number): string {
  if (v >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(1)}B`;
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}K`;
  return `${v}`;
}

export default function StockChart({ ticker, period }: Props) {
  const [chart, setChart] = useState<{ name: string; data: DataPoint[] } | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setErr(null);
    fetchChartData(ticker, period)
      .then((res) => { if (!cancelled) setChart(res); })
      .catch((e) => { if (!cancelled) setErr(e instanceof Error ? e.message : "Failed"); });
    return () => { cancelled = true; };
  }, [ticker, period]);

  if (err) return <div className="error-bar">{err}</div>;
  if (!chart) return <div className="loading-dots">Loading chart<span>.</span><span>.</span><span>.</span></div>;

  const { data, name } = chart;
  const latest = data[data.length - 1];
  const first = data[0];
  const isUp = latest.close >= first.close;
  const hasRsi = data.some((d) => d.rsi !== null);
  const hasMacd = data.some((d) => d.macd !== null);
  const hasBb = data.some((d) => d.bb_upper !== null);

  return (
    <div className="chart-container">
      <div className="chart-header">
        <div className="chart-title">{name} ({ticker})</div>
        <div className="chart-subtitle">
          <span className={isUp ? "text-up" : "text-down"} style={{ fontSize: 20, fontFamily: '"JetBrains Mono", monospace', fontWeight: 600 }}>
            ${latest.close.toFixed(2)}
          </span>
          <span style={{ color: "var(--text-muted)", marginLeft: 8, fontSize: 13 }}>
            {period} &middot; {data.length} days
          </span>
        </div>
      </div>

      <div className="chart-panel">
        <div className="chart-panel-title">Price &amp; Moving Averages</div>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={data}>
            <CartesianGrid stroke={C.grid} strokeDasharray="3 3" />
            <XAxis dataKey="date" tickFormatter={formatDate} stroke={C.text} tick={{ fontSize: 11 }} interval="preserveStartEnd" />
            <YAxis domain={["auto", "auto"]} stroke={C.text} tick={{ fontSize: 11 }} tickFormatter={(v: number) => `$${v.toFixed(0)}`} />
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 6 }} />
            {hasBb && <Area type="monotone" dataKey="bb_upper" stroke="none" fill={C.bb} name="BB Upper" />}
            {hasBb && <Area type="monotone" dataKey="bb_lower" stroke="none" fill={C.bb} name="BB Lower" />}
            <Line type="monotone" dataKey="close" stroke={C.close} strokeWidth={2} dot={false} name="Close" />
            <Line type="monotone" dataKey="sma20" stroke={C.sma20} strokeWidth={1.5} dot={false} name="SMA(20)" />
            <Line type="monotone" dataKey="sma50" stroke={C.sma50} strokeWidth={1.5} dot={false} name="SMA(50)" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-panel">
        <div className="chart-panel-title">Volume</div>
        <ResponsiveContainer width="100%" height={100}>
          <BarChart data={data}>
            <CartesianGrid stroke={C.grid} strokeDasharray="3 3" />
            <XAxis dataKey="date" tickFormatter={formatDate} stroke={C.text} tick={{ fontSize: 11 }} interval="preserveStartEnd" />
            <YAxis stroke={C.text} tick={{ fontSize: 11 }} tickFormatter={formatVol} />
            <Tooltip content={<ChartTooltip />} />
            <Bar dataKey="volume" opacity={0.7} name="Volume">
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.close >= entry.open ? C.volUp : C.volDown} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {hasRsi && (
        <div className="chart-panel">
          <div className="chart-panel-title">RSI (14)</div>
          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={data}>
              <CartesianGrid stroke={C.grid} strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={formatDate} stroke={C.text} tick={{ fontSize: 11 }} interval="preserveStartEnd" />
              <YAxis domain={[0, 100]} stroke={C.text} tick={{ fontSize: 11 }} />
              <Tooltip content={<ChartTooltip />} />
              <ReferenceLine y={70} stroke={C.volDown} strokeDasharray="4 4" strokeOpacity={0.5} />
              <ReferenceLine y={30} stroke={C.volUp} strokeDasharray="4 4" strokeOpacity={0.5} />
              <ReferenceLine y={50} stroke={C.grid} strokeDasharray="2 2" />
              <Line type="monotone" dataKey="rsi" stroke={C.rsi} strokeWidth={2} dot={false} name="RSI(14)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {hasMacd && (
        <div className="chart-panel">
          <div className="chart-panel-title">MACD (12, 26, 9)</div>
          <ResponsiveContainer width="100%" height={150}>
            <ComposedChart data={data}>
              <CartesianGrid stroke={C.grid} strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={formatDate} stroke={C.text} tick={{ fontSize: 11 }} interval="preserveStartEnd" />
              <YAxis stroke={C.text} tick={{ fontSize: 11 }} />
              <Tooltip content={<ChartTooltip />} />
              <ReferenceLine y={0} stroke={C.text} strokeOpacity={0.25} />
              <Bar dataKey="macd_hist" name="Histogram">
                {data.map((entry, i) => (
                  <Cell key={i} fill={(entry.macd_hist ?? 0) >= 0 ? C.macdHistUp : C.macdHistDown} />
                ))}
              </Bar>
              <Line type="monotone" dataKey="macd" stroke={C.macd} strokeWidth={2} dot={false} name="MACD" />
              <Line type="monotone" dataKey="macd_signal" stroke={C.macdSig} strokeWidth={2} dot={false} name="Signal" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
