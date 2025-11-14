from locust import HttpUser, task

class WebsiteUser(HttpUser):
    @task
    def send_request(self):
        res = self.client.post(
            "/api/v1/makeRequest",
            json={
                    "action": "CREATE-CLIENT",
                    "barber_shop": {
                        "id": 101,
                        "name": "The Classic Cut",
                        "owner": "Rajesh Kumar",
                        "address": {
                            "street": "123 Main Street",
                            "city": "Chennai",
                            "state": "Tamil Nadu",
                            "zip_code": "600001",
                            "landmark": "Near Central Park"
                        },
                        "contact": {
                            "phone": "+91-9876543210",
                            "email": "contact@classiccut.com",
                            "whatsapp": "+91-9876543210"
                        },
                        "services": [
                            {
                                "name": "Haircut",
                                "price": 300,
                                "duration_minutes": 30
                            },
                            {
                                "name": "Shave",
                                "price": 150,
                                "duration_minutes": 15
                            },
                            {
                                "name": "Hair Color",
                                "price": 800,
                                "duration_minutes": 60
                            },
                            {
                                "name": "Beard Trim",
                                "price": 200,
                                "duration_minutes": 20
                            }
                        ],
                        "opening_hours": {
                            "monday": "09:00-19:00",
                            "tuesday": "09:00-19:00",
                            "wednesday": "09:00-19:00",
                            "thursday": "09:00-19:00",
                            "friday": "09:00-20:00",
                            "saturday": "09:00-20:00",
                            "sunday": "10:00-18:00"
                        },
                        "facilities": [
                            "Free WiFi",
                            "AC",
                            "Online Booking",
                            "Parking"
                        ],
                        "social_media": {
                            "facebook": "https://facebook.com/classiccut",
                            "instagram": "https://instagram.com/classiccut"
                        },
                        "notes": "Friendly staff, hygienic tools, and walk-in customers welcome."
                    }
                }
        )

        print(res.json())
