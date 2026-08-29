from ninja import NinjaAPI
from materials.api import router as materials_router
from courses.api import router as courses_router
from main.api import router as main_router

api = NinjaAPI(
    title="Jamig Mosque API",
    description="API для SPA духовно-просветительского портала мечети",
    version="1.0.0",
    docs_url="/docs/",
)

api.add_router("/materials/", materials_router)
api.add_router("/courses/", courses_router)
api.add_router("/main/", main_router)
