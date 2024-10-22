import pytest
import requests

thread_id = None


def test_start_endpoint():
    global thread_id
    response = requests.get('http://localhost:8080/start')
    assert response.status_code == 200
    assert "thread_id" in response.json()
    assert response.json()["thread_id"] is not None
    thread_id = response.json()["thread_id"]


def test_chat_endpoint():
    global thread_id
    # Replace this URL with the actual URL of your running server
    url = "http://localhost:8080/chat"
    if not thread_id:
        thread_id = "thread_kkG0tGEFmnm6DxdvKnKy7AFv"
    payload = {
        "thread_id":
        thread_id,
        "message":
        "Hello! My name is Blair Vales. Can you help me find a college that I can apply to?"
    }

    response = requests.post(url, json=payload)

    assert response.status_code == 200
    assert "response" in response.json()
    assert response.json()["response"] is not None

    print(response.json()['response'])


if __name__ == "__main__":
    pytest.main()
