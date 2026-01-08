# def test_read_query(client):
#     payload = {
#         "query": "what are AI applications",
#         "top_k": 3
#     }

#     response = client.post("/read", json=payload)

#     assert response.status_code == 200
#     data = response.json()

#     assert "results" in data
#     assert isinstance(data["results"], list)

#     if data["results"]:
#         result = data["results"][0]
#         assert "text" in result
#         assert "source" in result
#         assert "score" in result


def test_read_query(client):
    payload = {
        "query": "what are AI applications",
        "top_k": 3
    }

    response = client.post("/read", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert isinstance(data["results"], list)

    if data["results"]:
        result = data["results"][0]
        assert "text" in result
        assert "source" in result

        # 🔧 FIX: API returns 'similarity_score', not 'score'
        assert "similarity_score" in result
