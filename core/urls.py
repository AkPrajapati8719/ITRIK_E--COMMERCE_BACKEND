import os
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView

# ============================
# HTML SERVING (LOCAL DEV ONLY)
# ============================

def home(request):
    """
    Serve index.html locally, or JSON info online.
    """
    if settings.DEBUG:
        index_path = os.path.join(str(settings.BASE_DIR.parent), "frontend_Itrik_code", "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HttpResponse(f.read(), content_type="text/html")
    
    # Online response (Render)
    return JsonResponse({
        "message": "ITRIK E-Commerce API is Online",
        "status": "Healthy",
        "frontend": "https://itrik-e-commerce-frontend.vercel.app"
    })

def serve_html_file(request, filename):
    """
    Serve specific HTML files locally only.
    """
    if settings.DEBUG:
        file_path = os.path.join(str(settings.BASE_DIR.parent), "frontend_Itrik_code", f"{filename}.html")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return HttpResponse(f.read(), content_type="text/html")
    
    return JsonResponse({"error": "API Mode: Use the Vercel frontend to access pages."}, status=404)


# ============================
# URL ROUTES
# ============================

urlpatterns = [
    # 🏠 API Landing / Local Homepage
    path("", home, name="home"),

    # 🔐 Admin Panel
    path("admin/", admin.site.urls),

    # 🔑 Auth & JWT
    path("api/accounts/", include("accounts.urls")),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # 📦 API Modules (E-commerce Logic)
    path("api/", include("store.urls")),
    path("api/cart/", include("cart.urls")),        
    path("api/orders/", include("orders.urls")),    
    path("api/", include("content.urls")),  
]

# ============================
# STATIC & MEDIA HANDLING
# ============================

# 🖼️ Media Files (Always served so product images work online)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 🛠️ Static Files (Always served so Django Admin looks correct)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


# 🖥️ Local Frontend Assets (Only when DEBUG is True)
if settings.DEBUG:
    # Serve images folder from frontend directory
    images_dir = os.path.join(settings.BASE_DIR.parent, "frontend_Itrik_code", "images")
    if os.path.exists(images_dir):
        urlpatterns += static("/images/", document_root=images_dir)
        
    # Serve static folder from frontend directory
    frontend_static_dir = os.path.join(settings.BASE_DIR.parent, "frontend_Itrik_code", "static")
    if os.path.exists(frontend_static_dir):
        urlpatterns += static("/static/", document_root=frontend_static_dir)

    # 📄 Catch-all for HTML files (must be at the bottom)
    urlpatterns += [
        path("delivery_panel.html", serve_html_file, kwargs={"filename": "delivery_panel"}),
        path("<str:filename>.html", serve_html_file),
    ]





# from django.contrib import admin
# from django.urls import path, include
# from django.http import JsonResponse, HttpResponse
# from django.conf import settings
# from django.conf.urls.static import static
# from rest_framework_simplejwt.views import TokenRefreshView
# import os

# # ============================
# # HTML SERVING (FRONTEND)
# # ============================

# def home(request):
#     """
#     Serve index.html as homepage
#     """
#     # 🔥 FIX: Use the local folder name instead of the Vercel URL. 
#     # os.path cannot read "https://", it can only read local folders.
#     index_path = os.path.join(str(settings.BASE_DIR.parent), "frontend_Itrik_code", "index.html")

#     if os.path.exists(index_path):
#         with open(index_path, "r", encoding="utf-8") as f:
#             return HttpResponse(f.read(), content_type="text/html")

#     return JsonResponse({
#         "message": "ITRIK API",
#         "version": "1.0.0"
#     })


# def serve_html_file(request, filename):
#     # 🔥 FIX: Changed back to "frontend_Itrik_code"
#     file_path = os.path.join(str(settings.BASE_DIR.parent), "frontend_Itrik_code", f"{filename}.html")

#     if os.path.exists(file_path):
#         with open(file_path, "r", encoding="utf-8") as f:
#             return HttpResponse(f.read(), content_type="text/html")

#     return JsonResponse({"error": "Page not found"}, status=404)


# # ============================
# # URLS
# # ============================

# urlpatterns = [

#     # Frontend
#     path("", home, name="home"),

#     # Admin
#     path("admin/", admin.site.urls),

#     # Auth / OTP
#     path("api/accounts/", include("accounts.urls")),

#     # API Modules
#     path("api/", include("store.urls")),
#     path("api/cart/", include("cart.urls")),        
#     path("api/orders/", include("orders.urls")),    
#     path("api/", include("content.urls")),  
    
#     # JWt
#     path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

#     # Delivery Panel Route
#     path("delivery_panel.html", serve_html_file, kwargs={"filename": "delivery_panel"}, name="delivery-panel-ui"),

#     # HTML pages (KEEP AT END)
#     path("<str:filename>.html", serve_html_file),
# ]


# # ============================
# # MEDIA & FRONTEND ASSETS (DEV)
# # ============================

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#     # 🔥 FIX: Changed back to "frontend_Itrik_code"
#     images_dir = os.path.join(settings.BASE_DIR.parent, "frontend_Itrik_code", "images")
#     if os.path.exists(images_dir):
#         urlpatterns += static("/images/", document_root=images_dir)
        
#     # 🔥 FIX: Changed back to "frontend_Itrik_code"
#     frontend_static_dir = os.path.join(settings.BASE_DIR.parent, "frontend_Itrik_code", "static")
#     if os.path.exists(frontend_static_dir):
#         urlpatterns += static("/static/", document_root=frontend_static_dir)