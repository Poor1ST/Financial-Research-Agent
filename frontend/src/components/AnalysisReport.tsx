interface ReportData {
  asset: string;
  name?: string;
  price?: number;
  changePct?: number;
  direction: "bullish" | "bearish" | "neutral";
  confidence: "high" | "medium" | "low";
  support?: number;
  resistance?: number;
  rsi?: number;
  technicalSummary?: string;
  fundamentalSummary?: string;
  riskFactors?: string[];
  conclusion?: string;
}

export default function AnalysisReport({ data }: { data: ReportData }) {
  const confidenceDots = data.confidence === "high" ? 4 : data.confidence === "medium" ? 3 : 2;
  const isPriceUp = (data.changePct ?? 0) >= 0;

  return (
    <div className="report-card">
      <div className="report-header">
        <div className="report-asset">
          <div className="report-asset-name">{data.name || data.asset} ({data.asset})</div>
          {data.price !== undefined && (
            <div className="report-asset-price">
              ${data.price.toFixed(2)}
              {data.changePct !== undefined && (
                <span className={isPriceUp ? "text-up" : "text-down"} style={{ fontSize: 14, marginLeft: 8, fontWeight: 600 }}>
                  {isPriceUp ? "+" : ""}{data.changePct.toFixed(2)}%
                </span>
              )}
            </div>
          )}
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
          <span className={`report-badge ${data.direction}`}>{data.direction}</span>
          <div style={{ display: "flex", gap: 3 }}>
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                style={{
                  width: 8, height: 8, borderRadius: "50%",
                  background: i < confidenceDots ? "var(--accent)" : "var(--border)",
                  transition: "background 0.2s",
                }}
              />
            ))}
            <span style={{ fontSize: 11, color: "var(--text-muted)", marginLeft: 4 }}>
              {data.confidence === "high" ? "High" : data.confidence === "medium" ? "Medium" : "Low"} Confidence
            </span>
          </div>
        </div>
      </div>
      <div className="report-body">
        {(data.support !== undefined || data.resistance !== undefined || data.rsi !== undefined) && (
          <div className="report-levels">
            {data.support !== undefined && (
              <div className="report-level">
                <div className="report-level-label">Support</div>
                <div className="report-level-value text-down">${data.support.toFixed(2)}</div>
              </div>
            )}
            {data.resistance !== undefined && (
              <div className="report-level">
                <div className="report-level-label">Resistance</div>
                <div className="report-level-value text-up">${data.resistance.toFixed(2)}</div>
              </div>
            )}
            {data.rsi !== undefined && (
              <div className="report-level">
                <div className="report-level-label">RSI(14)</div>
                <div className="report-level-value text-neutral">{data.rsi.toFixed(1)}</div>
              </div>
            )}
          </div>
        )}

        {data.technicalSummary && (
          <div className="report-section">
            <div className="report-section-title">Technical Analysis</div>
            <div className="report-section-text">{data.technicalSummary}</div>
          </div>
        )}

        {data.fundamentalSummary && (
          <div className="report-section">
            <div className="report-section-title">Fundamental Context</div>
            <div className="report-section-text">{data.fundamentalSummary}</div>
          </div>
        )}

        {data.riskFactors && data.riskFactors.length > 0 && (
          <div className="report-section">
            <div className="report-section-title">Risk Factors</div>
            <ul className="report-risk">
              {data.riskFactors.map((risk, i) => (
                <li key={i}>{risk}</li>
              ))}
            </ul>
          </div>
        )}

        {data.conclusion && (
          <div className="report-conclusion">{data.conclusion}</div>
        )}
      </div>
    </div>
  );
}
