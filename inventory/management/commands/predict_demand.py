from django.core.management.base import BaseCommand
from inventory.models import MachineStock, Item_Sales
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import requests
from datetime import date, timedelta


class Command(BaseCommand):
    help = "Train ML model and predict vending machine demand"

    def get_temperature(self):
        """
        Get tomorrow forecast temperature from Open-Meteo
        """
        try:
            url = "https://api.open-meteo.com/v1/forecast?latitude=38&longitude=23.8&daily=temperature_2m_max&timezone=auto"
            data = requests.get(url).json()
            return data["daily"]["temperature_2m_max"][0]
        except Exception:
            return 20  # fallback

    def encode_weather(self, weather):
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

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Starting demand prediction...\n")

        items = MachineStock.objects.select_related("product")

        for item in items:
            sales = Item_Sales.objects.filter(
                machine_item=item,
                interval_type="day"
            ).order_by("created_at")

            if sales.count() < 5:
                self.stdout.write(f"Skipping {item.product.name} (not enough data)")
                continue

            X = []
            y = []

            sales_list = list(sales)

            for i in range(3, len(sales_list)):
                s = sales_list[i]

                # --- Lag features ---
                prev_1 = float(sales_list[i - 1].amount)
                prev_2 = float(sales_list[i - 2].amount)
                prev_3 = float(sales_list[i - 3].amount)

                avg_3 = np.mean([prev_1, prev_2, prev_3])

                # --- Time features ---
                weekday = s.created_at.weekday()
                is_weekend = 1 if weekday >= 5 else 0
                week_of_year = s.created_at.isocalendar()[1]

                # --- Weather ---
                temp = float(s.temperature_weather or 20)
                weather_encoded = self.encode_weather(s.weather_type)

                # --- Product info ---
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
            temp = self.get_temperature()

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

            self.stdout.write(
                f"{item.product.name} → Predicted demand: {item.expected_demand}"
            )
            
        self.stdout.write(self.style.SUCCESS("\n✅ Prediction complete!"))