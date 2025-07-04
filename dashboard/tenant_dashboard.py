"""
Tenant Dashboard untuk Admin Interface
Dashboard web untuk konfigurasi tenant melalui web interface
"""

from flask import Flask, render_template, request, jsonify, Blueprint
import sqlite3
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Blueprint untuk tenant dashboard
tenant_bp = Blueprint('tenant', __name__, url_prefix='/tenant')

def get_tenant_db_connection():
    """Get database connection untuk tenant"""
    conn = sqlite3.connect('/home/user/workspace/dashboard/rental_bot.db')
    conn.row_factory = sqlite3.Row
    return conn

@tenant_bp.route('/dashboard')
def tenant_dashboard():
    """Dashboard utama untuk tenant management"""
    return render_template('tenant_dashboard.html')

@tenant_bp.route('/api/tenants', methods=['GET'])
def get_all_tenants():
    """API endpoint untuk mendapatkan semua tenant"""
    try:
        conn = get_tenant_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.*, s.plan, s.status as subscription_status 
            FROM tenants t 
            LEFT JOIN subscriptions s ON t.discord_id = s.discord_id
            ORDER BY t.created_at DESC
        """)
        rows = cursor.fetchall()
        
        tenants = []
        for row in rows:
            tenant_dict = dict(row)
            # Parse JSON fields
            try:
                tenant_dict['features'] = json.loads(tenant_dict.get('features', '{}'))
                tenant_dict['channels'] = json.loads(tenant_dict.get('channels', '{}'))
                tenant_dict['permissions'] = json.loads(tenant_dict.get('permissions', '{}'))
                tenant_dict['bot_config'] = json.loads(tenant_dict.get('bot_config', '{}'))
            except:
                tenant_dict['features'] = {}
                tenant_dict['channels'] = {}
                tenant_dict['permissions'] = {}
                tenant_dict['bot_config'] = {}
            
            tenants.append(tenant_dict)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': tenants,
            'message': f'Berhasil mengambil {len(tenants)} tenant'
        })
        
    except Exception as e:
        logger.error(f"Error getting tenants: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Gagal mengambil data tenant'
        }), 500

@tenant_bp.route('/api/tenants/<tenant_id>/features', methods=['PUT'])
def update_tenant_features(tenant_id):
    """API endpoint untuk update fitur tenant"""
    try:
        data = request.get_json()
        features = data.get('features', {})
        
        conn = get_tenant_db_connection()
        cursor = conn.cursor()
        
        # Ambil tenant saat ini
        cursor.execute("SELECT * FROM tenants WHERE tenant_id = ?", (tenant_id,))
        tenant = cursor.fetchone()
        
        if not tenant:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Tenant tidak ditemukan',
                'message': f'Tenant {tenant_id} tidak ditemukan'
            }), 404
        
        # Update features
        current_features = json.loads(tenant['features'] or '{}')
        current_features.update(features)
        
        cursor.execute("""
            UPDATE tenants 
            SET features = ?, updated_at = ? 
            WHERE tenant_id = ?
        """, (
            json.dumps(current_features),
            datetime.utcnow().isoformat(),
            tenant_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {'features': current_features},
            'message': 'Fitur tenant berhasil diupdate'
        })
        
    except Exception as e:
        logger.error(f"Error updating tenant features: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Gagal update fitur tenant'
        }), 500

@tenant_bp.route('/api/tenants/<tenant_id>/channels', methods=['PUT'])
def update_tenant_channels(tenant_id):
    """API endpoint untuk update channel configuration"""
    try:
        data = request.get_json()
        channels = data.get('channels', {})
        
        conn = get_tenant_db_connection()
        cursor = conn.cursor()
        
        # Ambil tenant saat ini
        cursor.execute("SELECT * FROM tenants WHERE tenant_id = ?", (tenant_id,))
        tenant = cursor.fetchone()
        
        if not tenant:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Tenant tidak ditemukan',
                'message': f'Tenant {tenant_id} tidak ditemukan'
            }), 404
        
        # Update channels
        current_channels = json.loads(tenant['channels'] or '{}')
        current_channels.update(channels)
        
        cursor.execute("""
            UPDATE tenants 
            SET channels = ?, updated_at = ? 
            WHERE tenant_id = ?
        """, (
            json.dumps(current_channels),
            datetime.utcnow().isoformat(),
            tenant_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {'channels': current_channels},
            'message': 'Konfigurasi channel berhasil diupdate'
        })
        
    except Exception as e:
        logger.error(f"Error updating tenant channels: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Gagal update konfigurasi channel'
        }), 500
