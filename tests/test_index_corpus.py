def test_index_corpus(client):
    response = client.post("/index_corpus")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "chunks_indexed" in data
    assert data["chunks_indexed"] >= 1
