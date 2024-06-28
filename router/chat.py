from fastapi import APIRouter

router = APIRouter(prefix= '/chat')

@router.get('/completions')
def chat():
    return 'chat'
    