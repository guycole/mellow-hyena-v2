#
# Title: pytest.sh
# Description: invoke pytest for hyena app and validator
#
source venv/bin/activate
python -m pytest -q test_hyena_app.py test_validator.py
#
