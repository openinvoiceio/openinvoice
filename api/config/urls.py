"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path, re_path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from common.views import ConfigAPIView

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("health/", include("health_check.urls")),
    path("api/", include("allauth.headless.urls")),
    path("api/v1/config", ConfigAPIView.as_view()),
    path("api/v1/", include("apps.stripe.urls")),
    path("api/v1/", include("apps.search.urls")),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.analytics.urls")),
    path("api/v1/", include("apps.coupons.urls")),
    path("api/v1/", include("apps.customers.urls")),
    path("api/v1/", include("apps.files.urls")),
    path("api/v1/", include("apps.invoices.urls")),
    path("api/v1/", include("apps.quotes.urls")),
    path("api/v1/", include("apps.credit_notes.urls")),
    path("api/v1/", include("apps.numbering_systems.urls")),
    path("api/v1/", include("apps.payments.urls")),
    path("api/v1/", include("apps.integrations.urls")),
    path("api/v1/", include("apps.portal.urls")),
    path("api/v1/", include("apps.prices.urls")),
    path("api/v1/", include("apps.products.urls")),
    path("api/v1/", include("apps.tax_rates.urls")),
    path("api/v1/", include("apps.shipping_rates.urls")),
    path("api/v1/", include("apps.users.urls")),
    re_path(
        r"^(?!api/|admin/|health/|accounts/|static/|media/|silk/).*$",
        TemplateView.as_view(template_name="index.html"),
    ),
]

if settings.DEBUG:
    urlpatterns += [
        path("api/v1/schema/", SpectacularAPIView.as_view()),
        path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
        path("silk/", include("silk.urls", namespace="silk")),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
