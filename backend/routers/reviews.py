"""
routers/reviews.py — Customer reviews, ratings, loyalty points.
"""
from fastapi import APIRouter, HTTPException, Depends
from database import supabase
from auth import verify_admin
from models import ReviewCreate
from ml.sentiment import analyse_sentiment

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("", summary="Get published reviews")
def get_reviews(limit: int = 20, offset: int = 0):
    result = supabase.table("reviews")\
        .select("*, orders(customer_name, tables(table_number))")\
        .eq("is_published", True)\
        .order("created_at", desc=True)\
        .limit(limit).offset(offset).execute()
    return result.data


@router.post("", status_code=201, summary="Submit review with auto-sentiment")
def submit_review(review: ReviewCreate):
    # Verify order exists
    order = supabase.table("orders").select("id,status").eq("id", review.order_id).execute()
    if not order.data:
        raise HTTPException(status_code=404, detail="Order not found")

    label, score = analyse_sentiment(review.comment)
    payload = {
        "order_id":        review.order_id,
        "customer_name":   review.customer_name,
        "rating":          review.rating,
        "comment":         review.comment,
        "sentiment":       label,
        "sentiment_score": score,
        "is_published":    True,
    }
    result = supabase.table("reviews").insert(payload).execute()
    return result.data[0]


@router.get("/admin", summary="Admin: all reviews including unpublished")
def admin_reviews(_: str = Depends(verify_admin)):
    return supabase.table("reviews")\
        .select("*, orders(customer_name, total_amount, tables(table_number))")\
        .order("created_at", desc=True).execute().data


@router.patch("/{review_id}/toggle", summary="Admin: toggle review visibility")
def toggle_review(review_id: str, _: str = Depends(verify_admin)):
    cur = supabase.table("reviews").select("is_published").eq("id", review_id).single().execute()
    if not cur.data:
        raise HTTPException(status_code=404, detail="Review not found")
    new_val = not cur.data["is_published"]
    supabase.table("reviews").update({"is_published": new_val}).eq("id", review_id).execute()
    return {"id": review_id, "is_published": new_val}


@router.delete("/{review_id}", summary="Admin: delete review")
def delete_review(review_id: str, _: str = Depends(verify_admin)):
    supabase.table("reviews").delete().eq("id", review_id).execute()
    return {"message": "Review deleted"}