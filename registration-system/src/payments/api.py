import uuid
import json
import os
from datetime import datetime
from typing import Dict, Optional
import hashlib
from src.payments.gateways import GatewayFactory, PaymentGateway


class PaymentManager:
    """Manages payment operations including UPI payments"""
    
    def __init__(self, business_name: str = None, gateway_config: Optional[Dict] = None):
        self.payments = {}
        self.transactions = {}
        self.business_name = business_name or "default"
        self.transaction_dir = f"data/businesses/{self.business_name}/transactions"
        self.gateway = None
        self.gateway_config = gateway_config or {}
        self._ensure_transaction_dir()
        self._initialize_gateway()
    
    def _ensure_transaction_dir(self):
        """Ensure transaction directory exists"""
        os.makedirs(self.transaction_dir, exist_ok=True)
    
    def _initialize_gateway(self):
        """Initialize payment gateway if configured"""
        try:
            if self.gateway_config.get("enabled"):
                gateway_name = self.gateway_config.get("name")
                gateway_credentials = self.gateway_config.get("credentials", {})
                
                if gateway_name and gateway_credentials:
                    self.gateway = GatewayFactory.create_gateway(
                        gateway_name,
                        **gateway_credentials
                    )
        except Exception as e:
            print(f"Error initializing payment gateway: {e}")
            self.gateway = None
    
    def _save_transaction(self, transaction_id: str, transaction_data: Dict):
        """Save transaction to file"""
        try:
            file_path = os.path.join(self.transaction_dir, f"{transaction_id}.json")
            with open(file_path, 'w') as f:
                json.dump(transaction_data, f, indent=2)
        except Exception as e:
            print(f"Error saving transaction: {e}")
    
    def _load_transaction(self, transaction_id: str) -> Optional[Dict]:
        """Load transaction from file"""
        try:
            file_path = os.path.join(self.transaction_dir, f"{transaction_id}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading transaction: {e}")
        return None
    
    def generate_upi_link(
        self,
        merchant_upi: str,
        merchant_name: str,
        amount: float,
        transaction_id: Optional[str] = None,
        description: str = "Payment for services"
    ) -> str:
        """
        Generate UPI deep link for payment
        
        Args:
            merchant_upi: Merchant's UPI ID (e.g., salon@upi)
            merchant_name: Merchant/Salon name
            amount: Payment amount in rupees
            transaction_id: Unique transaction ID (auto-generated if not provided)
            description: Payment description
            
        Returns:
            UPI deep link string
        """
        if not transaction_id:
            transaction_id = self.generate_transaction_id()
        
        # Encode special characters
        merchant_name = merchant_name.replace(" ", "%20")
        description = description.replace(" ", "%20")
        
        upi_link = (
            f"upi://pay?"
            f"pa={merchant_upi}&"
            f"pn={merchant_name}&"
            f"am={amount}&"
            f"tn={description}&"
            f"tr={transaction_id}"
        )
        
        return upi_link
    
    def generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        return f"TXN{uuid.uuid4().hex[:12].upper()}"
    
    def create_payment_request(
        self,
        customer_id: str,
        merchant_upi: str,
        merchant_name: str,
        amount: float,
        description: str = "Payment for services",
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a payment request
        
        Args:
            customer_id: Customer identifier
            merchant_upi: Merchant's UPI ID
            merchant_name: Merchant/Salon name
            amount: Payment amount
            description: Payment description
            metadata: Additional metadata
            
        Returns:
            Payment request details with UPI link
        """
        transaction_id = self.generate_transaction_id()
        upi_link = self.generate_upi_link(
            merchant_upi,
            merchant_name,
            amount,
            transaction_id,
            description
        )
        
        payment_request = {
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "merchant_upi": merchant_upi,
            "merchant_name": merchant_name,
            "amount": amount,
            "description": description,
            "upi_link": upi_link,
            "status": "PENDING",
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.payments[transaction_id] = payment_request
        self._save_transaction(transaction_id, payment_request)
        return payment_request
    
    def verify_payment(
        self,
        transaction_id: str,
        payment_status: str,
        reference_id: Optional[str] = None
    ) -> Dict:
        """
        Verify and update payment status
        
        Args:
            transaction_id: Transaction ID to verify
            payment_status: Status from UPI app (SUCCESS, FAILED, PENDING)
            reference_id: Bank reference ID
            
        Returns:
            Updated payment details
        """
        # Try to load from file first
        payment = self._load_transaction(transaction_id)
        
        if not payment and transaction_id not in self.payments:
            return {"error": "Transaction not found"}
        
        if not payment:
            payment = self.payments[transaction_id]
        
        payment["status"] = payment_status
        payment["reference_id"] = reference_id
        payment["verified_at"] = datetime.now().isoformat()
        
        self.transactions[transaction_id] = payment
        self._save_transaction(transaction_id, payment)
        return payment
    
    def verify_payment_with_gateway(self, transaction_id: str, amount: float = None) -> Dict:
        """
        Verify payment status with payment gateway in real-time
        
        Args:
            transaction_id: Transaction ID to verify
            amount: Amount for verification (optional)
            
        Returns:
            Payment verification result from gateway
        """
        if not self.gateway:
            return {
                "status": "ERROR",
                "error": "Payment gateway not configured",
                "transaction_id": transaction_id
            }
        
        try:
            # Get gateway verification
            gateway_result = self.gateway.get_payment_status(transaction_id)
            
            # Load existing payment
            payment = self._load_transaction(transaction_id)
            if not payment:
                payment = self.payments.get(transaction_id, {})
            
            # Update with gateway result
            if payment:
                payment["gateway_status"] = gateway_result.get("status")
                payment["gateway_response"] = gateway_result
                payment["verified_at"] = datetime.now().isoformat()
                
                # Update local status if gateway confirms success
                if gateway_result.get("status") == "SUCCESS":
                    payment["status"] = "SUCCESS"
                
                self._save_transaction(transaction_id, payment)
            
            return {
                "status": "SUCCESS",
                "transaction_id": transaction_id,
                "payment": payment,
                "gateway_verification": gateway_result
            }
        
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "transaction_id": transaction_id
            }
    
    def get_payment_status(self, transaction_id: str) -> Dict:
        """Get payment status"""
        # Try to load from file first
        payment = self._load_transaction(transaction_id)
        
        if payment:
            return payment
        
        if transaction_id not in self.payments:
            return {"error": "Transaction not found"}
        
        return self.payments[transaction_id]
    
    def get_customer_payments(self, customer_id: str) -> list:
        """Get all payments for a customer"""
        customer_payments = []
        
        # Load from files
        if os.path.exists(self.transaction_dir):
            for filename in os.listdir(self.transaction_dir):
                if filename.endswith('.json'):
                    transaction = self._load_transaction(filename.replace('.json', ''))
                    if transaction and transaction.get("customer_id") == customer_id:
                        customer_payments.append(transaction)
        
        # Also check in-memory payments
        for payment in self.payments.values():
            if payment["customer_id"] == customer_id and payment not in customer_payments:
                customer_payments.append(payment)
        
        return customer_payments


# Global payment manager instance
payment_manager = PaymentManager()
