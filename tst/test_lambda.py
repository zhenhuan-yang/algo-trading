import json
from src.lambda_function import lambda_handler

test_event = {
    "body": json.dumps({
        "action": "buy",
        "ticker": "TQQQ",
        "qty": 10,
        "order_type": "market",
        "time_in_force": "gtc"
    })
}

class MockContext:
    function_name = "test_lambda"

if __name__ == "__main__":
    response = lambda_handler(test_event, MockContext())
    print("Lambda Response:", response)
