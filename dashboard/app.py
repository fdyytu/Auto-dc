"""
Standalone Dashboard Web untuk Bot Rental System
Interface web untuk mengelola subscription bot rental (tanpa dependency Discord)
"""

from flask import Flask, render_template, request, jsonify
import sqlite3
import json
from datetime import datetime, timedelta
import uuid
import os

app = Flask(__name__)
app.secret_key = 'rental_bot_dashboard_secret_key_2025'

# Database path
DB_PATH = '/home/user/workspace/dashboard/rental_bot.db'

def init_database():
    """Initialize database dan buat tabel jika belum ada"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create subscription table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT UNIQUE NOT NULL,
            discord_id TEXT NOT NULL,
            plan TEXT NOT NULL,
            status TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            auto_renew BOOLEAN DEFAULT TRUE,
            bot_token TEXT,
            guild_id TEXT,
            features TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_days_remaining(end_date_str):
    """Hitung sisa hari dari end_date"""
    try:
        end_date = datetime.fromisoformat(end_date_str)
        now = datetime.utcnow()
        delta = end_date - now
        return max(0, delta.days)
    except:
        return 0

def is_subscription_active(status, end_date_str):
    """Cek apakah subscription masih aktif"""
    if status != 'active':
        return False
    try:
        end_date = datetime.fromisoformat(end_date_str)
        return datetime.utcnow() < end_date
    except:
        return False

@app.route('/')
def dashboard():
    """Dashboard utama"""
    return render_template('dashboard.html')

@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    """API endpoint untuk mendapatkan semua subscription"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM subscriptions ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        subscriptions = []
        for row in rows:
            sub_dict = dict(row)
            # Parse features
            try:
                sub_dict['features'] = json.loads(sub_dict['features']) if sub_dict['features'] else {}
            except:
                sub_dict['features'] = {}
            
            # Calculate additional fields
            sub_dict['days_remaining'] = calculate_days_remaining(sub_dict['end_date'])
            sub_dict['is_active'] = is_subscription_active(sub_dict['status'], sub_dict['end_date'])
            
            subscriptions.append(sub_dict)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': subscriptions,
            'message': f'Berhasil mengambil {len(subscriptions)} subscription'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Gagal mengambil data subscription'
        }), 500

@app.route('/api/subscriptions', methods=['POST'])
def create_subscription():
    """API endpoint untuk membuat subscription baru"""
    try:
        data = request.get_json()
        discord_id = data.get('discord_id')
        plan = data.get('plan', 'basic')
        duration_days = data.get('duration_days', 30)
        
        if not discord_id:
            return jsonify({
                'success': False,
                'error': 'Discord ID diperlukan',
                'message': 'Discord ID tidak boleh kosong'
            }), 400
        
        # Generate tenant ID
        tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"
        
        # Calculate dates
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=duration_days)
        
        # Default features based on plan
        features_map = {
            'basic': {
                "max_commands": 50,
                "max_users": 100,
                "custom_prefix": False,
                "analytics": False,
                "priority_support": False
            },
            'premium': {
                "max_commands": 200,
                "max_users": 500,
                "custom_prefix": True,
                "analytics": True,
                "priority_support": False
            },
            'enterprise': {
                "max_commands": -1,
                "max_users": -1,
                "custom_prefix": True,
                "analytics": True,
                "priority_support": True
            }
        }
        
        features = features_map.get(plan, features_map['basic'])
        
        # Insert to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO subscriptions 
            (tenant_id, discord_id, plan, status, start_date, end_date, auto_renew, features, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tenant_id,
            discord_id,
            plan,
            'pending',
            start_date.isoformat(),
            end_date.isoformat(),
            True,
            json.dumps(features),
            start_date.isoformat(),
            start_date.isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        # Return created subscription
        subscription = {
            'tenant_id': tenant_id,
            'discord_id': discord_id,
            'plan': plan,
            'status': 'pending',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'auto_renew': True,
            'features': features,
            'days_remaining': duration_days,
            'is_active': False,
            'created_at': start_date.isoformat(),
            'updated_at': start_date.isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': subscription,
            'message': f'Subscription {plan} berhasil dibuat untuk {duration_days} hari'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Gagal membuat subscription'
        }), 500

@app.route('/api/subscriptions/<tenant_id>/status', methods=['PUT'])
def update_subscription_status(tenant_id):
    """API endpoint untuk update status subscription"""
    try:
        data = request.get_json()
        status = data.get('status')
        
        if not status:
            return jsonify({
                'success': False,
                'error': 'Status diperlukan',
                'message': 'Status tidak boleh kosong'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updated_at = datetime.utcnow().isoformat()
        cursor.execute(
            "UPDATE subscriptions SET status = ?, updated_at = ? WHERE tenant_id = ?",
            (status, updated_at, tenant_id)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Subscription tidak ditemukan',
                'message': f'Tenant ID {tenant_id} tidak ditemukan'
            }), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {'tenant_id': tenant_id, 'new_status': status},
            'message': f'Status subscription berhasil diupdate ke {status}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Gagal update status subscription'
        }), 500

@app.route('/api/subscriptions/<tenant_id>/extend', methods=['PUT'])
def extend_subscription(tenant_id):
    """API endpoint untuk perpanjang subscription"""
    try:
        data = request.get_json()
        days = data.get('days', 30)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current subscription
        cursor.execute("SELECT end_date FROM subscriptions WHERE tenant_id = ?", (tenant_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Subscription tidak ditemukan',
                'message': f'Tenant ID {tenant_id} tidak ditemukan'
            }), 404
        
        # Calculate new end date
        current_end_date = datetime.fromisoformat(row['end_date'])
        new_end_date = current_end_date + timedelta(days=days)
        updated_at = datetime.utcnow().isoformat()
        
        # Update database
        cursor.execute(
            "UPDATE subscriptions SET end_date = ?, updated_at = ? WHERE tenant_id = ?",
            (new_end_date.isoformat(), updated_at, tenant_id)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'tenant_id': tenant_id,
                'extended_days': days,
                'new_end_date': new_end_date.isoformat()
            },
            'message': f'Subscription berhasil diperpanjang {days} hari'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Gagal perpanjang subscription'
        }), 500

@app.route('/api/stats')
def get_stats():
    """API endpoint untuk statistik"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total subscriptions
        cursor.execute("SELECT COUNT(*) as total FROM subscriptions")
        total = cursor.fetchone()['total']
        
        # Active subscriptions
        cursor.execute("SELECT COUNT(*) as active FROM subscriptions WHERE status = 'active'")
        active = cursor.fetchone()['active']
        
        # Subscriptions by plan
        cursor.execute("SELECT plan, COUNT(*) as count FROM subscriptions GROUP BY plan")
        plan_rows = cursor.fetchall()
        by_plan = {row['plan']: row['count'] for row in plan_rows}
        
        # Calculate estimated revenue
        plan_prices = {'basic': 10, 'premium': 25, 'enterprise': 50}
        estimated_revenue = sum(by_plan.get(plan, 0) * price for plan, price in plan_prices.items())
        
        conn.close()
        
        stats = {
            'total': total,
            'active': active,
            'by_plan': by_plan,
            'estimated_monthly_revenue': estimated_revenue
        }
        
        return jsonify({
            'success': True,
            'data': stats,
            'message': 'Statistik subscription berhasil diambil'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Gagal mengambil statistik'
        }), 500

@app.route('/api/subscription/<discord_id>')
def get_user_subscription(discord_id):
    """API endpoint untuk mendapatkan subscription user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM subscriptions WHERE discord_id = ? ORDER BY created_at DESC LIMIT 1",
            (discord_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Subscription tidak ditemukan',
                'message': f'Tidak ada subscription untuk Discord ID {discord_id}'
            }), 404
        
        subscription = dict(row)
        try:
            subscription['features'] = json.loads(subscription['features']) if subscription['features'] else {}
        except:
            subscription['features'] = {}
        
        subscription['days_remaining'] = calculate_days_remaining(subscription['end_date'])
        subscription['is_active'] = is_subscription_active(subscription['status'], subscription['end_date'])
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': subscription,
            'message': 'Subscription berhasil ditemukan'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Gagal mengambil subscription user'
        }), 500

@app.route('/plans')
def plans():
    """Halaman paket subscription"""
    return render_template('plans.html')

@app.route('/admin')
def admin():
    """Halaman admin"""
    return render_template('dashboard.html')

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
