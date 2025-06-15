"""Basic tests to verify setup works"""

def test_simple():
    """Most basic test possible"""
    assert 1 + 1 == 2

def test_import_app():
    """Test that we can import the app"""
    try:
        from backend.main import app
        assert app is not None
    except ImportError as e:
        print(f"Import error: {e}")
        raise
