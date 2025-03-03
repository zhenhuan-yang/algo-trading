import json
import os
from alpaca_trade_api.rest import REST

# Load Alpaca API keys from environment variables
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets/v2"

# Initialize Alpaca API client
api = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)

def lambda_handler(event, context):
    """
    Handles TradingView Webhook Alerts and places trades on Alpaca.
    """
    try:
        body = json.loads(event["body"])  # Parse webhook payload
        print(f"Received Webhook: {body}")

        action = body.get("action")
        symbol = body.get("ticker", "TQQQ")  # Default to TQQQ if no symbol provided
        qty = int(body.get("qty", 10))  # Default 10 shares
        order_type = body.get("order_type", "market")
        time_in_force = body.get("time_in_force", "gtc")

        if action == "buy":
            api.submit_order(
                symbol=symbol,
                qty=qty,
                side="buy",
                type=order_type,
                time_in_force=time_in_force
            )
            return {"statusCode": 200, "body": json.dumps({"message": f"BUY order placed for {qty} {symbol}"})}

        elif action == "sell":
            api.submit_order(
                symbol=symbol,
                qty=qty,
                side="sell",
                type=order_type,
                time_in_force=time_in_force
            )
            return {"statusCode": 200, "body": json.dumps({"message": f"SELL order placed for {qty} {symbol}"})}

        else:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid action"})}

    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
