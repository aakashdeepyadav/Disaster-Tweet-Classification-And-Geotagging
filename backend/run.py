#!/usr/bin/env python
"""
Wrapper script to run app.py with automatic venv activation check
This makes it easier to run: python run.py instead of activating venv manually
"""
import sys
import os
import subprocess

def find_venv_python():
    """Find Python executable in venv"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for venv in current directory
    venv_python = None
    
    if sys.platform == 'win32':
        # Windows paths - check multiple possible locations
        # Some venvs use 'bin' instead of 'Scripts' (especially if created on Linux/Mac)
        venv_paths = [
            os.path.join(script_dir, 'venv', 'bin', 'python.exe'),  # Check bin first (your case)
            os.path.join(script_dir, 'venv', 'bin', 'pythonw.exe'),
            os.path.join(script_dir, 'venv', 'Scripts', 'python.exe'),  # Standard Windows
            os.path.join(script_dir, 'venv', 'Scripts', 'pythonw.exe'),
        ]
    else:
        # Linux/Mac paths
        venv_paths = [
            os.path.join(script_dir, 'venv', 'bin', 'python'),
            os.path.join(script_dir, 'venv', 'bin', 'python3'),
        ]
    
    for path in venv_paths:
        if os.path.exists(path):
            venv_python = path
            break
    
    # Also check if we're already in a venv
    if not venv_python:
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            # Already in venv, use current Python
            venv_python = sys.executable
    
    return venv_python

def main():
    """Main entry point"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_py = os.path.join(script_dir, 'app.py')
    
    # Check if venv exists
    venv_python = find_venv_python()
    
    if venv_python:
        print(f"✓ Using virtual environment: {venv_python}")
        print("Starting Flask server...\n")
        # Run app.py with venv Python
        os.chdir(script_dir)
        try:
            # Pass through all command line arguments
            subprocess.run([venv_python, app_py] + sys.argv[1:], check=True)
        except KeyboardInterrupt:
            print("\n\nServer stopped by user.")
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            print(f"\n✗ Error starting server: {e}")
            print("\nTroubleshooting:")
            print("1. Make sure venv has packages installed: pip install -r requirements.txt")
            print("2. Check Python version: python --version (should be 3.8-3.13)")
            print("3. See PYTHON_VERSION_WARNING.md if using Python 3.14")
            sys.exit(1)
    else:
        print("="*70)
        print("ERROR: Virtual environment not found!")
        print("="*70)
        print(f"\nCurrent directory: {script_dir}")
        print(f"Looking for venv in: {os.path.join(script_dir, 'venv')}")
        
        # Check if venv directory exists
        venv_dir = os.path.join(script_dir, 'venv')
        if os.path.exists(venv_dir):
            print(f"\n⚠️  venv directory exists but Python executable not found!")
            print("   The venv might not be properly set up.")
        else:
            print(f"\n⚠️  venv directory does not exist!")
        
        print("\nPlease create and activate the virtual environment first:")
        print("\n1. Create venv:")
        print("   python -m venv venv")
        print("\n2. Activate venv:")
        if sys.platform == 'win32':
            print("   .\\venv\\Scripts\\Activate.ps1")
        else:
            print("   source venv/bin/activate")
        print("\n3. Install dependencies:")
        print("   pip install -r requirements.txt")
        print("\n4. Then run:")
        print("   python app.py")
        print("="*70)
        sys.exit(1)

if __name__ == '__main__':
    main()

