#!/usr/bin/env python3
"""
Script untuk memperbaiki import paths setelah restructuring
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix import statements in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix import patterns
        patterns = [
            (r'from core\.', 'from src.bot.'),
            (r'from data\.', 'from src.database.'),
            (r'from services\.', 'from src.services.'),
            (r'from database\.', 'from src.database.'),
            (r'from business\.', 'from src.business.'),
            (r'from utils\.', 'from src.utils.'),
            (r'from ui\.', 'from src.ui.'),
            (r'from handlers\.', 'from src.handlers.'),
            (r'from config\.', 'from src.config.'),
            (r'from cogs\.', 'from src.cogs.'),
            (r'import core\.', 'import src.bot.'),
            (r'import data\.', 'import src.database.'),
            (r'import services\.', 'import src.services.'),
            (r'import database\.', 'import src.database.'),
            (r'import business\.', 'import src.business.'),
            (r'import utils\.', 'import src.utils.'),
            (r'import ui\.', 'import src.ui.'),
            (r'import handlers\.', 'import src.handlers.'),
            (r'import config\.', 'import src.config.'),
            (r'import cogs\.', 'import src.cogs.'),
        ]
        
        for old_pattern, new_pattern in patterns:
            content = re.sub(old_pattern, new_pattern, content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed imports in: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Main function to fix all imports"""
    src_dir = Path("src")
    if not src_dir.exists():
        print("❌ src/ directory not found!")
        return
    
    fixed_count = 0
    total_count = 0
    
    # Find all Python files in src/
    for py_file in src_dir.rglob("*.py"):
        total_count += 1
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Total files checked: {total_count}")
    print(f"   Files fixed: {fixed_count}")
    print(f"   Files unchanged: {total_count - fixed_count}")

if __name__ == "__main__":
    main()
