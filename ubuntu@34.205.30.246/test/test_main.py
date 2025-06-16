from main import client

def test_get_data():
    response = client.get()
    assert response.status_code == 200
    assert response.text == "Data"