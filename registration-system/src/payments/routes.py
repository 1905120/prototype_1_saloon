from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from src.payments.api import PaymentManager


# Request models
class CreatePaymentRequest(BaseModel):
    business_name: str
    customer_id: str
    merchant_upi: str
    merchant_name: str
    amount: float
    description: Optional[str] = "Payment for services"
    metadata: Optional[Dict[str, Any]] = None


class VerifyPaymentRequest(BaseModel):
    business_name: str
    transaction_id: str
    payment_status: str
    reference_id: Optional[str] = None


class PaymentResponse(BaseModel):
    status: str
    result: Dict[str, Any]


# Create router
router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


def get_payment_manager(business_name: str) -> PaymentManager:
    """Get or create payment manager for business"""
    return PaymentManager(business_name=business_name)


@router.post("/create-upi-payment", response_model=PaymentResponse)
async def create_upi_payment(payload: CreatePaymentRequest):
    """
    Create a UPI payment request
    
    Args:
        payload: Payment request details
        
    Returns:
        Payment request with UPI link
    """
    try:
        payment_manager = get_payment_manager(payload.business_name)
        
        payment_request = payment_manager.create_payment_request(
            customer_id=payload.customer_id,
            merchant_upi=payload.merchant_upi,
            merchant_name=payload.merchant_name,
            amount=payload.amount,
            description=payload.description,
            metadata=payload.metadata
        )
        
        return PaymentResponse(
            status="SUCCESS",
            result=payment_request
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-payment", response_model=PaymentResponse)
async def verify_payment(payload: VerifyPaymentRequest):
    """
    Verify payment status after UPI transaction
    
    Args:
        payload: Payment verification details
        
    Returns:
        Updated payment details
    """
    try:
        payment_manager = get_payment_manager(payload.business_name)
        
        payment = payment_manager.verify_payment(
            transaction_id=payload.transaction_id,
            payment_status=payload.payment_status,
            reference_id=payload.reference_id
        )
        
        if 'error' in payment:
            raise HTTPException(status_code=404, detail=payment['error'])
        
        return PaymentResponse(
            status="SUCCESS",
            result=payment
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{business_name}/{transaction_id}", response_model=PaymentResponse)
async def get_payment_status(business_name: str, transaction_id: str):
    """Get payment status by transaction ID"""
    try:
        payment_manager = get_payment_manager(business_name)
        payment = payment_manager.get_payment_status(transaction_id)
        
        if 'error' in payment:
            raise HTTPException(status_code=404, detail=payment['error'])
        
        return PaymentResponse(
            status="SUCCESS",
            result=payment
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer/{business_name}/{customer_id}", response_model=PaymentResponse)
async def get_customer_payments(business_name: str, customer_id: str):
    """Get all payments for a customer"""
    try:
        payment_manager = get_payment_manager(business_name)
        payments = payment_manager.get_customer_payments(customer_id)
        
        return PaymentResponse(
            status="SUCCESS",
            result={
                "business_name": business_name,
                "customer_id": customer_id,
                "payments": payments,
                "total_count": len(payments)
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-with-gateway", response_model=PaymentResponse)
async def verify_with_gateway(payload: VerifyPaymentRequest):
    """
    Verify payment status with payment gateway in real-time
    
    Args:
        payload: Payment verification details
        
    Returns:
        Payment verification result from gateway
    """
    try:
        payment_manager = get_payment_manager(payload.business_name)
        
        result = payment_manager.verify_payment_with_gateway(
            transaction_id=payload.transaction_id,
            amount=None
        )
        
        if result.get("status") == "ERROR":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return PaymentResponse(
            status="SUCCESS",
            result=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
