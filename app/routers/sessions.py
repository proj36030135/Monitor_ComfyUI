"""Router para endpoints de sessões.

Implementa todos os endpoints relacionados ao gerenciamento
de sessões de observabilidade conforme especificado no DSD.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session as DBSession

from ..db import get_db
from ..schemas import (
    Session, SessionCreate, SessionUpdate, SessionQuery, SessionWithSummary,
    SuccessResponse, ErrorResponse, SessionStatus
)
from ..crud.sessions import SessionCRUD


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=Session, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: DBSession = Depends(get_db)
):
    """Cria uma nova sessão de observabilidade.
    
    A sessão é criada com status 'inactive' por padrão.
    Use POST /sessions/{id}/start para ativá-la.
    
    Args:
        session_data: Dados da sessão a ser criada
        db: Sessão do banco de dados
        
    Returns:
        Sessão criada
        
    Raises:
        400: Dados inválidos
        422: Erro de validação
    """
    try:
        db_session = SessionCRUD.create(db, session_data)
        
        # Carregar tags para resposta
        session_with_tags = SessionCRUD.get_by_id_with_tags(db, db_session.id)
        if session_with_tags:
            # Extrair nomes das tags
            tag_names = [st.tag.name for st in session_with_tags.session_tags]
            # Criar resposta com tags
            response_data = Session.model_validate(session_with_tags)
            response_data.tags = tag_names
            return response_data
        
        return Session.model_validate(db_session)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Erro interno do servidor"}
        )


@router.get("/", response_model=List[Session])
async def list_sessions(
    status_filter: Optional[SessionStatus] = Query(None, alias="status"),
    tag: Optional[str] = Query(None),
    profile_id: Optional[str] = Query(None),
    from_ms: Optional[int] = Query(None, alias="from"),
    to_ms: Optional[int] = Query(None, alias="to"),
    q: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: DBSession = Depends(get_db)
):
    """Lista sessões com filtros opcionais.
    
    Args:
        status_filter: Filtrar por status da sessão
        tag: Filtrar por nome de tag
        profile_id: Filtrar por ID do perfil
        from_ms: Timestamp inicial (epoch ms)
        to_ms: Timestamp final (epoch ms)
        q: Busca textual no nome/nota
        limit: Limite de resultados (1-500)
        offset: Offset para paginação
        db: Sessão do banco de dados
        
    Returns:
        Lista de sessões
    """
    try:
        query = SessionQuery(
            status=status_filter,
            tag=tag,
            profile_id=profile_id,
            from_ms=from_ms,
            to_ms=to_ms,
            q=q,
            limit=limit,
            offset=offset
        )
        
        sessions = SessionCRUD.list_sessions(db, query)
        
        # Carregar tags para cada sessão
        result = []
        for session in sessions:
            session_with_tags = SessionCRUD.get_by_id_with_tags(db, session.id)
            if session_with_tags:
                tag_names = [st.tag.name for st in session_with_tags.session_tags]
                response_data = Session.model_validate(session_with_tags)
                response_data.tags = tag_names
                result.append(response_data)
            else:
                result.append(Session.model_validate(session))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Erro interno do servidor"}
        )


@router.get("/{session_id}", response_model=SessionWithSummary)
async def get_session(
    session_id: str,
    db: DBSession = Depends(get_db)
):
    """Obtém detalhes de uma sessão específica.
    
    Inclui resumo de métricas (duração, número de runs, estatísticas).
    
    Args:
        session_id: ID da sessão
        db: Sessão do banco de dados
        
    Returns:
        Sessão com resumo de métricas
        
    Raises:
        404: Sessão não encontrada
    """
    try:
        # Buscar sessão com tags
        session = SessionCRUD.get_by_id_with_tags(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "session_not_found", "message": f"Sessão {session_id} não encontrada"}
            )
        
        # Gerar resumo
        summary = SessionCRUD.get_session_summary(db, session_id)
        
        # Extrair tags
        tag_names = [st.tag.name for st in session.session_tags]
        
        # Criar resposta
        response_data = SessionWithSummary.model_validate(session)
        response_data.tags = tag_names
        response_data.summary = summary
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Erro interno do servidor"}
        )


@router.patch("/{session_id}", response_model=Session)
async def update_session(
    session_id: str,
    session_data: SessionUpdate,
    db: DBSession = Depends(get_db)
):
    """Atualiza uma sessão existente.
    
    Permite atualizar nome, nota e tags da sessão.
    
    Args:
        session_id: ID da sessão
        session_data: Dados para atualização
        db: Sessão do banco de dados
        
    Returns:
        Sessão atualizada
        
    Raises:
        404: Sessão não encontrada
        400: Dados inválidos
    """
    try:
        updated_session = SessionCRUD.update(db, session_id, session_data)
        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "session_not_found", "message": f"Sessão {session_id} não encontrada"}
            )
        
        # Carregar tags para resposta
        session_with_tags = SessionCRUD.get_by_id_with_tags(db, session_id)
        if session_with_tags:
            tag_names = [st.tag.name for st in session_with_tags.session_tags]
            response_data = Session.model_validate(session_with_tags)
            response_data.tags = tag_names
            return response_data
        
        return Session.model_validate(updated_session)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Erro interno do servidor"}
        )


@router.post("/{session_id}/start", response_model=Session)
async def start_session(
    session_id: str,
    db: DBSession = Depends(get_db)
):
    """Inicia uma sessão (torna ativa).
    
    Implementa a regra de negócio de apenas uma sessão ativa:
    - Encerra qualquer sessão ativa atual
    - Ativa a sessão especificada
    
    Args:
        session_id: ID da sessão a ser iniciada
        db: Sessão do banco de dados
        
    Returns:
        Sessão iniciada
        
    Raises:
        404: Sessão não encontrada
        409: Conflito de estado
    """
    try:
        started_session = SessionCRUD.start_session(db, session_id)
        if not started_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "session_not_found", "message": f"Sessão {session_id} não encontrada"}
            )
        
        # Carregar tags para resposta
        session_with_tags = SessionCRUD.get_by_id_with_tags(db, session_id)
        if session_with_tags:
            tag_names = [st.tag.name for st in session_with_tags.session_tags]
            response_data = Session.model_validate(session_with_tags)
            response_data.tags = tag_names
            return response_data
        
        return Session.model_validate(started_session)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "session_conflict", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Erro interno do servidor"}
        )


@router.post("/{session_id}/pause", response_model=Session)
async def pause_session(
    session_id: str,
    db: DBSession = Depends(get_db)
):
    """Pausa uma sessão ativa.
    
    Args:
        session_id: ID da sessão a ser pausada
        db: Sessão do banco de dados
        
    Returns:
        Sessão pausada
        
    Raises:
        404: Sessão não encontrada
        409: Sessão não está ativa
    """
    try:
        paused_session = SessionCRUD.pause_session(db, session_id)
        if not paused_session:
            # Verificar se sessão existe
            session = SessionCRUD.get_by_id(db, session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "session_not_found", "message": f"Sessão {session_id} não encontrada"}
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": "session_not_active", "message": "Sessão não está ativa"}
                )
        
        # Carregar tags para resposta
        session_with_tags = SessionCRUD.get_by_id_with_tags(db, session_id)
        if session_with_tags:
            tag_names = [st.tag.name for st in session_with_tags.session_tags]
            response_data = Session.model_validate(session_with_tags)
            response_data.tags = tag_names
            return response_data
        
        return Session.model_validate(paused_session)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Erro interno do servidor"}
        )


@router.post("/{session_id}/resume", response_model=Session)
async def resume_session(
    session_id: str,
    db: DBSession = Depends(get_db)
):
    """Retoma uma sessão pausada.
    
    Args:
        session_id: ID da sessão a ser retomada
        db: Sessão do banco de dados
        
    Returns:
        Sessão retomada
        
    Raises:
        404: Sessão não encontrada
        409: Sessão não está pausada
    """
    try:
        resumed_session = SessionCRUD.resume_session(db, session_id)
        if not resumed_session:
            # Verificar se sessão existe
            session = SessionCRUD.get_by_id(db, session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "session_not_found", "message": f"Sessão {session_id} não encontrada"}
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": "session_not_paused", "message": "Sessão não está pausada"}
                )
        
        # Carregar tags para resposta
        session_with_tags = SessionCRUD.get_by_id_with_tags(db, session_id)
        if session_with_tags:
            tag_names = [st.tag.name for st in session_with_tags.session_tags]
            response_data = Session.model_validate(session_with_tags)
            response_data.tags = tag_names
            return response_data
        
        return Session.model_validate(resumed_session)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Erro interno do servidor"}
        )


@router.post("/{session_id}/end", response_model=Session)
async def end_session(
    session_id: str,
    db: DBSession = Depends(get_db)
):
    """Encerra uma sessão.
    
    Args:
        session_id: ID da sessão a ser encerrada
        db: Sessão do banco de dados
        
    Returns:
        Sessão encerrada
        
    Raises:
        404: Sessão não encontrada
    """
    try:
        ended_session = SessionCRUD.end_session(db, session_id)
        if not ended_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "session_not_found", "message": f"Sessão {session_id} não encontrada"}
            )
        
        # Carregar tags para resposta
        session_with_tags = SessionCRUD.get_by_id_with_tags(db, session_id)
        if session_with_tags:
            tag_names = [st.tag.name for st in session_with_tags.session_tags]
            response_data = Session.model_validate(session_with_tags)
            response_data.tags = tag_names
            return response_data
        
        return Session.model_validate(ended_session)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Erro interno do servidor"}
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: DBSession = Depends(get_db)
):
    """Remove uma sessão e todos os dados relacionados.
    
    ATENÇÃO: Esta operação é irreversível e remove:
    - A sessão
    - Todos os runs da sessão
    - Todas as amostras da sessão
    - Todos os eventos da sessão
    - Associações com tags
    
    Args:
        session_id: ID da sessão a ser removida
        db: Sessão do banco de dados
        
    Raises:
        404: Sessão não encontrada
    """
    try:
        deleted = SessionCRUD.delete(db, session_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "session_not_found", "message": f"Sessão {session_id} não encontrada"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Erro interno do servidor"}
        )
