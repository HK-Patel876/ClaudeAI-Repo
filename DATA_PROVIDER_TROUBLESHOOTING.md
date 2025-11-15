# Data Provider Troubleshooting Guide

## Overview

This guide helps diagnose and fix data fetching issues in the AI Trading System. The system uses a multi-provider fallback strategy with comprehensive error handling.

## System Architecture

### Data Provider Hierarchy

The system tries providers in this order:

1. **Alpaca** (stocks & crypto) - Requires API key
2. **Polygon.io** (stocks) - Requires API key
3. **Alpha Vantage** (stocks) - Requires API key
4. **yfinance** (stocks & crypto) - No API key required (fallback)

### Error Handling Features

- **Retry Logic**: Automatic retry with exponential backoff (3 attempts)
- **Timeouts**: 30 seconds for real-time data, 60 seconds for historical
- **Circuit Breakers**: Temporarily disable failing providers (5 failures → 5-minute cooldown)
- **Data Validation**: Validates price ranges, OHLC relationships, required fields
- **Detailed Logging**: Categorized error messages (network, auth, rate limit, etc.)

## Quick Diagnostics

### Check Provider Status

The system logs provider status on startup. Look for these messages:

```
✅ Available providers: yfinance, alpaca
🟢 Active providers: yfinance
```

- **Available**: Provider is configured and initialized
- **Active**: Provider successfully returned data in last 5 minutes

### Common Log Messages

| Message | Meaning | Action |
|---------|---------|--------|
| `✅ yfinance: AAPL = $150.00` | Success | No action needed |
| `⚠️ No historical data returned` | Empty response | Check symbol format |
| `❌ All providers failed` | Complete failure | See troubleshooting below |
| `🎲 Using demo data` | Fallback mode | Check provider configuration |
| `Circuit breaker opened` | Provider disabled | Wait 5 minutes or fix root cause |

## Troubleshooting by Error Type

### 1. "All Providers Failed"

**Symptoms:**
- System uses demo/random data
- Log shows: `❌ All providers failed for SYMBOL`

**Diagnosis:**
```bash
# Check backend logs for detailed errors
tail -f backend/logs/app.log | grep "failed for"

# Look for specific error messages:
# - "Network error" → Connection issues
# - "Authentication failed" → Invalid API keys
# - "Rate limit exceeded" → Too many requests
# - "Invalid symbol" → Symbol format wrong
# - "No data available" → Symbol not found
```

**Solutions:**

#### a) No API Keys Configured (Expected)
```bash
# This is normal! yfinance should work without keys
# Check if yfinance is available:
grep "yfinance available" backend/logs/app.log

# If yfinance failed, check internet connection
ping yahoo.com
```

#### b) Network Issues
```bash
# Test connectivity to data providers
curl -I https://data.alpaca.markets
curl -I https://www.alphavantage.co
curl -I https://api.polygon.io

# Check if system can access yfinance
python3 -c "import yfinance; print(yfinance.Ticker('AAPL').history(period='1d'))"
```

#### c) yfinance Specific Issues
```bash
# Update yfinance to latest version
pip install --upgrade yfinance

# Test yfinance directly
python3 << EOF
import yfinance as yf
ticker = yf.Ticker("AAPL")
print("Info:", ticker.info.get('currentPrice', 'N/A'))
print("History:", ticker.history(period="1d"))
EOF
```

### 2. "Circuit Breaker Opened"

**Symptoms:**
- Provider stops being tried
- Log shows: `Circuit breaker opened after 5 failures`

**Diagnosis:**
```bash
# Check provider status
curl http://localhost:8000/api/v1/system/providers
```

**Solutions:**

#### a) Wait for Automatic Reset
- Circuit breakers automatically reset after 5 minutes
- Monitor logs for: `Circuit breaker entering half-open state`

#### b) Fix Underlying Issue
- Check the last error message for the provider
- Fix configuration (API keys, network, etc.)
- Restart the backend to reset circuit breakers immediately

### 3. "Authentication Failed"

**Symptoms:**
- Log shows: `Authentication failed: unauthorized` or `invalid key`
- Specific provider consistently fails

**Solutions:**

```bash
# Check .env file has correct API keys
cat .env | grep -E "ALPACA|ALPHA_VANTAGE|POLYGON"

# Verify API key format (no extra spaces, quotes)
# Correct: ALPACA_API_KEY=PK1234567890
# Wrong:   ALPACA_API_KEY="PK1234567890"
# Wrong:   ALPACA_API_KEY = PK1234567890

# Test API key directly
curl -H "APCA-API-KEY-ID: YOUR_KEY" \
     -H "APCA-API-SECRET-KEY: YOUR_SECRET" \
     https://paper-api.alpaca.markets/v2/account
```

### 4. "Rate Limit Exceeded"

**Symptoms:**
- Log shows: `Rate limit exceeded` or `too many requests`
- Provider works intermittently

**Solutions:**

1. **Reduce request frequency** (if using auto-trading)
2. **Upgrade API plan** (free tiers have limits)
3. **Use different provider** (system auto-falls back)
4. **Implement caching** (reduce API calls)

### 5. "Invalid Symbol"

**Symptoms:**
- Log shows: `Invalid symbol` or `not found`
- Only affects specific symbols

**Solutions:**

Check symbol format for each provider:

| Provider | Format | Example |
|----------|--------|---------|
| yfinance | Yahoo format | `AAPL`, `MSFT`, `BTC-USD` |
| Alpaca | Simple ticker | `AAPL`, `TSLA` |
| Alpaca Crypto | Pair format | `BTC/USD`, `ETH/USD` |
| Polygon | Simple ticker | `AAPL`, `GOOGL` |

```bash
# Test different symbol formats
# Stock: AAPL (works everywhere)
# Crypto: BTC-USD (yfinance), BTC/USD (Alpaca)
```

### 6. "Empty Data / No Data Available"

**Symptoms:**
- Provider returns empty response
- Log shows: `No historical data returned`

**Possible Causes:**

1. **Market Closed**: Some providers don't return data outside trading hours
2. **Delisted Stock**: Symbol no longer traded
3. **Invalid Date Range**: Requesting data before IPO
4. **Unsupported Asset**: Provider doesn't support this asset type

**Solutions:**

```bash
# Try a well-known symbol
curl "http://localhost:8000/api/v1/data/price/AAPL"

# Check if market is open
date  # Check current time
# US market: 9:30 AM - 4:00 PM ET, Mon-Fri

# Try different timeframe
curl "http://localhost:8000/api/v1/data/market/AAPL?days=30"
```

## Advanced Debugging

### Enable Debug Logging

Edit `backend/app/core/config.py`:

```python
DEBUG: bool = True  # Enable verbose logging
```

Restart backend and check logs for detailed error information.

### Check Provider Statistics

```bash
# Get detailed provider status
curl http://localhost:8000/api/v1/system/providers | jq

# Example output:
{
  "yfinance": {
    "available": true,
    "active": true,
    "circuit_breaker_state": "closed",
    "can_attempt": true,
    "success_count": 42,
    "error_count": 3,
    "success_rate": 0.93,
    "last_error_msg": null
  }
}
```

### Manual Provider Test

Create `backend/test_providers.py`:

```python
import asyncio
from app.core.config import settings
from app.services.multi_source_data import MultiSourceDataService

async def test():
    service = MultiSourceDataService(settings)

    print("Testing Providers...")
    print("=" * 50)

    # Test price fetch
    symbols = ["AAPL", "MSFT", "TSLA"]
    for symbol in symbols:
        price = await service.get_price(symbol)
        print(f"{symbol}: ${price}" if price else f"{symbol}: FAILED")

    # Show provider status
    print("\nProvider Status:")
    print("=" * 50)
    status = service.get_provider_status()
    for provider, info in status.items():
        print(f"{provider}:")
        print(f"  Available: {info['available']}")
        print(f"  Success Rate: {info['success_rate']:.1%}")
        if info['last_error_msg']:
            print(f"  Last Error: {info['last_error_msg']}")

if __name__ == "__main__":
    asyncio.run(test())
```

Run it:
```bash
cd backend
python test_providers.py
```

### Monitor Real-Time Logs

```bash
# Watch all data provider activity
tail -f backend/logs/app.log | grep -E "✅|⚠️|❌"

# Watch specific provider
tail -f backend/logs/app.log | grep "yfinance"

# Watch errors only
tail -f backend/logs/app.log | grep -E "ERROR|WARNING"
```

## Configuration Best Practices

### 1. Start Simple

```bash
# .env - minimal configuration
# Leave API keys blank - yfinance works without them
ALPACA_API_KEY=
ALPHA_VANTAGE_API_KEY=
POLYGON_API_KEY=
```

### 2. Add Providers Incrementally

1. **First**: Verify yfinance works
2. **Then**: Add Alpaca for real-time data
3. **Finally**: Add Polygon/Alpha Vantage for redundancy

### 3. Test Each Provider

After adding API keys, test individually:

```bash
# Restart backend
pkill -f uvicorn
cd backend && python -m uvicorn app.main:app --reload

# Check logs for initialization
grep "initialized" backend/logs/app.log

# Test via API
curl http://localhost:8000/api/v1/data/price/AAPL
```

## Common Issues & Solutions

### yfinance Returns Empty Data

```bash
# Update to latest version
pip install --upgrade yfinance

# Clear yfinance cache
rm -rf ~/.cache/py-yfinance

# Test with different symbol
python3 -c "import yfinance; print(yfinance.Ticker('SPY').history(period='5d'))"
```

### All Providers Timeout

```bash
# Increase timeout in code
# Edit backend/app/services/multi_source_data.py
REQUEST_TIMEOUT = 60.0  # Increase from 30 to 60 seconds

# Check system time (important for API authentication)
date
# If wrong: sudo ntpdate pool.ntp.org
```

### Intermittent Failures

- Check internet connection stability
- Monitor network latency: `ping -c 100 api.alpaca.markets`
- Consider using VPN if geoblocked
- Check if ISP/firewall blocks financial APIs

## Prevention

### 1. Setup Monitoring

Add to crontab to check provider health:

```bash
*/5 * * * * curl -s http://localhost:8000/api/v1/system/providers | \
  jq -r '.[] | select(.success_rate < 0.5) | "Provider \(.name) unhealthy"' | \
  mail -s "Trading System Alert" admin@example.com
```

### 2. Use Multiple Providers

Configure at least 2 providers for redundancy:
- Primary: Alpaca (fast, real-time)
- Fallback: yfinance (free, reliable)

### 3. Implement Caching

The system has built-in caching, but you can enhance it:

```python
# backend/app/services/data_service.py
self.cache = TTLCache(maxsize=1000, ttl=60)  # 1-minute cache
```

## Getting Help

If issues persist after troubleshooting:

1. **Collect Information:**
   ```bash
   # Provider status
   curl http://localhost:8000/api/v1/system/providers > provider_status.json

   # Recent logs
   tail -n 500 backend/logs/app.log > recent_logs.txt

   # Configuration (REDACT API KEYS!)
   cat .env | sed 's/=.*/=***REDACTED***/' > sanitized_config.txt
   ```

2. **Test Basic Connectivity:**
   ```bash
   python3 << EOF
import yfinance as yf
import requests

print("yfinance test:", yf.Ticker("AAPL").info.get("currentPrice", "FAIL"))
print("Internet test:", requests.get("https://www.google.com").status_code)
EOF
   ```

3. **Check GitHub Issues**: Search for similar problems
4. **Enable DEBUG mode**: Set `DEBUG=True` in config
5. **Review provider documentation**: Each provider has specific requirements

## Quick Reference

### Restart Everything

```bash
# Kill all processes
pkill -f uvicorn
pkill -f "npm start"

# Clean start
cd backend && python -m uvicorn app.main:app --reload &
cd frontend && npm start &
```

### Reset Circuit Breakers

```bash
# Option 1: Wait 5 minutes
# Option 2: Restart backend
pkill -f uvicorn && cd backend && python -m uvicorn app.main:app --reload
```

### Verify System Health

```bash
# Check all endpoints
curl http://localhost:8000/api/v1/system/health
curl http://localhost:8000/api/v1/data/price/AAPL
curl http://localhost:8000/api/v1/system/providers
```

---

## Summary

The system is designed to be resilient with multiple fallback layers:

1. ✅ **Multiple providers** - if one fails, try next
2. ✅ **Automatic retries** - transient errors handled automatically
3. ✅ **Circuit breakers** - prevent cascading failures
4. ✅ **Data validation** - catch bad data early
5. ✅ **Detailed logging** - debug issues quickly
6. ✅ **Demo fallback** - system always works, even without data providers

Most issues resolve themselves automatically. For persistent problems, use this guide to diagnose and fix the root cause.
