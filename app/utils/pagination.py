from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Query
from sqlalchemy import func
from math import ceil

class PaginationResult:
    """Clase para encapsular resultados de paginación"""
    
    def __init__(
        self,
        items: List[Any],
        page: int,
        per_page: int,
        total: int,
        has_prev: bool = False,
        has_next: bool = False,
        prev_num: Optional[int] = None,
        next_num: Optional[int] = None
    ):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = ceil(total / per_page) if per_page > 0 else 0
        self.has_prev = has_prev
        self.has_next = has_next
        self.prev_num = prev_num
        self.next_num = next_num
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario para templates"""
        return {
            'items': self.items,
            'page': self.page,
            'per_page': self.per_page,
            'total': self.total,
            'pages': self.pages,
            'has_prev': self.has_prev,
            'has_next': self.has_next,
            'prev_num': self.prev_num,
            'next_num': self.next_num
        }

def paginate_query(
    query: Query,
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> PaginationResult:
    """Pagina una consulta SQLAlchemy
    
    Args:
        query: Consulta SQLAlchemy
        page: Número de página (empezando en 1)
        per_page: Elementos por página
        max_per_page: Máximo elementos por página permitidos
    
    Returns:
        PaginationResult con los datos paginados
    """
    # Validar parámetros
    page = max(1, page)
    per_page = min(max(1, per_page), max_per_page)
    
    # Obtener total de elementos
    total = query.count()
    
    # Calcular offset
    offset = (page - 1) * per_page
    
    # Obtener elementos de la página actual
    items = query.offset(offset).limit(per_page).all()
    
    # Calcular información de navegación
    has_prev = page > 1
    has_next = offset + per_page < total
    prev_num = page - 1 if has_prev else None
    next_num = page + 1 if has_next else None
    
    return PaginationResult(
        items=items,
        page=page,
        per_page=per_page,
        total=total,
        has_prev=has_prev,
        has_next=has_next,
        prev_num=prev_num,
        next_num=next_num
    )

def get_pagination_params(
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    default_per_page: int = 20,
    max_per_page: int = 100
) -> tuple[int, int]:
    """Obtiene y valida parámetros de paginación
    
    Args:
        page: Número de página solicitado
        per_page: Elementos por página solicitados
        default_per_page: Valor por defecto para per_page
        max_per_page: Máximo permitido para per_page
    
    Returns:
        Tupla (page, per_page) validada
    """
    # Validar página
    if page is None or page < 1:
        page = 1
    
    # Validar elementos por página
    if per_page is None:
        per_page = default_per_page
    else:
        per_page = min(max(1, per_page), max_per_page)
    
    return page, per_page

def create_pagination_context(
    pagination: PaginationResult,
    base_url: str,
    **query_params
) -> Dict[str, Any]:
    """Crea contexto para templates con información de paginación
    
    Args:
        pagination: Resultado de paginación
        base_url: URL base para los enlaces
        **query_params: Parámetros adicionales para mantener en URLs
    
    Returns:
        Diccionario con contexto para templates
    """
    # Construir parámetros de query string
    def build_url(page_num: int) -> str:
        params = {**query_params, 'page': page_num, 'per_page': pagination.per_page}
        query_string = '&'.join([f"{k}={v}" for k, v in params.items() if v is not None])
        return f"{base_url}?{query_string}" if query_string else base_url
    
    # Calcular rango de páginas para mostrar
    start_page = max(1, pagination.page - 2)
    end_page = min(pagination.pages, pagination.page + 2)
    
    # Ajustar rango si estamos cerca del inicio o final
    if end_page - start_page < 4:
        if start_page == 1:
            end_page = min(pagination.pages, start_page + 4)
        else:
            start_page = max(1, end_page - 4)
    
    page_range = list(range(start_page, end_page + 1))
    
    return {
        'pagination': pagination.to_dict(),
        'page_range': page_range,
        'first_url': build_url(1) if pagination.page > 1 else None,
        'prev_url': build_url(pagination.prev_num) if pagination.has_prev else None,
        'next_url': build_url(pagination.next_num) if pagination.has_next else None,
        'last_url': build_url(pagination.pages) if pagination.page < pagination.pages else None,
        'page_urls': {page: build_url(page) for page in page_range}
    }