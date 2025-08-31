#!/usr/bin/env python3
"""
Unified script to test CI jobs locally with act.
Usage: python scripts/tests/ci_local.py [job_name|all]
Examples: 
  python scripts/tests/ci_local.py tests-unit
  python scripts/tests/ci_local.py all
"""

import sys
import subprocess
import os
from pathlib import Path


def check_prerequisites():
    """Check if act and Docker are available."""
    print("🔍 Checking prerequisites...")
    
    # Check if act is installed
    try:
        subprocess.run(["act", "--version"], capture_output=True, check=True)
        print("✅ act is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ act is not installed")
        print("   Install with: brew install act (macOS)")
        print("   Or visit: https://github.com/nektos/act")
        return False
    
    # Check if Docker is running
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
        print("✅ Docker is running")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not running")
        print("   Please start Docker first")
        return False
    
    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Please create .env with your environment variables")
        return False
    else:
        print("✅ .env file found")
    
    return True


def get_available_jobs():
    """Get list of available CI jobs."""
    return [
        "setup",
        "tests-unit", 
        "tests-integration",
        "tests-performance",
        "go-lint",
        "coverage"
    ]


def run_act_job(job_name):
    """Run a specific act job."""
    print(f"🚀 Running job: {job_name}")
    print("-" * 50)
    
    cmd = [
        "act", "-j", job_name,
        "--secret-file", ".env",
        "--pull=false",
        "--container-daemon-socket", "/var/run/docker.sock",
        "--env-file", ".env"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"✅ Job {job_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Job {job_name} failed with exit code {e.returncode}")
        return False


def run_all_jobs():
    """Run all CI jobs in sequence."""
    jobs = get_available_jobs()
    
    print("🚀 Testing all CI jobs...")
    print(f"📋 Jobs to run: {', '.join(jobs)}")
    print("=" * 60)
    
    results = {}
    
    for i, job in enumerate(jobs, 1):
        print(f"\n{i}️⃣ Testing {job}...")
        success = run_act_job(job)
        results[job] = success
        
        if not success:
            print(f"⚠️  Job {job} failed, but continuing with remaining jobs...")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    successful_jobs = [job for job, success in results.items() if success]
    failed_jobs = [job for job, success in results.items() if not success]
    
    print(f"✅ Successful jobs ({len(successful_jobs)}): {', '.join(successful_jobs)}")
    if failed_jobs:
        print(f"❌ Failed jobs ({len(failed_jobs)}): {', '.join(failed_jobs)}")
    
    all_success = len(failed_jobs) == 0
    if all_success:
        print("🎉 All jobs completed successfully!")
    else:
        print(f"⚠️  {len(failed_jobs)} job(s) failed")
    
    return all_success


def main():
    """Main function."""
    print("🧪 CI Local Testing Tool")
    print("=" * 40)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Get job name from command line arguments
    if len(sys.argv) < 2:
        job_name = "all"
    else:
        job_name = sys.argv[1]
    
    available_jobs = get_available_jobs()
    
    # Validate job name
    if job_name not in available_jobs and job_name != "all":
        print(f"❌ Invalid job: {job_name}")
        print(f"Available jobs: {', '.join(available_jobs)}, all")
        print("\nUsage examples:")
        print("  python scripts/tests/ci_local.py tests-unit")
        print("  python scripts/tests/ci_local.py all")
        sys.exit(1)
    
    # Run the requested job(s)
    if job_name == "all":
        success = run_all_jobs()
    else:
        success = run_act_job(job_name)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
