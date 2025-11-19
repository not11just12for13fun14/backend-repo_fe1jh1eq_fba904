"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

# Example schemas (kept for reference):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Configurator-specific schemas (collections used by the app)

class Customer(BaseModel):
    """
    Customer data for an offer request
    Collection name: "customer"
    """
    first_name: str
    last_name: str
    company: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    notes: Optional[str] = None

class Configuration(BaseModel):
    """
    Vehicle configuration submitted by the user
    Collection name: "configuration"
    """
    vehicle_id: str = Field(..., description="Selected vehicle ID")
    vehicle_name: str = Field(..., description="Selected vehicle name for convenience")
    color_code: str = Field(..., description="Color code")
    color_name: str = Field(..., description="Color name")
    upholstery_code: str = Field(..., description="Upholstery code")
    upholstery_name: str = Field(..., description="Upholstery name")
    factory_options: List[str] = Field(default_factory=list, description="List of selected factory option codes")
    accessories: List[str] = Field(default_factory=list, description="List of selected accessory codes")
    special_agreement: Optional[str] = Field(None, description="Special agreement notes")
    customer: Customer
    total_price: Optional[float] = Field(None, ge=0)
