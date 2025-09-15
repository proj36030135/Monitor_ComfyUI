"""Testes para funcionalidades de sessões.

Testa CRUD operations, regras de negócio e endpoints
relacionados ao gerenciamento de sessões.
"""

import pytest
from fastapi.testclient import TestClient

from app.crud.sessions import SessionCRUD
from app.schemas import SessionCreate, SessionUpdate, SessionQuery, SessionStatus
from app.models import Session


class TestSessionCRUD:
    """Testes para operações CRUD de sessões."""
    
    def test_create_session(self, db_session, sample_session_data):
        """Testa criação de sessão."""
        session_data = SessionCreate(**sample_session_data)
        session = SessionCRUD.create(db_session, session_data)
        
        assert session.id is not None
        assert session.name == sample_session_data["name"]
        assert session.note == sample_session_data["note"]
        assert session.status == SessionStatus.INACTIVE
        assert session.created_at_ms is not None
        assert session.updated_at_ms is not None
    
    def test_get_session_by_id(self, db_session, sample_session_data):
        """Testa busca de sessão por ID."""
        # Criar sessão
        session_data = SessionCreate(**sample_session_data)
        created_session = SessionCRUD.create(db_session, session_data)
        
        # Buscar por ID
        found_session = SessionCRUD.get_by_id(db_session, created_session.id)
        
        assert found_session is not None
        assert found_session.id == created_session.id
        assert found_session.name == created_session.name
    
    def test_get_nonexistent_session(self, db_session):
        """Testa busca de sessão inexistente."""
        session = SessionCRUD.get_by_id(db_session, "nonexistent-id")
        assert session is None
    
    def test_list_sessions(self, db_session, sample_session_data):
        """Testa listagem de sessões."""
        # Criar algumas sessões
        for i in range(3):
            session_data = SessionCreate(
                name=f"Sessão {i+1}",
                note=f"Sessão de teste {i+1}",
                tags=["teste"]
            )
            SessionCRUD.create(db_session, session_data)
        
        # Listar todas
        query = SessionQuery(limit=10, offset=0)
        sessions = SessionCRUD.list_sessions(db_session, query)
        
        assert len(sessions) == 3
        assert all(s.name.startswith("Sessão") for s in sessions)
    
    def test_update_session(self, db_session, sample_session_data):
        """Testa atualização de sessão."""
        # Criar sessão
        session_data = SessionCreate(**sample_session_data)
        session = SessionCRUD.create(db_session, session_data)
        
        # Atualizar
        update_data = SessionUpdate(
            name="Sessão Atualizada",
            note="Nota atualizada"
        )
        updated_session = SessionCRUD.update(db_session, session.id, update_data)
        
        assert updated_session is not None
        assert updated_session.name == "Sessão Atualizada"
        assert updated_session.note == "Nota atualizada"
        assert updated_session.updated_at_ms >= session.updated_at_ms
    
    def test_start_session(self, db_session, sample_session_data):
        """Testa início de sessão."""
        # Criar sessão
        session_data = SessionCreate(**sample_session_data)
        session = SessionCRUD.create(db_session, session_data)
        
        # Iniciar
        started_session = SessionCRUD.start_session(db_session, session.id)
        
        assert started_session is not None
        assert started_session.status == SessionStatus.ACTIVE
        assert started_session.started_at_ms is not None
        assert started_session.ended_at_ms is None
    
    def test_only_one_active_session(self, db_session, sample_session_data):
        """Testa regra de apenas uma sessão ativa."""
        # Criar duas sessões
        session1_data = SessionCreate(name="Sessão 1", tags=[])
        session2_data = SessionCreate(name="Sessão 2", tags=[])
        
        session1 = SessionCRUD.create(db_session, session1_data)
        session2 = SessionCRUD.create(db_session, session2_data)
        
        # Iniciar primeira sessão
        SessionCRUD.start_session(db_session, session1.id)
        
        # Verificar que está ativa
        active_session = SessionCRUD.get_active_session(db_session)
        assert active_session.id == session1.id
        
        # Iniciar segunda sessão
        SessionCRUD.start_session(db_session, session2.id)
        
        # Verificar que agora a segunda está ativa
        active_session = SessionCRUD.get_active_session(db_session)
        assert active_session.id == session2.id
        
        # Verificar que a primeira foi encerrada
        session1_updated = SessionCRUD.get_by_id(db_session, session1.id)
        assert session1_updated.status == SessionStatus.ENDED
    
    def test_pause_and_resume_session(self, db_session, sample_session_data):
        """Testa pausa e retomada de sessão."""
        # Criar e iniciar sessão
        session_data = SessionCreate(**sample_session_data)
        session = SessionCRUD.create(db_session, session_data)
        SessionCRUD.start_session(db_session, session.id)
        
        # Pausar
        paused_session = SessionCRUD.pause_session(db_session, session.id)
        assert paused_session.status == SessionStatus.PAUSED
        
        # Retomar
        resumed_session = SessionCRUD.resume_session(db_session, session.id)
        assert resumed_session.status == SessionStatus.ACTIVE
    
    def test_end_session(self, db_session, sample_session_data):
        """Testa encerramento de sessão."""
        # Criar e iniciar sessão
        session_data = SessionCreate(**sample_session_data)
        session = SessionCRUD.create(db_session, session_data)
        SessionCRUD.start_session(db_session, session.id)
        
        # Encerrar
        ended_session = SessionCRUD.end_session(db_session, session.id)
        
        assert ended_session.status == SessionStatus.ENDED
        assert ended_session.ended_at_ms is not None
    
    def test_delete_session(self, db_session, sample_session_data):
        """Testa remoção de sessão."""
        # Criar sessão
        session_data = SessionCreate(**sample_session_data)
        session = SessionCRUD.create(db_session, session_data)
        
        # Deletar
        deleted = SessionCRUD.delete(db_session, session.id)
        assert deleted is True
        
        # Verificar que não existe mais
        found_session = SessionCRUD.get_by_id(db_session, session.id)
        assert found_session is None


class TestSessionAPI:
    """Testes para endpoints da API de sessões."""
    
    def test_create_session_endpoint(self, client, sample_session_data):
        """Testa endpoint POST /sessions."""
        response = client.post("/sessions", json=sample_session_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_session_data["name"]
        assert data["status"] == "inactive"
        assert "id" in data
        assert "created_at_ms" in data
    
    def test_list_sessions_endpoint(self, client, sample_session_data):
        """Testa endpoint GET /sessions."""
        # Criar algumas sessões
        for i in range(2):
            session_data = {
                "name": f"Sessão {i+1}",
                "note": f"Teste {i+1}",
                "tags": ["teste"]
            }
            client.post("/sessions", json=session_data)
        
        # Listar
        response = client.get("/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("id" in session for session in data)
    
    def test_get_session_endpoint(self, client, sample_session_data):
        """Testa endpoint GET /sessions/{id}."""
        # Criar sessão
        create_response = client.post("/sessions", json=sample_session_data)
        session_id = create_response.json()["id"]
        
        # Buscar por ID
        response = client.get(f"/sessions/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["name"] == sample_session_data["name"]
        assert "summary" in data
    
    def test_get_nonexistent_session_endpoint(self, client):
        """Testa endpoint GET /sessions/{id} para sessão inexistente."""
        response = client.get("/sessions/nonexistent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data["detail"]
    
    def test_update_session_endpoint(self, client, sample_session_data):
        """Testa endpoint PATCH /sessions/{id}."""
        # Criar sessão
        create_response = client.post("/sessions", json=sample_session_data)
        session_id = create_response.json()["id"]
        
        # Atualizar
        update_data = {"name": "Nome Atualizado", "note": "Nova nota"}
        response = client.patch(f"/sessions/{session_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Nome Atualizado"
        assert data["note"] == "Nova nota"
    
    def test_session_lifecycle_endpoints(self, client, sample_session_data):
        """Testa endpoints de ciclo de vida da sessão."""
        # Criar sessão
        create_response = client.post("/sessions", json=sample_session_data)
        session_id = create_response.json()["id"]
        
        # Iniciar
        start_response = client.post(f"/sessions/{session_id}/start")
        assert start_response.status_code == 200
        assert start_response.json()["status"] == "active"
        
        # Pausar
        pause_response = client.post(f"/sessions/{session_id}/pause")
        assert pause_response.status_code == 200
        assert pause_response.json()["status"] == "paused"
        
        # Retomar
        resume_response = client.post(f"/sessions/{session_id}/resume")
        assert resume_response.status_code == 200
        assert resume_response.json()["status"] == "active"
        
        # Encerrar
        end_response = client.post(f"/sessions/{session_id}/end")
        assert end_response.status_code == 200
        assert end_response.json()["status"] == "ended"
    
    def test_delete_session_endpoint(self, client, sample_session_data):
        """Testa endpoint DELETE /sessions/{id}."""
        # Criar sessão
        create_response = client.post("/sessions", json=sample_session_data)
        session_id = create_response.json()["id"]
        
        # Deletar
        delete_response = client.delete(f"/sessions/{session_id}")
        assert delete_response.status_code == 204
        
        # Verificar que não existe mais
        get_response = client.get(f"/sessions/{session_id}")
        assert get_response.status_code == 404
    
    def test_session_filters(self, client):
        """Testa filtros na listagem de sessões."""
        # Criar sessões com diferentes status e tags
        sessions_data = [
            {"name": "Sessão GPU", "tags": ["gpu", "teste"]},
            {"name": "Sessão CPU", "tags": ["cpu", "teste"]},
            {"name": "Sessão Prod", "tags": ["producao"]}
        ]
        
        session_ids = []
        for data in sessions_data:
            response = client.post("/sessions", json=data)
            session_ids.append(response.json()["id"])
        
        # Iniciar uma sessão
        client.post(f"/sessions/{session_ids[0]}/start")
        
        # Filtrar por status
        response = client.get("/sessions?status=active")
        assert response.status_code == 200
        active_sessions = response.json()
        assert len(active_sessions) == 1
        assert active_sessions[0]["status"] == "active"
        
        # Filtrar por tag
        response = client.get("/sessions?tag=teste")
        assert response.status_code == 200
        test_sessions = response.json()
        assert len(test_sessions) == 2
        
        # Busca textual
        response = client.get("/sessions?q=GPU")
        assert response.status_code == 200
        gpu_sessions = response.json()
        assert len(gpu_sessions) == 1
        assert "GPU" in gpu_sessions[0]["name"]
