"""Payment configuration"""

# UPI Configuration
UPI_CONFIG = {
    "enabled": True,
    "default_merchant_upi": "salon@upi",  # Update with actual UPI ID
    "timeout": 300,  # 5 minutes
    "retry_attempts": 3
}

# Payment Status Constants
PAYMENT_STATUS = {
    "PENDING": "PENDING",
    "SUCCESS": "SUCCESS",
    "FAILED": "FAILED",
    "CANCELLED": "CANCELLED",
    "EXPIRED": "EXPIRED"
}

# Payment Methods
PAYMENT_METHODS = {
    "UPI": "upi",
    "CARD": "card",
    "WALLET": "wallet",
    "NETBANKING": "netbanking"
}

# Default payment method
DEFAULT_PAYMENT_METHOD = "UPI"

# Payment Gateway Configurations
# Choose one and update with your credentials

# Razorpay Configuration
RAZORPAY_CONFIG = {
    "enabled": False,  # Set to True to enable
    "name": "razorpay",
    "credentials": {
        "key_id": "YOUR_RAZORPAY_KEY_ID",
        "key_secret": "YOUR_RAZORPAY_KEY_SECRET"
    }
}

# Stripe Configuration
STRIPE_CONFIG = {
    "enabled": False,  # Set to True to enable
    "name": "stripe",
    "credentials": {
        "api_key": "YOUR_STRIPE_API_KEY"
    }
}

# Paytm Configuration
PAYTM_CONFIG = {
    "enabled": False,  # Set to True to enable
    "name": "paytm",
    "credentials": {
        "merchant_id": "YOUR_PAYTM_MERCHANT_ID",
        "merchant_key": "YOUR_PAYTM_MERCHANT_KEY"
    }
}

# PhonePe Configuration
PHONEPE_CONFIG = {
    "enabled": False,  # Set to True to enable
    "name": "phonepe",
    "credentials": {
        "merchant_id": "YOUR_PHONEPE_MERCHANT_ID",
        "api_key": "YOUR_PHONEPE_API_KEY"
    }
}

# Select active gateway
ACTIVE_GATEWAY = RAZORPAY_CONFIG  # Change to your preferred gateway
