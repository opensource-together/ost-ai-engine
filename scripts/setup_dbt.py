#!/usr/bin/env python3
"""
Script to setup dbt dependencies and run test models.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None, env=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, cwd=cwd, env=env, check=True, 
                              capture_output=True, text=True)
        print(f"✅ Command succeeded: {' '.join(cmd)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main function to setup dbt."""
    # Get current working directory
    current_dir = Path.cwd()
    print(f"📁 Current working directory: {current_dir}")
    
    # List all files in current directory for debugging
    print("📋 Files in current directory:")
    for item in current_dir.iterdir():
        print(f"   - {item.name}")
    
    # Try different possible dbt directory locations
    possible_dbt_dirs = [
        current_dir / "src" / "dbt",
        current_dir / "dbt",
        Path("/github/workspace/src/dbt"),  # act container path
        Path("/github/workspace/dbt"),      # act container path
        Path("/workspace/src/dbt"),         # alternative act path
        Path("/workspace/dbt"),             # alternative act path
    ]
    
    dbt_dir = None
    for possible_dir in possible_dbt_dirs:
        print(f"🔍 Checking: {possible_dir}")
        if possible_dir.exists():
            print(f"   ✅ Directory exists")
            if (possible_dir / "dbt_project.yml").exists():
                print(f"   ✅ dbt_project.yml found")
                dbt_dir = possible_dir
                break
            else:
                print(f"   ❌ dbt_project.yml not found")
        else:
            print(f"   ❌ Directory does not exist")
    
    if not dbt_dir:
        print(f"❌ dbt project not found. Searched in:")
        for possible_dir in possible_dbt_dirs:
            print(f"   - {possible_dir}")
        return False
    
    print(f"📁 Using dbt directory: {dbt_dir}")
    
    # Verify dbt project structure
    print("🔍 Verifying dbt project structure:")
    required_files = ["dbt_project.yml", "profiles.yml", "packages.yml"]
    for file_name in required_files:
        file_path = dbt_dir / file_name
        if file_path.exists():
            print(f"   ✅ {file_name}")
        else:
            print(f"   ❌ {file_name} missing")
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        'POSTGRES_HOST': 'localhost',
        'POSTGRES_USER': env.get('POSTGRES_USER', 'user'),
        'POSTGRES_PASSWORD': env.get('POSTGRES_PASSWORD', 'password'),
        'POSTGRES_PORT': env.get('POSTGRES_PORT', '5434'),
        'POSTGRES_DB': env.get('POSTGRES_DB', 'OST_PROD'),
    })
    
    print("📦 Installing dbt dependencies...")
    # Use absolute path for dbt commands
    dbt_cmd = ['poetry', 'run', 'dbt', 'deps', '--target', 'ci', '--project-dir', str(dbt_dir)]
    if not run_command(dbt_cmd, env=env):
        print("❌ Failed to install dbt dependencies")
        return False
    
    print("🔧 Running dbt models...")
    # Use absolute path for dbt commands
    dbt_cmd = ['poetry', 'run', 'dbt', 'run', '--select', 'tag:test', '--target', 'ci', '--project-dir', str(dbt_dir)]
    if not run_command(dbt_cmd, env=env):
        print("⚠️  dbt models failed, using fallback method...")
        # Run fallback script
        fallback_script = Path(__file__).parent / "setup_test_data_fallback.py"
        if fallback_script.exists():
            return run_command(['poetry', 'run', 'python', str(fallback_script)], env=env)
        else:
            print("❌ Fallback script not found")
            return False
    
    print("✅ dbt setup completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
