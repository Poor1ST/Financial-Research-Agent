interface PriceData {
  name?: string;
  ticker: string;
  price: number;
  change: number;
  changePct: number;
  rsi?: number;
  sma20?: number;
  sma50?: number;
  volume?: number;
}

export default function PriceCard({ data }: { data: PriceData }) {
  const isUp = data.change >= 0;

  return (
    <div className="price-card">
      <div className="price-card-header">
        {data.name || data.ticker} ({data.ticker})
      </div>
      <div className="price-card-main">
        ${data.price.toFixed(2)}
        <span className={isUp ? "text-up" : "text-down"} style={{ fontSize: 16, marginLeft: 8, fontWeight: 600 }}>
          {isUp ? "+" : ""}
          {data.change.toFixed(2)} ({isUp ? "+" : ""}
          {data.changePct.toFixed(2)}%)
        </span>
      </div>
      {(data.rsi !== undefined || data.sma20 !== undefined) && (
        <div className="price-card-indicators">
          {data.rsi !== undefined && (
            <div className="price-card-ind">
              <span className="price-card-ind-label">RSI(14)</span>
              <span className="price-card-ind-value">{data.rsi.toFixed(1)}</span>
            </div>
          )}
          {data.sma20 !== undefined && (
            <div className="price-card-ind">
              <span className="price-card-ind-label">SMA(20)</span>
              <span className="price-card-ind-value">${data.sma20.toFixed(2)}</span>
            </div>
          )}
          {data.sma50 !== undefined && (
            <div className="price-card-ind">
              <span className="price-card-ind-label">SMA(50)</span>
              <span className="price-card-ind-value">${data.sma50.toFixed(2)}</span>
            </div>
          )}
          {data.volume !== undefined && (
            <div className="price-card-ind">
              <span className="price-card-ind-label">Volume</span>
              <span className="price-card-ind-value">{data.volume.toLocaleString()}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
