import os

# Isolate test environment configuration
os.environ["SECRET_KEY"] = "test_only_secret_key_do_not_use_in_prod"
os.environ["DATABASE_URL"] = "sqlite:///./test_civicvision_isolated.db"
