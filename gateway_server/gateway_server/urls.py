"""gateway_server URL Configuration

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
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from rest_framework.urlpatterns import format_suffix_patterns
from server import views
from rest_framework_swagger.views import get_swagger_view
from rest_framework_jwt.views import refresh_jwt_token, obtain_jwt_token

schema_view = get_swagger_view(title='REST API')

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/login/$', auth_views.login, {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^token/$', obtain_jwt_token, name='get_auth_token'),
    url(r'^refresh-token/$', refresh_jwt_token, name='refresh_token'),
    url(r'^projects/$', views.ProjectList.as_view()),
    url(r'^projects/(?P<p_name>[A-Za-z0-9_.-]{1,50})/connectors/$', views.Connectors.as_view()),
    url(r'^projects/(?P<p_name>[A-Za-z0-9_.-]{1,50})/connectors/(?P<conn_name>[A-Za-z0-9_.]{1,20})/$',
        views.ConnectorList.as_view()),
    # url(r'^projects/(?P<p_name>[A-Za-z_\.]{1,20})/connector/$', views.ConnectorList.as_view()),
    url(r'^projects/(?P<p_name>[A-Za-z0-9_.-]{1,50})/$', views.ProjectDetails.as_view()),
    # url(r'^projects/(?P<p_name>[A-Za-z0-9_.-]{1,50})/(?P<attribute>[A-Za-z0-9_.]{1,20})/$',
    #     views.ProjectStatus.as_view()),
    url(r'^projects/(?P<p_name>[A-Za-z0-9_.-]{1,50})/connector/(?P<conn_name>[A-Za-z0-9_.]{1,20})/(?P<attribute>[A-Za-z0-9_.]{1,20})/$',
        views.ConnectorDetails.as_view()),
    url(r'^projects/(?P<p_name>[A-Za-z0-9_.-]{1,50})/connector/(?P<conn_name>[A-Za-z0-9_.]{1,20})/$',
        views.ConnectorEdit.as_view()),
    url(r'^simulations/$', views.Simulate.as_view()),
    url(r'^simulations/(?P<s_id>[A-Za-z0-9_.-]{1,50})/$', views.SimulationDetail.as_view()),
    url(r'^upload_project/(?P<p_name>[A-Za-z0-9_.-]{1,50})/$', views.UploadProject.as_view()),
    url(r'^machines/$', views.Machines.as_view()),
    url(r'^machines/(?P<m_name>[A-Za-z0-9_.-]{1,50})/$', views.MachineDetails.as_view()),
    url(r'^docs/$', schema_view),
]

urlpatterns = format_suffix_patterns(urlpatterns)
