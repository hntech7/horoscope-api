from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
from collections import Counter
from ..models import User, UserAnalytics, CreditTransaction, FeatureType, FEATURE_COSTS
from ..schemas import (
    UserAnalyticsResponse,
    AnalyticsSummaryResponse,
    FeatureUsageStats,
    UserActivityRequest
)
from ..auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

async def get_or_create_user_analytics(user_id: str) -> UserAnalytics:
    """Get user analytics or create if doesn't exist"""
    user_analytics = await UserAnalytics.find_one(UserAnalytics.user_id == user_id)
    if not user_analytics:
        user_analytics = UserAnalytics(user_id=user_id)
        await user_analytics.save()
    return user_analytics

@router.post("/track-activity")
async def track_user_activity(
    request: UserActivityRequest,
    current_user: User = Depends(get_current_user)
):
    """Track user activity and session data"""
    try:
        # Get or create user analytics
        user_analytics = await get_or_create_user_analytics(current_user.user_id)
        
        # Update session data
        user_analytics.total_sessions += 1
        user_analytics.total_time_spent += request.session_duration
        user_analytics.last_active = datetime.utcnow()
        
        # Update feature usage
        for feature in request.features_used:
            if feature in user_analytics.feature_usage:
                user_analytics.feature_usage[feature] += 1
            else:
                user_analytics.feature_usage[feature] = 1
        
        # Update favorite features (top 3 most used)
        if user_analytics.feature_usage:
            sorted_features = sorted(
                user_analytics.feature_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )
            user_analytics.favorite_features = [feature[0] for feature in sorted_features[:3]]
        
        user_analytics.updated_at = datetime.utcnow()
        await user_analytics.save()
        
        return {
            "message": "Activity tracked successfully",
            "total_sessions": user_analytics.total_sessions,
            "total_time_spent": user_analytics.total_time_spent
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track activity: {str(e)}"
        )

@router.get("/user", response_model=UserAnalyticsResponse)
async def get_user_analytics(current_user: User = Depends(get_current_user)):
    """Get current user's analytics data"""
    try:
        user_analytics = await get_or_create_user_analytics(current_user.user_id)
        
        return UserAnalyticsResponse(
            id=user_analytics.id,
            user_id=user_analytics.user_id,
            feature_usage=user_analytics.feature_usage,
            total_sessions=user_analytics.total_sessions,
            last_active=user_analytics.last_active,
            total_time_spent=user_analytics.total_time_spent,
            favorite_features=user_analytics.favorite_features,
            created_at=user_analytics.created_at,
            updated_at=user_analytics.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user analytics: {str(e)}"
        )

@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary():
    """Get overall analytics summary (admin endpoint)"""
    try:
        # Get current time boundaries
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)
        
        # Total users
        total_users = await User.count()
        
        # Active users
        active_users_today = await UserAnalytics.find(
            UserAnalytics.last_active >= today_start
        ).count()
        
        active_users_this_week = await UserAnalytics.find(
            UserAnalytics.last_active >= week_start
        ).count()
        
        active_users_this_month = await UserAnalytics.find(
            UserAnalytics.last_active >= month_start
        ).count()
        
        # Get all user analytics to calculate feature usage
        all_analytics = await UserAnalytics.find().to_list()
        
        # Aggregate feature usage
        feature_usage_counter = Counter()
        for analytics in all_analytics:
            for feature, count in analytics.feature_usage.items():
                feature_usage_counter[feature] += count
        
        # Calculate most popular features with credit costs
        most_popular_features = []
        for feature, usage_count in feature_usage_counter.most_common(5):
            try:
                feature_enum = FeatureType(feature)
                credit_cost = FEATURE_COSTS[feature_enum]
                total_credits_spent = usage_count * credit_cost
            except (ValueError, KeyError):
                credit_cost = 0
                total_credits_spent = 0
            
            most_popular_features.append(FeatureUsageStats(
                feature_name=feature,
                usage_count=usage_count,
                total_credits_spent=total_credits_spent
            ))
        
        # Total credits consumed
        debit_transactions = await CreditTransaction.find(
            CreditTransaction.transaction_type == "debit"
        ).to_list()
        
        total_credits_consumed = sum(transaction.amount for transaction in debit_transactions)
        
        # Average session duration
        total_time = sum(analytics.total_time_spent for analytics in all_analytics)
        total_sessions = sum(analytics.total_sessions for analytics in all_analytics)
        average_session_duration = total_time / total_sessions if total_sessions > 0 else 0
        
        return AnalyticsSummaryResponse(
            total_users=total_users,
            active_users_today=active_users_today,
            active_users_this_week=active_users_this_week,
            active_users_this_month=active_users_this_month,
            most_popular_features=most_popular_features,
            total_credits_consumed=total_credits_consumed,
            average_session_duration=round(average_session_duration, 2)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics summary: {str(e)}"
        )

@router.get("/feature-usage")
async def get_feature_usage_stats(current_user: User = Depends(get_current_user)):
    """Get detailed feature usage statistics for current user"""
    try:
        user_analytics = await get_or_create_user_analytics(current_user.user_id)
        
        # Calculate credits spent per feature
        feature_stats = []
        for feature, usage_count in user_analytics.feature_usage.items():
            try:
                feature_enum = FeatureType(feature)
                credit_cost = FEATURE_COSTS[feature_enum]
                total_credits_spent = usage_count * credit_cost
            except (ValueError, KeyError):
                credit_cost = 0
                total_credits_spent = 0
            
            feature_stats.append({
                "feature_name": feature,
                "usage_count": usage_count,
                "credit_cost_per_use": credit_cost,
                "total_credits_spent": total_credits_spent
            })
        
        # Sort by usage count
        feature_stats.sort(key=lambda x: x["usage_count"], reverse=True)
        
        return {
            "feature_usage_stats": feature_stats,
            "total_features_used": len(feature_stats),
            "most_used_feature": feature_stats[0]["feature_name"] if feature_stats else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feature usage stats: {str(e)}"
        )

@router.get("/user-engagement")
async def get_user_engagement_metrics(current_user: User = Depends(get_current_user)):
    """Get user engagement metrics"""
    try:
        user_analytics = await get_or_create_user_analytics(current_user.user_id)
        
        # Calculate engagement metrics
        days_since_signup = (datetime.utcnow() - user_analytics.created_at).days
        if days_since_signup == 0:
            days_since_signup = 1  # Avoid division by zero
        
        average_sessions_per_day = user_analytics.total_sessions / days_since_signup
        average_time_per_session = (
            user_analytics.total_time_spent / user_analytics.total_sessions 
            if user_analytics.total_sessions > 0 else 0
        )
        
        # Days since last active
        days_since_last_active = (datetime.utcnow() - user_analytics.last_active).days
        
        return {
            "total_sessions": user_analytics.total_sessions,
            "total_time_spent_minutes": user_analytics.total_time_spent,
            "average_sessions_per_day": round(average_sessions_per_day, 2),
            "average_time_per_session_minutes": round(average_time_per_session, 2),
            "days_since_signup": days_since_signup,
            "days_since_last_active": days_since_last_active,
            "favorite_features": user_analytics.favorite_features,
            "engagement_level": (
                "High" if average_sessions_per_day > 2 else
                "Medium" if average_sessions_per_day > 0.5 else
                "Low"
            )
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve engagement metrics: {str(e)}"
        )
