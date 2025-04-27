import pandas as pd
from datetime import datetime

def predict_crash(input_csv="data/analyzed_posts.csv", output_csv="data/crash_predictions.csv"):
    try:
        # Load analyzed posts
        df = pd.read_csv(input_csv)
        
        # Convert date to datetime and extract week
        df["date"] = pd.to_datetime(df["date"])
        df["week"] = df["date"].dt.isocalendar().week
        df["year"] = df["date"].dt.year
        
        # Group by year and week, calculate average sentiment and issue counts
        grouped = df.groupby(["year", "week"]).agg({
            "sentiment": "mean",
            "issues": lambda x: sum("'mental_health'" in str(i) for i in x),  # Count mental_health issues
            "title": "count"  # Count posts per week
        }).rename(columns={"issues": "mental_health_count", "title": "post_count"}).reset_index()
        
        # Define crash periods (low sentiment and high mental health issues)
        grouped["crash_period"] = (grouped["sentiment"] < -0.2) & (grouped["mental_health_count"] >= 2)
        
        # Drexel's 2024-2025 academic calendar
        calendar = {
            (2024, 41): "Co-op Deadlines (Fall)",
            (2024, 49): "Finals (Fall)",
            (2025, 10): "Co-op Deadlines (Winter)",
            (2025, 24): "Finals (Spring)"
        }
        
        # Map calendar events to weeks
        grouped["event"] = grouped.apply(
            lambda row: calendar.get((row["year"], row["week"]), ""), axis=1
        )
        
        # Generate recommendations
        def get_recommendation(row):
            if row["crash_period"]:
                if "Finals" in row["event"]:
                    return "Host mental health workshop during finals week"
                elif "Co-op" in row["event"]:
                    return "Offer co-op stress management sessions"
                elif row["mental_health_count"] >= 2:
                    return "Conduct mental health awareness campaign"
            return ""
        
        grouped["recommendation"] = grouped.apply(get_recommendation, axis=1)
        
        # Save results
        grouped.to_csv(output_csv, index=False)
        return grouped
    except Exception as e:
        print(f"Error predicting crashes: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = predict_crash()
    print(f"Predicted crash periods for {len(df)} weeks")
    print(df[["year", "week", "sentiment", "mental_health_count", "event", "crash_period", "recommendation"]].head())