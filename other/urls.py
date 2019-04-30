"""zhuican URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import url, include
from django.contrib import admin
from django.template.response import SimpleTemplateResponse

from main import urls as main_urls
from main.views import get_index, login, chat
from analysis import urls as analysis_urls
from reviews import urls as reviews_urls
from new_reviews import urls as new_reviews_urls
from recommend import urls as recommend_urls

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', get_index),
    url(r'^login/', login),
    url(r'^api/main/', include(main_urls)),
    url(r'^main/', include(main_urls)),
    url(r'^api/analyse/', include(analysis_urls)),
    url(r'^analyse/', include(analysis_urls)),
    url(r'^reviews/', include(reviews_urls)),
    url(r'^new_reviews/', include(new_reviews_urls)),
    url(r'^recommend/', include(recommend_urls)),
    url(r'^chat/', chat),
]
