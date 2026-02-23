from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
import os

# ============================
# HTML SERVING (FRONTEND)
# ============================

def home(request):
    """
    Serve index.html as homepage
    """
    # 🔥 FIX: Added 'https://itrik-e-commerce-frontend.vercel.app' to the path
    index_path = os.path.join(str(settings.BASE_DIR.parent), "https://itrik-e-commerce-frontend.vercel.app", "index.html")

    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HttpResponse(f.read(), content_type="text/html")

    return JsonResponse({
        "message": "ITRIK API",
        "version": "1.0.0"
    })


def serve_html_file(request, filename):
    # 🔥 FIX: Added 'https://itrik-e-commerce-frontend.vercel.app' to the path
    file_path = os.path.join(str(settings.BASE_DIR.parent), "https://itrik-e-commerce-frontend.vercel.app", f"{filename}.html")

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return HttpResponse(f.read(), content_type="text/html")

    return JsonResponse({"error": "Page not found"}, status=404)


# ============================
# URLS
# ============================

urlpatterns = [

    # Frontend
    path("", home, name="home"),

    # Admin
    path("admin/", admin.site.urls),

    # Auth / OTP
    path("api/accounts/", include("accounts.urls")),

    # API Modules
    path("api/", include("store.urls")),
    path("api/cart/", include("cart.urls")),        
    path("api/orders/", include("orders.urls")),    
    path("api/", include("content.urls")),  
    
    # JWt
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Delivery Panel Route
    path("delivery_panel.html", serve_html_file, kwargs={"filename": "delivery_panel"}, name="delivery-panel-ui"),

    # HTML pages (KEEP AT END)
    path("<str:filename>.html", serve_html_file),
]

# ============================
# MEDIA & FRONTEND ASSETS (DEV)
# ============================

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # 🔥 FIX: Point to the images folder inside https://itrik-e-commerce-frontend.vercel.app
    images_dir = os.path.join(settings.BASE_DIR.parent, "https://itrik-e-commerce-frontend.vercel.app", "images")
    if os.path.exists(images_dir):
        urlpatterns += static("/images/", document_root=images_dir)
        
    # 🔥 FIX: Point to the static folder (JS/CSS) inside https://itrik-e-commerce-frontend.vercel.app
    frontend_static_dir = os.path.join(settings.BASE_DIR.parent, "https://itrik-e-commerce-frontend.vercel.app", "static")
    if os.path.exists(frontend_static_dir):
        urlpatterns += static("/static/", document_root=frontend_static_dir)