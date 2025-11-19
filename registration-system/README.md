# Salon Prototype 2

## Description

A centralized booking platform for salon businesses and their customers. Business owners register their salons with the system and receive notifications when customers book appointments. Customers can browse registered salons and book appointments directly through the platform.

## Features

### Client Management (Business Owners/Salons)
- Register salon with the centralized system
- Toggle salon status (open/closed for the day)
- Create and modify available time slots (1-hour slots)
- **Set "Ask me before booking" option for each slot (optional)**
- Receive booking requests for slots requiring approval
- Approve or reject booking requests
- Receive notifications for confirmed bookings
- View appointments

### Customer Management
- Automatic registration on first use
- **New customers:** Receive salon suggestions within 2km radius
- **Returning customers:** Receive two types of suggestions:
  1. Salons from booking history (previously visited)
  2. Nearby salons within 2km radius
- Search for salons if suggestions aren't suitable
- View salon details (services, pricing, availability)
- Select time slot and initiate booking

### Centralized Booking System
- Accept customer booking requests
- **Check if slot requires salon owner approval:**
  - If "Ask me before booking" is **enabled** → Request approval from salon owner → Wait for confirmation → Validate → Process payment → Confirm booking
  - If "Ask me before booking" is **disabled** → Validate → Process payment → Automatically approve and book slot
- **Payment Processing:**
  - Online payment (verify payment status)
  - Cash payment option (pay at salon)
- Confirm booking to customer
- Notify salon owner of confirmed booking
- Track all bookings
- **Maintain complete booking history for each customer**

### System Administration & Analytics
- Manage salon profiles (services, pricing, descriptions, operating hours, etc.)
- Approve salon registrations
- Manage all customer and client data
- Store and maintain historical booking records
- **Analytics Dashboard:**
  - **Customer Analytics:**
    - Individual customer booking patterns
    - Customer booking history
    - Customer retention rates
    - Frequent customers
    - Customer preferences
    - Region-wise customer distribution (state/city/street)
  - **Client Analytics (Salon Owners):**
    - Individual salon performance
    - Booking trends per salon (increase/decrease)
    - Revenue per salon
    - Popular time slots
    - Approval/rejection rates
    - Region-wise salon performance (state/city/street)

## Tech Stack
(To be determined)

## Getting Started
(To be added)

## Configuration
(To be added)

## Development
(To be added)

## Roadmap / Future Features
(To be added)
