def test_read_root():
    from main import app

    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}
