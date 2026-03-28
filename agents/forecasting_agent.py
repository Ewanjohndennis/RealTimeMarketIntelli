import argparse
import warnings
import math
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import feedparser
import yfinance as yf

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

import matplotlib
matplotlib.use("Agg")          # non-interactive backend (safe for Streamlit too)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

LOOKBACK      = 30    # how many past days the LSTM sees at once (sequence length)
EPOCHS        = 80    # training iterations (increase for better accuracy, slower training)
HIDDEN_SIZE   = 64    # number of LSTM neurons per layer
NUM_LAYERS    = 2     # stacked LSTM depth
LEARNING_RATE = 0.001
BATCH_SIZE    = 16
TRAIN_SPLIT   = 0.8   # 80% train / 20% test


# ─────────────────────────────────────────────────────────────────────────────
# 1.  LSTM MODEL DEFINITION
# ─────────────────────────────────────────────────────────────────────────────

class LSTMForecaster(nn.Module):
    """
    A stacked LSTM that takes a sequence of `lookback` timesteps
    and predicts the NEXT single value.

    Architecture:
        Input  → LSTM (hidden_size, num_layers) → Dropout → Linear → Output
    """

    def __init__(self, input_size=1, hidden_size=HIDDEN_SIZE,
                 num_layers=NUM_LAYERS, dropout=0.2):
        super(LSTMForecaster, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers  = num_layers

        self.lstm = nn.LSTM(
            input_size  = input_size,
            hidden_size = hidden_size,
            num_layers  = num_layers,
            batch_first = True,       # input shape: (batch, seq_len, features)
            dropout     = dropout if num_layers > 1 else 0.0
        )
        self.dropout = nn.Dropout(dropout)
        self.fc      = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)

        out, _ = self.lstm(x, (h0, c0))   # out: (batch, seq_len, hidden_size)
        out     = self.dropout(out[:, -1, :])  # take the LAST timestep only
        out     = self.fc(out)                 # (batch, 1)
        return out


# ─────────────────────────────────────────────────────────────────────────────
# 2.  DATA COLLECTION
# ─────────────────────────────────────────────────────────────────────────────

class DataCollector:
    """Fetches stock prices and builds a daily sentiment time series."""

    def __init__(self, ticker: str, topic: str, history_days: int = 180):
        self.ticker       = ticker
        self.topic        = topic
        self.history_days = history_days
        self.analyzer     = SentimentIntensityAnalyzer()

    # ── 2a. Stock Prices ──────────────────────────────────────────────────────

    def fetch_stock(self) -> pd.Series:
        """Returns a daily closing price Series indexed by date."""
        end   = datetime.today()
        start = end - timedelta(days=self.history_days)
        df    = yf.download(self.ticker, start=start, end=end,
                            progress=False, auto_adjust=True)
        if df.empty:
            raise ValueError(f"No stock data returned for ticker '{self.ticker}'."
                             " Check the ticker symbol.")
        series = df["Close"].squeeze()
        series.index = pd.to_datetime(series.index).normalize()
        series.name  = "stock_price"
        print(f"[DataCollector] Stock: {len(series)} days fetched for {self.ticker}")
        return series

    # ── 2b. News Sentiment ────────────────────────────────────────────────────

    def fetch_sentiment(self) -> pd.Series:
        """
        Pulls headlines from Google News RSS for `self.topic`,
        scores each with VADER, and returns a daily average compound
        sentiment series. Missing days are forward-filled.
        """
        encoded_topic = self.topic.replace(" ", "+")
        rss_url       = (f"https://news.google.com/rss/search?"
                         f"q={encoded_topic}&hl=en-US&gl=US&ceid=US:en")

        feed    = feedparser.parse(rss_url)
        records = []

        for entry in feed.entries:
            title  = entry.get("title", "")
            score  = self.analyzer.polarity_scores(title)["compound"]
            # published date varies in format; try multiple
            pub    = entry.get("published", entry.get("updated", ""))
            try:
                date = pd.to_datetime(pub, utc=True).normalize().tz_localize(None)
            except Exception:
                continue
            records.append({"date": date, "sentiment": score})

        if not records:
            print("[DataCollector] Warning: No RSS entries found. "
                  "Returning zero-sentiment series.")
            end   = datetime.today()
            dates = pd.date_range(end=end, periods=self.history_days, freq="D")
            return pd.Series(0.0, index=dates, name="sentiment")

        df_sent = (pd.DataFrame(records)
                   .groupby("date")["sentiment"]
                   .mean()
                   .rename("sentiment"))

        # Reindex to a full date range and forward-fill gaps (weekends / quiet days)
        end = pd.Timestamp.today().normalize()
        start     = end - timedelta(days=self.history_days)
        full_idx  = pd.date_range(start=start, end=end, freq="D")
        df_sent   = df_sent.reindex(full_idx).ffill().bfill()
        df_sent.index.name = "date"

        print(f"[DataCollector] Sentiment: {len(df_sent)} days, "
              f"{len(records)} headlines scored")
        return df_sent

    # ── 2c. Industry Trend Score ──────────────────────────────────────────────

    @staticmethod
    def build_trend(stock: pd.Series, sentiment: pd.Series) -> pd.Series:
        """
        Composite industry trend score.

        Formula:
            trend = 0.6 × normalised_price_momentum  +  0.4 × sentiment

        Price momentum = 7-day rolling % change (captures direction, not magnitude).
        Both inputs are normalised to [-1, 1] before combining.
        """
        # Align on shared dates
        combined = pd.DataFrame({"price": stock, "sentiment": sentiment}).dropna()

        momentum = combined["price"].pct_change(7).fillna(0)

        def normalise(s):
            mn, mx = s.min(), s.max()
            if mx == mn:
                return pd.Series(0.0, index=s.index)
            return 2 * (s - mn) / (mx - mn) - 1   # maps to [-1, 1]

        norm_mom  = normalise(momentum)
        norm_sent = normalise(combined["sentiment"])

        trend = (0.6 * norm_mom + 0.4 * norm_sent).rename("industry_trend")
        print(f"[DataCollector] Trend score built: {len(trend)} days")
        return trend


# ─────────────────────────────────────────────────────────────────────────────
# 3.  SEQUENCE PREPARATION
# ─────────────────────────────────────────────────────────────────────────────

def make_sequences(data: np.ndarray, lookback: int):
    """
    Converts a 1-D array into (X, y) pairs for supervised LSTM training.

    Example with lookback=3, data=[1,2,3,4,5]:
        X = [[1,2,3], [2,3,4]]
        y = [4, 5]
    """
    X, y = [], []
    for i in range(len(data) - lookback):
        X.append(data[i : i + lookback])
        y.append(data[i + lookback])
    return np.array(X), np.array(y)


# ─────────────────────────────────────────────────────────────────────────────
# 4.  TRAINING & EVALUATION
# ─────────────────────────────────────────────────────────────────────────────

def train_lstm(series: pd.Series,
               forecast_days: int,
               label: str,
               lookback: int   = LOOKBACK,
               epochs: int     = EPOCHS) -> dict:
    """
    Full pipeline: scale → sequence → train → evaluate → forecast.

    Returns a dict with:
        historical   : original pd.Series
        forecast     : pd.Series of future predictions
        rmse         : float (test-set Root Mean Squared Error, original scale)
        train_losses : list of per-epoch loss values
        plot_fig     : matplotlib Figure ready to display or save
    """
    print(f"\n[LSTM] Training for: {label}")

    # ── 4a. Scale to [0, 1] ──────────────────────────────────────────────────
    scaler = MinMaxScaler(feature_range=(0, 1))
    values = series.values.reshape(-1, 1).astype(np.float32)
    scaled = scaler.fit_transform(values).flatten()

    # ── 4b. Train / Test split ────────────────────────────────────────────────
    split      = int(len(scaled) * TRAIN_SPLIT)
    train_data = scaled[:split]
    test_data  = scaled[split:]

    if len(train_data) <= lookback or len(test_data) <= lookback:
        raise ValueError(f"Not enough data for '{label}'. "
                         f"Need > {lookback * 2} days, got {len(scaled)}.")

    X_train, y_train = make_sequences(train_data, lookback)
    X_test,  y_test  = make_sequences(test_data,  lookback)

    # Reshape for PyTorch: (samples, seq_len, features)
    to_tensor = lambda a: torch.tensor(a, dtype=torch.float32).unsqueeze(-1)
    X_tr = to_tensor(X_train)
    y_tr = torch.tensor(y_train, dtype=torch.float32).unsqueeze(-1)
    X_te = to_tensor(X_test)
    y_te = torch.tensor(y_test,  dtype=torch.float32).unsqueeze(-1)

    train_loader = DataLoader(TensorDataset(X_tr, y_tr),
                              batch_size=BATCH_SIZE, shuffle=True)

    # ── 4c. Model, Loss, Optimiser ────────────────────────────────────────────
    model     = LSTMForecaster()
    criterion = nn.MSELoss()
    optimiser = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = torch.optim.lr_scheduler.StepLR(optimiser, step_size=30, gamma=0.5)

    # ── 4d. Training Loop ─────────────────────────────────────────────────────
    train_losses = []
    model.train()
    for epoch in range(1, epochs + 1):
        epoch_loss = 0.0
        for xb, yb in train_loader:
            optimiser.zero_grad()
            pred  = model(xb)
            loss  = criterion(pred, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # stability
            optimiser.step()
            epoch_loss += loss.item()
        scheduler.step()
        avg_loss = epoch_loss / len(train_loader)
        train_losses.append(avg_loss)
        if epoch % 20 == 0:
            print(f"   Epoch {epoch:3d}/{epochs}  loss={avg_loss:.6f}")

    # ── 4e. Test Evaluation (RMSE) ────────────────────────────────────────────
    model.eval()
    with torch.no_grad():
        test_preds_scaled = model(X_te).numpy().flatten()

    # Inverse-transform back to original scale
    test_preds = scaler.inverse_transform(
        test_preds_scaled.reshape(-1, 1)).flatten()
    test_actuals = scaler.inverse_transform(
        y_test.reshape(-1, 1)).flatten()

    rmse = math.sqrt(mean_squared_error(test_actuals, test_preds))
    print(f"   Test RMSE ({label}): {rmse:.4f}")

    # ── 4f. Future Forecast ───────────────────────────────────────────────────
    # Seed with the last `lookback` known values, then predict step-by-step
    seed     = scaled[-lookback:].copy()
    forecast_scaled = []

    model.eval()
    with torch.no_grad():
        for _ in range(forecast_days):
            inp    = torch.tensor(seed, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
            pred   = model(inp).item()
            forecast_scaled.append(pred)
            seed   = np.append(seed[1:], pred)   # slide window forward

    forecast_values = scaler.inverse_transform(
        np.array(forecast_scaled).reshape(-1, 1)).flatten()

    last_date      = series.index[-1]
    forecast_dates = pd.date_range(
        start=last_date + timedelta(days=1),
        periods=forecast_days,
        freq="D"
    )
    forecast_series = pd.Series(forecast_values,
                                index=forecast_dates,
                                name=f"{label}_forecast")

    # ── 4g. Plot ──────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle(f"LSTM Forecast — {label}", fontsize=14, fontweight="bold")

    # Top panel: historical + forecast
    ax1 = axes[0]
    ax1.plot(series.index, series.values, label="Historical", color="#2196F3", linewidth=1.5)
    ax1.plot(forecast_series.index, forecast_series.values,
             label=f"Forecast (+{forecast_days}d)", color="#FF5722",
             linestyle="--", linewidth=2)
    ax1.axvline(x=last_date, color="gray", linestyle=":", alpha=0.7, label="Forecast start")
    ax1.set_ylabel(label)
    ax1.legend(fontsize=9)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=30, ha="right")
    ax1.grid(alpha=0.3)
    ax1.set_title(f"RMSE on test set: {rmse:.4f}", fontsize=10, color="gray")

    # Bottom panel: training loss curve
    ax2 = axes[1]
    ax2.plot(range(1, epochs + 1), train_losses, color="#4CAF50", linewidth=1.5)
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("MSE Loss")
    ax2.set_title("Training Loss Curve")
    ax2.grid(alpha=0.3)

    plt.tight_layout()

    return {
        "historical"  : series,
        "forecast"    : forecast_series,
        "rmse"        : rmse,
        "train_losses": train_losses,
        "plot_fig"    : fig,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5.  FORECASTING AGENT  (main class to import into your project)
# ─────────────────────────────────────────────────────────────────────────────

class ForecastingAgent:
    """
    Drop-in forecasting agent for the RealTimeMarketIntelli system.

    Parameters
    ----------
    ticker       : str   – stock ticker symbol, e.g. "AAPL", "MSFT", "TSLA"
    topic        : str   – industry topic for RSS news, e.g. "electric vehicles"
    history_days : int   – how many days of history to train on (default 180)

    Example
    -------
        agent   = ForecastingAgent(ticker="NVDA", topic="semiconductor AI chips")
        results = agent.run(forecast_days=30)

        # Access results
        print(results["stock"]["rmse"])
        results["stock"]["plot_fig"].savefig("stock_forecast.png")
        print(results["sentiment"]["forecast"].tail())
    """

    def __init__(self, ticker: str, topic: str, history_days: int = 180):
        self.ticker       = ticker.upper()
        self.topic        = topic
        self.history_days = history_days
        self.collector    = DataCollector(ticker, topic, history_days)

    def run(self, forecast_days: int = 30) -> dict:
        """
        Collect data, train three LSTM models, return all results.

        Returns
        -------
        dict with keys "stock", "sentiment", "trend"
        Each value is itself a dict with:
            historical    : pd.Series  – actual historical data
            forecast      : pd.Series  – predicted future values
            rmse          : float      – test-set RMSE
            train_losses  : list[float]
            plot_fig      : matplotlib.figure.Figure
        """
        print(f"\n{'='*60}")
        print(f"  ForecastingAgent — {self.ticker} / '{self.topic}'")
        print(f"  History: {self.history_days} days  |  Forecast: {forecast_days} days")
        print(f"{'='*60}")

        # ── Collect ───────────────────────────────────────────────────────────
        stock_series     = self.collector.fetch_stock()
        sentiment_series = self.collector.fetch_sentiment()
        trend_series     = self.collector.build_trend(stock_series, sentiment_series)

        # Align all series to same date range (inner join)
        combined = pd.DataFrame({
            "stock"    : stock_series,
            "sentiment": sentiment_series,
            "trend"    : trend_series,
        }).dropna()

        # ── Train ─────────────────────────────────────────────────────────────
        results = {}

        results["stock"] = train_lstm(
            combined["stock"],
            forecast_days = forecast_days,
            label         = f"Stock Price ({self.ticker})",
        )
        results["sentiment"] = train_lstm(
            combined["sentiment"],
            forecast_days = forecast_days,
            label         = "News Sentiment Score",
        )
        results["trend"] = train_lstm(
            combined["trend"],
            forecast_days = forecast_days,
            label         = f"Industry Trend ({self.topic})",
        )

        # ── Summary ───────────────────────────────────────────────────────────
        print(f"\n{'='*60}")
        print("  FORECAST SUMMARY")
        print(f"{'='*60}")
        for key, res in results.items():
            fc  = res["forecast"]
            print(f"  {key:12s} | RMSE: {res['rmse']:.4f} | "
                  f"Next value: {fc.iloc[0]:.4f} | "
                  f"In {forecast_days}d: {fc.iloc[-1]:.4f}")
        print(f"{'='*60}\n")

        return results


# ─────────────────────────────────────────────────────────────────────────────
# 6.  STREAMLIT HELPER  (import this in your dashboard)
# ─────────────────────────────────────────────────────────────────────────────

def render_streamlit(results: dict):
    """
    Renders all three forecast panels inside a Streamlit app.

    Usage in your Streamlit page:
        from agents.forecasting_agent import ForecastingAgent, render_streamlit
        agent   = ForecastingAgent(ticker="AAPL", topic="AI chips")
        results = agent.run(forecast_days=30)
        render_streamlit(results)
    """
    try:
        import streamlit as st
    except ImportError:
        print("Streamlit not installed; skipping render.")
        return

    label_map = {
        "stock"    : "📈 Stock Price Forecast",
        "sentiment": "🗞️  News Sentiment Forecast",
        "trend"    : "🏭 Industry Trend Forecast",
    }

    for key, res in results.items():
        st.subheader(label_map.get(key, key))
        col1, col2 = st.columns([3, 1])

        with col1:
            st.pyplot(res["plot_fig"])

        with col2:
            fc = res["forecast"]
            st.metric("RMSE (test set)", f"{res['rmse']:.4f}")
            st.metric("Next day forecast", f"{fc.iloc[0]:.4f}")
            st.metric(f"In {len(fc)} days",  f"{fc.iloc[-1]:.4f}")
            direction = "↑ Upward" if fc.iloc[-1] > fc.iloc[0] else "↓ Downward"
            st.info(f"Trend direction: **{direction}**")

        with st.expander("View forecast table"):
            st.dataframe(
                res["forecast"].reset_index().rename(
                    columns={"index": "Date", 0: "Forecast"}
                ),
                use_container_width=True
            )
        st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# 7.  CLI ENTRYPOINT  (run directly: python forecasting_agent.py --ticker AAPL)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="LSTM Forecasting Agent – RealTimeMarketIntelli"
    )
    parser.add_argument("--ticker",  type=str, default="AAPL",
                        help="Stock ticker symbol (default: AAPL)")
    parser.add_argument("--topic",   type=str, default="artificial intelligence",
                        help="Industry topic for news sentiment")
    parser.add_argument("--days",    type=int, default=30,
                        help="Number of days to forecast ahead (default: 30)")
    parser.add_argument("--history", type=int, default=180,
                        help="Days of historical data to train on (default: 180)")
    parser.add_argument("--save",    action="store_true",
                        help="Save forecast plots as PNG files")
    args = parser.parse_args()

    agent   = ForecastingAgent(
        ticker       = args.ticker,
        topic        = args.topic,
        history_days = args.history,
    )
    results = agent.run(forecast_days=args.days)

    if args.save:
        for key, res in results.items():
            fname = f"forecast_{key}_{args.ticker}.png"
            res["plot_fig"].savefig(fname, dpi=150, bbox_inches="tight")
            print(f"[Saved] {fname}")
    else:
        plt.show()