from fastapi import APIRouter


# initialize the app router 
router = APIRouter()

# define the home route 
@router.get('/')
async def Home():
    return "Home route"