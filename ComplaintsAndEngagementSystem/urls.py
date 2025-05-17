"""
URL configuration for ComplaintsAndEngagementSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
import debug_toolbar
from ComplaintsAndEngagementSystem import settings
from ComplaintsAndEngagementSystem.settings import MEDIA_ROOT, MEDIA_URL

admin.site.site_header = "PropApp"
admin.site.index_title = "Admin dashboard"
urlpatterns = [
    path('admin/', admin.site.urls, name="admin"),
    path('', include('compliants.urls')),
    path('__debug__', include(debug_toolbar.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=MEDIA_ROOT)
