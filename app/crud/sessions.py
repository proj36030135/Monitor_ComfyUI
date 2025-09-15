"""CRUD operations para sessões.

Implementa as operações de Create, Read, Update, Delete
para sessões, incluindo regras de negócio específicas.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session as DBSession, selectinload
from sqlalchemy import select, update, and_, or_, func, text
from sqlalchemy.exc import IntegrityError

from ..models import Session, SessionTag, Tag, Sample, Run, Event
from ..schemas import (
    SessionCreate, SessionUpdate, SessionQuery, SessionStatus,
    SessionSummary, SessionWithSummary
)


def current_timestamp_ms() -> int:
    """Retorna timestamp atual em milissegundos."""
    return int(datetime.now().timestamp() * 1000)


class SessionCRUD:
    """Operações CRUD para sessões."""
    
    @staticmethod
    def create(db: DBSession, session_data: SessionCreate) -> Session:
        """Cria uma nova sessão.
        
        Args:
            db: Sessão do banco de dados
            session_data: Dados da sessão a ser criada
            
        Returns:
            Sessão criada
        """
        current_ms = current_timestamp_ms()
        
        # Criar sessão
        db_session = Session(
            name=session_data.name,
            status=SessionStatus.INACTIVE,
            profile_id=session_data.profile_id,
            note=session_data.note,
            created_at_ms=current_ms,
            updated_at_ms=current_ms
        )
        
        db.add(db_session)
        db.flush()  # Para obter o ID
        
        # Adicionar tags se fornecidas
        if session_data.tags:
            SessionCRUD._add_tags_to_session(db, db_session.id, session_data.tags)
        
        db.commit()
        db.refresh(db_session)
        
        return db_session
    
    @staticmethod
    def get_by_id(db: DBSession, session_id: str) -> Optional[Session]:
        """Busca sessão por ID.
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão
            
        Returns:
            Sessão encontrada ou None
        """
        stmt = select(Session).where(Session.id == session_id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_by_id_with_tags(db: DBSession, session_id: str) -> Optional[Session]:
        """Busca sessão por ID incluindo tags.
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão
            
        Returns:
            Sessão encontrada ou None
        """
        stmt = (
            select(Session)
            .options(selectinload(Session.session_tags).selectinload(SessionTag.tag))
            .where(Session.id == session_id)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_active_session(db: DBSession) -> Optional[Session]:
        """Busca a sessão ativa atual.
        
        Args:
            db: Sessão do banco de dados
            
        Returns:
            Sessão ativa ou None
        """
        stmt = select(Session).where(Session.status == SessionStatus.ACTIVE)
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    def list_sessions(db: DBSession, query: SessionQuery) -> List[Session]:
        """Lista sessões com filtros.
        
        Args:
            db: Sessão do banco de dados
            query: Parâmetros de consulta
            
        Returns:
            Lista de sessões
        """
        stmt = select(Session)
        
        # Aplicar filtros
        conditions = []
        
        if query.status:
            conditions.append(Session.status == query.status)
        
        if query.profile_id:
            conditions.append(Session.profile_id == query.profile_id)
        
        if query.from_ms:
            conditions.append(Session.created_at_ms >= query.from_ms)
        
        if query.to_ms:
            conditions.append(Session.created_at_ms <= query.to_ms)
        
        if query.q:
            # Busca textual no nome e nota
            search_term = f"%{query.q}%"
            conditions.append(
                or_(
                    Session.name.ilike(search_term),
                    Session.note.ilike(search_term)
                )
            )
        
        if query.tag:
            # Filtrar por tag
            stmt = stmt.join(SessionTag).join(Tag).where(Tag.name == query.tag)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Ordenação e paginação
        stmt = (
            stmt
            .order_by(Session.created_at_ms.desc())
            .offset(query.offset)
            .limit(query.limit)
        )
        
        result = db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    def update(db: DBSession, session_id: str, session_data: SessionUpdate) -> Optional[Session]:
        """Atualiza uma sessão.
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão
            session_data: Dados para atualização
            
        Returns:
            Sessão atualizada ou None se não encontrada
        """
        # Verificar se sessão existe
        db_session = SessionCRUD.get_by_id(db, session_id)
        if not db_session:
            return None
        
        # Atualizar campos
        update_data = {}
        if session_data.name is not None:
            update_data["name"] = session_data.name
        if session_data.note is not None:
            update_data["note"] = session_data.note
        
        if update_data:
            # Garantir que o timestamp seja diferente
            import time
            time.sleep(0.001)  # 1ms delay para garantir timestamp diferente
            update_data["updated_at_ms"] = current_timestamp_ms()
            
            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .values(**update_data)
            )
            db.execute(stmt)
        
        # Atualizar tags se fornecidas
        if session_data.tags is not None:
            SessionCRUD._update_session_tags(db, session_id, session_data.tags)
        
        db.commit()
        return SessionCRUD.get_by_id(db, session_id)
    
    @staticmethod
    def start_session(db: DBSession, session_id: str) -> Optional[Session]:
        """Inicia uma sessão (torna ativa).
        
        Implementa a regra de negócio de apenas uma sessão ativa:
        - Encerra qualquer sessão ativa atual
        - Ativa a sessão especificada
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão a ser iniciada
            
        Returns:
            Sessão iniciada ou None se não encontrada
        """
        # Verificar se sessão existe
        target_session = SessionCRUD.get_by_id(db, session_id)
        if not target_session:
            return None
        
        # Verificar se já está ativa
        if target_session.status == SessionStatus.ACTIVE:
            return target_session
        
        current_ms = current_timestamp_ms()
        
        try:
            # 1. Encerrar qualquer sessão ativa atual
            active_session = SessionCRUD.get_active_session(db)
            if active_session and active_session.id != session_id:
                stmt_end_active = (
                    update(Session)
                    .where(Session.id == active_session.id)
                    .values(
                        status=SessionStatus.ENDED,
                        ended_at_ms=current_ms,
                        updated_at_ms=current_ms
                    )
                )
                db.execute(stmt_end_active)
            
            # 2. Ativar a sessão alvo
            stmt_start = (
                update(Session)
                .where(Session.id == session_id)
                .values(
                    status=SessionStatus.ACTIVE,
                    started_at_ms=current_ms,
                    ended_at_ms=None,
                    updated_at_ms=current_ms
                )
            )
            db.execute(stmt_start)
            
            db.commit()
            return SessionCRUD.get_by_id(db, session_id)
            
        except IntegrityError as e:
            db.rollback()
            # Pode ocorrer se duas sessões tentarem ficar ativas simultaneamente
            raise ValueError(f"Erro ao ativar sessão: {e}")
    
    @staticmethod
    def pause_session(db: DBSession, session_id: str) -> Optional[Session]:
        """Pausa uma sessão ativa.
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão a ser pausada
            
        Returns:
            Sessão pausada ou None se não encontrada/não ativa
        """
        session = SessionCRUD.get_by_id(db, session_id)
        if not session or session.status != SessionStatus.ACTIVE:
            return None
        
        current_ms = current_timestamp_ms()
        
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(
                status=SessionStatus.PAUSED,
                updated_at_ms=current_ms
            )
        )
        db.execute(stmt)
        db.commit()
        
        return SessionCRUD.get_by_id(db, session_id)
    
    @staticmethod
    def resume_session(db: DBSession, session_id: str) -> Optional[Session]:
        """Retoma uma sessão pausada.
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão a ser retomada
            
        Returns:
            Sessão retomada ou None se não encontrada/não pausada
        """
        session = SessionCRUD.get_by_id(db, session_id)
        if not session or session.status != SessionStatus.PAUSED:
            return None
        
        # Usar a mesma lógica do start para garantir apenas uma ativa
        return SessionCRUD.start_session(db, session_id)
    
    @staticmethod
    def end_session(db: DBSession, session_id: str) -> Optional[Session]:
        """Encerra uma sessão.
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão a ser encerrada
            
        Returns:
            Sessão encerrada ou None se não encontrada
        """
        session = SessionCRUD.get_by_id(db, session_id)
        if not session or session.status == SessionStatus.ENDED:
            return session
        
        current_ms = current_timestamp_ms()
        
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(
                status=SessionStatus.ENDED,
                ended_at_ms=current_ms,
                updated_at_ms=current_ms
            )
        )
        db.execute(stmt)
        db.commit()
        
        return SessionCRUD.get_by_id(db, session_id)
    
    @staticmethod
    def get_session_summary(db: DBSession, session_id: str) -> Optional[SessionSummary]:
        """Gera resumo de métricas de uma sessão.
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão
            
        Returns:
            Resumo da sessão ou None se não encontrada
        """
        session = SessionCRUD.get_by_id(db, session_id)
        if not session:
            return None
        
        # Contar amostras
        stmt_samples = select(func.count(Sample.id)).where(Sample.session_id == session_id)
        total_samples = db.execute(stmt_samples).scalar() or 0
        
        # Contar runs
        stmt_runs = select(func.count(Run.id)).where(Run.session_id == session_id)
        total_runs = db.execute(stmt_runs).scalar() or 0
        
        # Calcular duração
        duration_ms = None
        if session.started_at_ms and session.ended_at_ms:
            duration_ms = session.ended_at_ms - session.started_at_ms
        elif session.started_at_ms and session.status == SessionStatus.ACTIVE:
            duration_ms = current_timestamp_ms() - session.started_at_ms
        
        # Estatísticas por grupo de métrica
        metric_groups = {}
        
        # Query para estatísticas por grupo
        stmt_stats = (
            select(
                Sample.metric_group,
                func.count(Sample.id).label('count'),
                func.avg(Sample.value).label('avg_value'),
                func.min(Sample.value).label('min_value'),
                func.max(Sample.value).label('max_value')
            )
            .where(Sample.session_id == session_id)
            .group_by(Sample.metric_group)
        )
        
        stats_result = db.execute(stmt_stats)
        for row in stats_result:
            metric_groups[row.metric_group] = {
                'count': row.count,
                'avg_value': round(float(row.avg_value), 2) if row.avg_value else 0,
                'min_value': float(row.min_value) if row.min_value else 0,
                'max_value': float(row.max_value) if row.max_value else 0,
            }
        
        return SessionSummary(
            total_samples=total_samples,
            total_runs=total_runs,
            duration_ms=duration_ms,
            metric_groups=metric_groups
        )
    
    @staticmethod
    def delete(db: DBSession, session_id: str) -> bool:
        """Remove uma sessão e todos os dados relacionados.
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão a ser removida
            
        Returns:
            True se removida, False se não encontrada
        """
        session = SessionCRUD.get_by_id(db, session_id)
        if not session:
            return False
        
        # O cascade delete cuidará dos relacionamentos
        db.delete(session)
        db.commit()
        
        return True
    
    @staticmethod
    def _add_tags_to_session(db: DBSession, session_id: str, tag_names: List[str]) -> None:
        """Adiciona tags a uma sessão.
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão
            tag_names: Lista de nomes de tags
        """
        if not tag_names:
            return
        
        current_ms = current_timestamp_ms()
        
        for tag_name in tag_names:
            # Buscar ou criar tag
            tag = db.execute(select(Tag).where(Tag.name == tag_name)).scalar_one_or_none()
            if not tag:
                tag = Tag(name=tag_name, created_at_ms=current_ms)
                db.add(tag)
                db.flush()
            
            # Verificar se associação já existe
            existing = db.execute(
                select(SessionTag).where(
                    and_(SessionTag.session_id == session_id, SessionTag.tag_id == tag.id)
                )
            ).scalar_one_or_none()
            
            if not existing:
                session_tag = SessionTag(
                    session_id=session_id,
                    tag_id=tag.id,
                    created_at_ms=current_ms
                )
                db.add(session_tag)
    
    @staticmethod
    def _update_session_tags(db: DBSession, session_id: str, tag_names: List[str]) -> None:
        """Atualiza as tags de uma sessão (substitui todas).
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão
            tag_names: Lista de nomes de tags
        """
        # Remover todas as tags atuais
        db.execute(
            text("DELETE FROM session_tags WHERE session_id = :session_id"),
            {"session_id": session_id}
        )
        
        # Adicionar novas tags
        SessionCRUD._add_tags_to_session(db, session_id, tag_names)
