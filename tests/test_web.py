from fastapi.testclient import TestClient

from etl.api.main import app


def test_index_served():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Openclaw Quant Dashboard" in r.text


def test_static_assets_served():
    client = TestClient(app)
    for path in ["/static/app.js", "/static/monitor.js", "/static/backtest.js", "/static/style.css", "/static/echarts.min.js"]:
        r = client.get(path)
        assert r.status_code == 200, path
