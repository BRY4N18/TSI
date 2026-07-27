"""Small domain exception vocabulary for the commercial pipeline."""
class ValidationError(Exception): pass
class ConflictError(Exception): pass
class ForbiddenError(Exception): pass
class NotFoundError(Exception): pass
class UnauthorizedError(Exception): pass
