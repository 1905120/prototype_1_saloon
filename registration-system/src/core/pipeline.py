"""
DataPipeline class - main orchestrator
Load → Validate → Process → Persist
"""
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from src.common.enums import OperationType, PipelineStatus
from src.core.session import SessionManager
from src.core.universal_cache import UniversalCache
from src.errors.error_handler import ErrorHandler


class DataPipeline:
    """
    Main pipeline orchestrator
    Handles: Load → Validate → Process → Persist
    """
    
    def __init__(self, session_cache):
        """
        Initialize pipeline
        
        Args:
            universal_cache: UniversalCache instance
        """
        self.session_cache = session_cache
    
    # ============ PHASE 1: LOAD ============
    def load(self) -> Dict[str, Any]:
        
        pass
        return 
    
    # ============ PHASE 2: VALIDATE ============
    def validate(self) -> Dict[str, Any]:
        
        pass
        
        return
    
    # ============ PHASE 4: PROCESS ============
    def process(self):
        pass
        return
    
    # ============ PHASE 5: PERSIST ============
    def persist(self, session_id: str, persist_func: Callable) -> Dict[str, Any]:
        """
        Persist phase: Write data to storage
        
        Args:
            session_id: Session identifier
            persist_func: Function to persist data
        
        Returns:
            Updated session
        """
        session = self.session_manager.get_session(session_id)
        
        try:
            result = persist_func(session.get("data"))
            self.session_manager.set_session_status(session_id, PipelineStatus.PERSISTED)
            
            if "phases" not in session:
                session["phases"] = {}
            
            session["phases"]["persist"] = {
                "status": PipelineStatus.PERSISTED.value,
                "timestamp": datetime.now().isoformat(),
                "result": result
            }
            
        except Exception as e:
            self.session_manager.update_session(session_id, {
                "error": str(e),
                "status": PipelineStatus.FAILED.value
            })
            ErrorHandler.raise_processing_error(f"Persistence failed: {str(e)}")
        
        return session
    
    # ============ TEMPLATE FLOW ============
    async def template_flow(self, function) -> Dict[str, Any]:
        """
        Template flow: Execute pipeline phases in sequence
        Calls: load → validate → process → persist
        
        Args:
            session_id: Session identifier
            validator_func: Validation function
            processor_func: Processing function
            persist_func: Persistence function
            api_func: Optional API call function
            post_action_funcs: Optional post-action functions
        
        Returns:
            Final session with all phases completed
        """
        try:
            # Phase 1: Load
            session = self.load()
            
            # Phase 2: Validate
            session = self.validate()
            
            response = await function(self.session_cache)
            
            # Phase 4: Persist
            # if persist_func:
            #     session = self.persist()
            
            return response
            
        except Exception as e:
            raise
    
    def _update_final_metadata(self, session: Dict[str, Any]) -> None:
        """
        Update metadata at end of process with lock
        
        Args:
            session: Final session object
        """
        phone = session.get("phone")
        version = session.get("version")
        session_id = session.get("session_id")
        
        if phone and version and session_id:
            self.cache.acquire_write_lock()
            try:
                metadata = self.cache.read(phone)
                if metadata:
                    metadata["latest_version"] = version
                    self.cache.update(phone, metadata)
            finally:
                self.cache.release_write_lock()
