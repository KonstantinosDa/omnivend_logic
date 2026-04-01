from celery import shared_task
from datetime import datetime
from .models import VendingMachine,MachineStock,Sales,Store,Item_Sales
from django.utils.timezone import now
from django.core.management.base import BaseCommand
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import requests
from datetime import date, timedelta
from django.db.models import Sum

today = now().date()

def encode_weather(weather):
    weather_map = {
        "sunny": 1,
        "cloudy": 0,
        "partly_cloudy": 0.5,
        "windy": -0.5,
        "rainy": -1,
        "stormy": -2,
        "snowy": -3,
    }
    return weather_map.get(weather, 0)

def get_tomorrow_weather(latitude,longitude):
    
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}.8&daily=temperature_2m_max&timezone=auto"
        data = requests.get(url).json()
        return data["daily"]["temperature_2m_max"][0]
    except Exception:
        return 20  # fallback

@shared_task
def expected_demand():
    items = MachineStock.objects.select_related("product")

    for item in items:
        sales = Item_Sales.objects.filter(
            machine_item=item,
            interval_type="day"
        ).order_by("created_at")

        if sales.count() < 5:
            print(f"Skipping {item.product.name} (not enough data)")
            continue

        X = []
        y = []

        sales_list = list(sales)

        for i in range(3, len(sales_list)):
            s = sales_list[i]

            #  Lag features 
            prev_1 = float(sales_list[i - 1].amount)
            prev_2 = float(sales_list[i - 2].amount)
            prev_3 = float(sales_list[i - 3].amount)

            avg_3 = np.mean([prev_1, prev_2, prev_3])

            #  Time features 
            weekday = s.created_at.weekday()
            is_weekend = 1 if weekday >= 5 else 0
            week_of_year = s.created_at.isocalendar()[1]

            #  Weather 
            temp = float(s.temperature_weather or 20)
            weather_encoded = encode_weather(s.weather_type)

            # Product info 
            price = float(item.product.price) if hasattr(item.product, "price") else 0

            # Feature vector
            X.append([
                s.created_at.month,
                weekday,
                is_weekend,
                week_of_year,
                temp,
                weather_encoded,
                prev_1,
                prev_2,
                prev_3,
                avg_3,
                price,
            ])

            y.append(float(s.amount))

        X = np.array(X)
        y = np.array(y)

        # Train model
        model = RandomForestRegressor(n_estimators=150, random_state=42)
        model.fit(X, y)

        # 🔮 Predict tomorrow
        tomorrow = date.today() + timedelta(days=1)
        temp = get_tomorrow_weather()

        weekday = tomorrow.weekday()
        is_weekend = 1 if weekday >= 5 else 0
        week_of_year = tomorrow.isocalendar()[1]

        # --- Latest lag values ---
        last_sales = sales_list[-3:]
        prev_1 = float(last_sales[-1].amount)
        prev_2 = float(last_sales[-2].amount)
        prev_3 = float(last_sales[-3].amount)
        avg_3 = np.mean([prev_1, prev_2, prev_3])

        weather_encoded = 0  # unknown for tomorrow

        price = float(item.product.price) if hasattr(item.product, "price") else 0

        features = [[
            tomorrow.month,
            weekday,
            is_weekend,
            week_of_year,
            temp,
            weather_encoded,
            prev_1,
            prev_2,
            prev_3,
            avg_3,
            price,
        ]]

        prediction = model.predict(features)[0]

        item.expected_demand = max(1, int(prediction))
        item.save()

        print(
            f"{item.product.name} → Predicted demand: {item.expected_demand}"
        )
        
    print("Prediction complete!")

@shared_task
def run_daily_aggregations():
    today = now().date()
    weekday = today.weekday()  # Monday=0, Sunday=6

    if weekday == 6:  
        start_of_week = today - timedelta(days=weekday)
        end_of_week = start_of_week + timedelta(days=6)

        weekly_data = (
            Sales.objects
            .filter(interval_type="day",
                    created_at__range=(start_of_week, end_of_week),
                    machine__isnull=False)
            .values("machine")
            .annotate(total=Sum("amount"))
        )

        for row in weekly_data:
            Sales.objects.update_or_create(
                machine_id=row["machine"],
                interval_type="week",
                created_at=start_of_week,
                defaults={
                    "source_type": "machine",
                    "amount": row["total"],
                    "ended_at": end_of_week
                }
            )

    start_of_month = today.replace(day=1)
    if today == (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1):
        # today is last day of month
        if today.month == 12:
            next_month = date(today.year + 1, 1, 1)
        else:
            next_month = date(today.year, today.month + 1, 1)
        end_of_month = next_month - timedelta(days=1)

        monthly_data = (
            Sales.objects
            .filter(interval_type="week",
                    created_at__range=(start_of_month, end_of_month),
                    machine__isnull=False)
            .values("machine")
            .annotate(total=Sum("amount"))
        )

        for row in monthly_data:
            Sales.objects.update_or_create(
                machine_id=row["machine"],
                interval_type="month",
                created_at=start_of_month,
                defaults={
                    "source_type": "machine",
                    "amount": row["total"],
                    "ended_at": end_of_month
                }
            )

    if today.month == 12 and today.day == 31:
        start_of_year = date(today.year, 1, 1)
        end_of_year = date(today.year, 12, 31)

        yearly_data = (
            Sales.objects
            .filter(interval_type="month",
                    created_at__range=(start_of_year, end_of_year),
                    machine__isnull=False)
            .values("machine")
            .annotate(total=Sum("amount"))
        )

        for row in yearly_data:
            Sales.objects.update_or_create(
                machine_id=row["machine"],
                interval_type="year",
                created_at=start_of_year,
                defaults={
                    "source_type": "machine",
                    "amount": row["total"],
                    "ended_at": end_of_year
                }
            )
    start_of_year = date(today.year, 1, 1)
    end_of_year = date(today.year, 12, 31)
    yearly_data = (
        Sales.objects
        .filter(
            interval_type="month",
            created_at__range=(start_of_year, end_of_year),
            machine__isnull=False
        )
        .values("machine")
        .annotate(total=Sum("amount"))
    )
    for row in yearly_data:
        Sales.objects.update_or_create(
            machine_id=row["machine"],
            interval_type="year",
            created_at=start_of_year,
            defaults={
                "source_type": "machine",
                "amount": row["total"],
                "ended_at": end_of_year
            }
        )

#run this in the bash to start the beat whorker
# # Start worker
# celery -A omnivend_logic worker -l info

# # Start beat scheduler
# celery -A omnivend_logic beat -l info