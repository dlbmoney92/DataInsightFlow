import streamlit as st
import datetime

# Define subscription tiers with features and limits
SUBSCRIPTION_TIERS = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "price_yearly": 0,
        "features": [
            "Basic data analysis",
            "Up to 3 datasets",
            "Limited transformations",
            "Basic visualizations",
            "No AI-powered insights"
        ],
        "limits": {
            "max_datasets": 3,
            "max_rows_per_dataset": 5000,
            "max_transformations_per_dataset": 10,
            "ai_features_enabled": False,
            "export_formats": ["CSV"],
            "support_level": "Community"
        }
    },
    "basic": {
        "name": "Basic",
        "price_monthly": 9.99,
        "price_yearly": 99.99,
        "features": [
            "Advanced data analysis",
            "Up to 10 datasets",
            "Full transformation suite",
            "Interactive visualizations",
            "Basic AI-powered insights"
        ],
        "limits": {
            "max_datasets": 10,
            "max_rows_per_dataset": 50000,
            "max_transformations_per_dataset": 50,
            "ai_features_enabled": True,
            "export_formats": ["CSV", "Excel", "JSON"],
            "support_level": "Email"
        }
    },
    "pro": {
        "name": "Professional",
        "price_monthly": 24.99,
        "price_yearly": 249.99,
        "features": [
            "Full data analysis suite",
            "Unlimited datasets",
            "Advanced AI-powered insights",
            "Custom visualization options",
            "AI learning system",
            "Priority support"
        ],
        "limits": {
            "max_datasets": float("inf"),
            "max_rows_per_dataset": 1000000,
            "max_transformations_per_dataset": float("inf"),
            "ai_features_enabled": True,
            "export_formats": ["CSV", "Excel", "JSON", "PDF", "HTML"],
            "ai_learning": True,
            "support_level": "Priority"
        }
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": "Contact us",
        "price_yearly": "Contact us",
        "features": [
            "Everything in Professional",
            "Advanced AI learning system",
            "On-premises deployment option",
            "Custom integrations",
            "Advanced security features",
            "Dedicated account manager"
        ],
        "limits": {
            "max_datasets": float("inf"),
            "max_rows_per_dataset": float("inf"),
            "max_transformations_per_dataset": float("inf"),
            "ai_features_enabled": True,
            "export_formats": ["CSV", "Excel", "JSON", "PDF", "HTML", "Custom"],
            "ai_learning": True,
            "advanced_learning": True,
            "support_level": "Dedicated"
        }
    }
}

def get_subscription_info(tier):
    """Get subscription information for a specific tier."""
    if tier in SUBSCRIPTION_TIERS:
        return SUBSCRIPTION_TIERS[tier]
    return SUBSCRIPTION_TIERS["free"]  # Default to free tier

def is_trial_active(trial_end_date):
    """Check if trial is still active."""
    if not trial_end_date:
        return False
    
    now = datetime.datetime.utcnow()
    return trial_end_date > now

def get_trial_days_remaining(trial_end_date):
    """Get number of days remaining in trial."""
    if not trial_end_date:
        return 0
    
    now = datetime.datetime.utcnow()
    if trial_end_date <= now:
        return 0
    
    days_left = (trial_end_date - now).days
    return max(0, days_left)

def get_subscription_expires_in_days(subscription_end_date):
    """Get number of days until subscription expires."""
    if not subscription_end_date:
        return 0
    
    now = datetime.datetime.utcnow()
    if subscription_end_date <= now:
        return 0
    
    days_left = (subscription_end_date - now).days
    return max(0, days_left)

def format_price(price):
    """Format price for display."""
    if isinstance(price, (int, float)):
        return f"${price:.2f}"
    return price