

class AppError(Exception):
   
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)

    

class AuthError(AppError):
    
    def __init__(self, detail: str = "Требуется авторизация", status_code: int = 401):
        super().__init__(detail, status_code)