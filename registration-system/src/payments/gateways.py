"""Payment gateway integrations for real-time payment verification"""

import requests
import hmac
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from datetime import datetime


class PaymentGateway(ABC):
    """Abstract base class for payment gateways"""
    
    @abstractmethod
    def verify_payment(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        """Verify payment status from gateway"""
        pass
    
    @abstractmethod
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get payment status"""
        pass


class RazorpayGateway(PaymentGateway):
    """Razorpay payment gateway integration"""
    
    def __init__(self, key_id: str, key_secret: str):
        self.key_id = key_id
        self.key_secret = key_secret
        self.base_url = "https://api.razorpay.com/v1"
    
    def verify_payment(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        """
        Verify payment with Razorpay
        
        Args:
            transaction_id: Razorpay payment ID
            amount: Amount in paise (multiply by 100)
            
        Returns:
            Payment verification result
        """
        try:
            url = f"{self.base_url}/payments/{transaction_id}"
            
            response = requests.get(
                url,
                auth=(self.key_id, self.key_secret),
                timeout=10
            )
            
            if response.status_code == 200:
                payment_data = response.json()
                
                return {
                    "status": "SUCCESS" if payment_data.get("status") == "captured" else "PENDING",
                    "transaction_id": transaction_id,
                    "amount": payment_data.get("amount") / 100,  # Convert from paise
                    "currency": payment_data.get("currency"),
                    "method": payment_data.get("method"),
                    "description": payment_data.get("description"),
                    "created_at": datetime.fromtimestamp(payment_data.get("created_at")).isoformat(),
                    "gateway_response": payment_data
                }
            else:
                return {
                    "status": "FAILED",
                    "error": f"Gateway error: {response.status_code}",
                    "transaction_id": transaction_id
                }
        
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "transaction_id": transaction_id
            }
    
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get payment status from Razorpay"""
        return self.verify_payment(transaction_id, 0)
    
    def verify_webhook_signature(self, webhook_body: str, webhook_signature: str) -> bool:
        """Verify Razorpay webhook signature"""
        try:
            expected_signature = hmac.new(
                self.key_secret.encode(),
                webhook_body.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, webhook_signature)
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False


class StripeGateway(PaymentGateway):
    """Stripe payment gateway integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.stripe.com/v1"
    
    def verify_payment(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        """
        Verify payment with Stripe
        
        Args:
            transaction_id: Stripe payment intent ID
            amount: Amount in dollars
            
        Returns:
            Payment verification result
        """
        try:
            url = f"{self.base_url}/payment_intents/{transaction_id}"
            
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            
            if response.status_code == 200:
                payment_data = response.json()
                
                return {
                    "status": "SUCCESS" if payment_data.get("status") == "succeeded" else "PENDING",
                    "transaction_id": transaction_id,
                    "amount": payment_data.get("amount") / 100,  # Convert from cents
                    "currency": payment_data.get("currency"),
                    "payment_method": payment_data.get("payment_method"),
                    "created_at": datetime.fromtimestamp(payment_data.get("created")).isoformat(),
                    "gateway_response": payment_data
                }
            else:
                return {
                    "status": "FAILED",
                    "error": f"Gateway error: {response.status_code}",
                    "transaction_id": transaction_id
                }
        
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "transaction_id": transaction_id
            }
    
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get payment status from Stripe"""
        return self.verify_payment(transaction_id, 0)


class PaytmGateway(PaymentGateway):
    """Paytm payment gateway integration"""
    
    def __init__(self, merchant_id: str, merchant_key: str):
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key
        self.base_url = "https://securegw.paytm.in/merchant-status/getTxnStatus"
    
    def verify_payment(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        """
        Verify payment with Paytm
        
        Args:
            transaction_id: Paytm order ID
            amount: Amount in rupees
            
        Returns:
            Payment verification result
        """
        try:
            # Create checksum
            checksum_data = {
                "MID": self.merchant_id,
                "ORDERID": transaction_id,
                "key": self.merchant_key
            }
            
            checksum_string = f"{self.merchant_id}|{transaction_id}|{self.merchant_key}"
            checksum = hashlib.md5(checksum_string.encode()).hexdigest()
            
            payload = {
                "MID": self.merchant_id,
                "ORDERID": transaction_id,
                "CHECKSUMHASH": checksum
            }
            
            response = requests.post(
                self.base_url,
                data=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                return {
                    "status": "SUCCESS" if response_data.get("STATUS") == "TXN_SUCCESS" else "PENDING",
                    "transaction_id": transaction_id,
                    "amount": amount,
                    "gateway_response": response_data
                }
            else:
                return {
                    "status": "FAILED",
                    "error": f"Gateway error: {response.status_code}",
                    "transaction_id": transaction_id
                }
        
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "transaction_id": transaction_id
            }
    
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get payment status from Paytm"""
        return self.verify_payment(transaction_id, 0)


class PhonePeGateway(PaymentGateway):
    """PhonePe payment gateway integration"""
    
    def __init__(self, merchant_id: str, api_key: str):
        self.merchant_id = merchant_id
        self.api_key = api_key
        self.base_url = "https://api.phonepe.com/apis/hermes/status"
    
    def verify_payment(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        """
        Verify payment with PhonePe
        
        Args:
            transaction_id: PhonePe transaction ID
            amount: Amount in rupees
            
        Returns:
            Payment verification result
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "merchantId": self.merchant_id,
                "transactionId": transaction_id
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                return {
                    "status": "SUCCESS" if response_data.get("success") else "PENDING",
                    "transaction_id": transaction_id,
                    "amount": amount,
                    "gateway_response": response_data
                }
            else:
                return {
                    "status": "FAILED",
                    "error": f"Gateway error: {response.status_code}",
                    "transaction_id": transaction_id
                }
        
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "transaction_id": transaction_id
            }
    
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get payment status from PhonePe"""
        return self.verify_payment(transaction_id, 0)


class GatewayFactory:
    """Factory for creating payment gateway instances"""
    
    _gateways = {
        "razorpay": RazorpayGateway,
        "stripe": StripeGateway,
        "paytm": PaytmGateway,
        "phonepe": PhonePeGateway
    }
    
    @classmethod
    def create_gateway(cls, gateway_name: str, **kwargs) -> Optional[PaymentGateway]:
        """
        Create a payment gateway instance
        
        Args:
            gateway_name: Name of the gateway (razorpay, stripe, paytm, phonepe)
            **kwargs: Gateway-specific credentials
            
        Returns:
            Payment gateway instance or None
        """
        gateway_class = cls._gateways.get(gateway_name.lower())
        
        if not gateway_class:
            raise ValueError(f"Unknown gateway: {gateway_name}")
        
        return gateway_class(**kwargs)
    
    @classmethod
    def register_gateway(cls, name: str, gateway_class: type):
        """Register a new payment gateway"""
        cls._gateways[name.lower()] = gateway_class
