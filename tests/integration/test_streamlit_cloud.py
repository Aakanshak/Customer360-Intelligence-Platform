from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_bundled_streamlit_app_renders_without_external_api(monkeypatch):
    monkeypatch.delenv("API_URL", raising=False)
    app_path = Path(__file__).resolve().parents[2] / "frontend" / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=120).run()
    assert not app.exception
    assert len(app.metric) == 5
    assert len(app.get("plotly_chart")) == 3
