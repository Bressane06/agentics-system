class DominioError(Exception):
    """Base dos erros de regra de negócio."""

class NaoEncontradoError(DominioError):
    pass

class ConflitoError(DominioError):
    pass

class RegraDeNegocioError(DominioError):
    pass