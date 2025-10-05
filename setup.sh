#!/bin/bash
# Setup script for Policy Completeness Framework

echo "==========================================="
echo "Policy Completeness Framework Setup"
echo "==========================================="

# Check Python installation
if command -v python3 &> /dev/null; then
    echo "[OK] Python3 found"
else
    echo "[ERROR] Python3 not found. Please install Python 3.8 or higher"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q pandas numpy jupyter dataclasses-json

echo ""
echo "==========================================="
echo "Setup Complete!"
echo "==========================================="
echo ""
echo "To get started:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start Jupyter: jupyter notebook"
echo "3. Open notebooks/01_incident_analysis.ipynb"
echo ""
echo "For executive summary, open: results/dashboard.html"
echo ""
echo "Key files to review:"
echo "- README.md                    : Overview and competitive advantages"
echo "- notebooks/02_multi_turn_pipeline.ipynb : Working test pipeline"
echo "- notebooks/03_competitive_baseline.ipynb : Competitor analysis"  
echo "- docs/EXECUTIVE.md            : Non-technical summary"
echo "- results/dashboard.html       : Visual dashboard"
echo ""
