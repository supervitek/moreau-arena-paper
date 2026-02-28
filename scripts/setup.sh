#!/bin/bash
set -e

python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python -c "import simulator; print('simulator OK')"
python -c "import agents; print('agents OK')"
python -c "import analysis; print('analysis OK')"
echo "Setup complete!"
