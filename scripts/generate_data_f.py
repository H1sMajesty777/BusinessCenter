import random
import datetime
import psycopg2
from faker import Faker

# ================= НАСТРОЙКИ =================
DB_NAME = "bc"
DB_USER = "postgres"
DB_PASSWORD = "1postgres1"      
DB_HOST = "localhost"
DB_PORT = "5432"

NUM_NEW_USERS = 50
DAILY_VIEWS_BASE = 15
# ===============================================

fake = Faker('ru_RU')
random.seed(42)

def get_seasonal_factor(date):
    month = date.month
    if month in [3, 4, 5, 9, 10]:
        return 1.5
    elif month in [1, 7, 8]:
        return 0.4
    else:
        return 1.0

def get_duration_by_price(price):
    if price < 25000:
        return random.randint(10, 45)
    elif price < 60000:
        return random.randint(30, 120)
    elif price < 100000:
        return random.randint(60, 240)
    else:
        return random.randint(120, 600)

def get_contact_probability(price, duration):
    base_prob = 0.15
    if duration > 120:
        base_prob += 0.25
    if price > 80000:
        base_prob += 0.10
    return min(base_prob, 0.6)

def main():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        conn.autocommit = False
        print("Connected successfully!")
    except Exception as e:
        print(f"Connection error: {e}")
        return

    # ОЧИСТКА СТАРЫХ ДАННЫХ
    print("Clearing old historical data...")
    try:
        cur.execute("TRUNCATE TABLE payments, contracts, applications, office_views RESTART IDENTITY CASCADE")
        conn.commit()
        print("Old data cleared successfully.")
    except Exception as e:
        print(f"Warning - could not clear  {e}")
        conn.rollback()

    print(f"Creating {NUM_NEW_USERS} new clients...")
    user_ids = [3]
    
    for _ in range(NUM_NEW_USERS):
        login = f"client_{fake.user_name()}_{random.randint(100, 999)}"
        email = fake.email()
        name = fake.name()
        phone = fake.phone_number()
        
        try:
            cur.execute("""
                INSERT INTO users (login, password_hash, email, full_name, phone, role_id, is_active, created_at)
                VALUES (%s, 'client123', %s, %s, %s, 3, TRUE, %s)
                RETURNING id
            """, (login, email, name, phone, datetime.datetime.now()))
            user_ids.append(cur.fetchone()[0])
            conn.commit()
        except Exception as e:
            conn.rollback()
            if "unique" not in str(e).lower():
                print(f"Warning: {e}")
            continue

    print(f"   Total clients available: {len(user_ids)}")

    print("Loading offices list...")
    cur.execute("SELECT id, office_number, price_per_month, floor, area_sqm FROM offices")
    offices = cur.fetchall()
    print(f"   Found offices: {len(offices)}")

    # Проверка, какое поле используется в таблице offices
    print("Checking offices table structure...")
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'offices' AND column_name IN ('status_id', 'is_free')
    """)
    available_columns = [row[0] for row in cur.fetchall()]
    print(f"   Available columns: {available_columns}")
    
    use_status_id = 'status_id' in available_columns
    use_is_free = 'is_free' in available_columns
    
    if use_status_id:
        print("   Using: status_id field")
    elif use_is_free:
        print("   Using: is_free field")
    else:
        print("   WARNING: Neither status_id nor is_free found!")

    print("Generating historical data (730 days)...")
    
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=730)
    
    views_data = []
    applications_data = []
    contracts_data = []
    payments_data = []
    
    app_id_counter = 1
    contract_id_counter = 1
    
    current_date = start_date
    day_count = 0
    
    while current_date <= end_date:
        day_count += 1
        seasonal_factor = get_seasonal_factor(current_date)
        daily_views = int(DAILY_VIEWS_BASE * seasonal_factor * random.uniform(0.7, 1.3))
        
        for _ in range(daily_views):
            user_id = random.choice(user_ids)
            office = random.choice(offices)
            office_id, office_number, price, floor, area = office
            
            duration = get_duration_by_price(price)
            contact_prob = get_contact_probability(price, duration)
            is_contacted = random.random() < contact_prob
            
            view_hour = random.randint(9, 20)
            view_minute = random.randint(0, 59)
            view_time = current_date.replace(hour=view_hour, minute=view_minute)
            
            views_data.append((user_id, office_id, view_time, duration, is_contacted))
            
            if is_contacted and random.random() < 0.30:
                app_date = view_time + datetime.timedelta(days=random.randint(1, 5))
                
                status_roll = random.random()
                if status_roll < 0.50:
                    status_id = 2
                elif status_roll < 0.80:
                    status_id = 3
                else:
                    status_id = 1
                
                reviewed_at = app_date + datetime.timedelta(days=random.randint(1, 3)) if status_id != 1 else None
                
                current_app_id = app_id_counter
                applications_data.append((user_id, office_id, status_id, "Auto-generated application", app_date, reviewed_at))
                
                if status_id == 2:
                    signed_date = app_date + datetime.timedelta(days=random.randint(2, 10))
                    lease_start = signed_date + datetime.timedelta(days=random.randint(5, 30))
                    lease_duration_months = random.choice([6, 12, 12, 12, 24])
                    lease_end = lease_start + datetime.timedelta(days=lease_duration_months * 30)
                    total_amount = price * lease_duration_months
                    
                    contracts_data.append((current_app_id, user_id, office_id, lease_start.date(), lease_end.date(), total_amount, 4, signed_date))
                    
                    payment_date = lease_start
                    payment_num = 0
                    while payment_date < lease_end and payment_num < 3:
                        payment_amount = price
                        transaction_id = f"TRX-{current_date.year}-{random.randint(10000, 99999)}"
                        payments_data.append((contract_id_counter, payment_amount, payment_date.date(), 4, transaction_id))
                        
                        payment_date += datetime.timedelta(days=30)
                        payment_num += 1
                    
                    contract_id_counter += 1
                
                app_id_counter += 1
        
        current_date += datetime.timedelta(days=1)
        
        if day_count % 100 == 0:
            print(f"   ... processed {day_count} of 730 days")

    print("Saving data to database...")
    
    try:
        # Views
        if views_data:
            cur.executemany("""
                INSERT INTO office_views (user_id, office_id, viewed_at, duration_seconds, is_contacted)
                VALUES (%s, %s, %s, %s, %s)
            """, views_data)
            print(f"   Added views: {len(views_data)}")
        
        # Applications
        if applications_data:
            cur.executemany("""
                INSERT INTO applications (user_id, office_id, status_id, comment, created_at, reviewed_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, applications_data)
            print(f"   Added applications: {len(applications_data)}")
        
        # Contracts
        if contracts_data:
            cur.executemany("""
                INSERT INTO contracts (application_id, user_id, office_id, start_date, end_date, total_amount, status_id, signed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, contracts_data)
            print(f"   Added contracts: {len(contracts_data)}")
        
        # Payments
        if payments_data:
            cur.executemany("""
                INSERT INTO payments (contract_id, amount, payment_date, status_id, transaction_id)
                VALUES (%s, %s, %s, %s, %s)
            """, payments_data)
            print(f"   Added payments: {len(payments_data)}")
        
        # Обновление статусов офисов (адаптивное)
        print("Updating office statuses...")
        if use_status_id:
            cur.execute("""
                UPDATE offices 
                SET status_id = 7 
                WHERE id IN (
                    SELECT DISTINCT office_id 
                    FROM contracts 
                    WHERE status_id = 4 
                    AND end_date > NOW()
                )
            """)
        elif use_is_free:
            cur.execute("""
                UPDATE offices 
                SET is_free = FALSE 
                WHERE id IN (
                    SELECT DISTINCT office_id 
                    FROM contracts 
                    WHERE status_id = 4 
                    AND end_date > NOW()
                )
            """)
        
        updated = cur.rowcount
        print(f"   Marked offices as rented: {updated}")
        
        conn.commit()
        print("\nSUCCESS! Data generated successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"\nError saving  {e}")
        raise

    finally:
        cur.close()
        conn.close()

    print("\n" + "="*50)
    print("STATISTICS:")
    print("="*50)
    print(f"Period: {start_date.date()} - {end_date.date()}")
    print(f"Total users: {len(user_ids)}")
    print(f"Office views: {len(views_data)}")
    print(f"Applications: {len(applications_data)}")
    print(f"Contracts: {len(contracts_data)}")
    print(f"Payments: {len(payments_data)}")
    
    if contracts_data:
        total_revenue = sum(c[5] for c in contracts_data)
        print(f"Total revenue: {total_revenue:,.0f} RUB")
    
    print("="*50)

if __name__ == "__main__":
    main()