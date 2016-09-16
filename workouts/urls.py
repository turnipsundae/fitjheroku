from django.conf.urls import url

from . import views

app_name = 'workouts'
urlpatterns = [
  # e.g. /workouts
  url(r'^$', views.index, name='index'),
  # e.g. /workouts/base
  url(r'^base/$', views.base, name='base'),
  # e.g. workouts/trending
  url(r'^trending/$', views.trending, name='trending'),
  # e.g. workouts/user
  url(r'^user/$', views.user, name='user'),
  # e.g. /workouts/2
  url(r'^(?P<routine_id>[0-9]+)/$', views.detail, name='detail'),
  # e.g. /workouts/2/results
  url(r'^(?P<routine_id>[0-9]+)/results/$', views.results, name='results'),
  # e.g. /workouts/2/likes
  url(r'^(?P<routine_id>[0-9]+)/likes/$', views.like, name='like'),
  # e.g. /workouts/add/routine
  url(r'^add/routine/$', views.add_routine, name='add_routine'),
  # e.g. /workouts/add/user
  url(r'^add/user/$', views.add_user, name='add_user'),
  # e.g. /workouts/2/add/exercise
  url(r'^(?P<routine_id>[0-9]+)/add/exercise/$', views.add_exercise, name='add_exercise'),
  # e.g. /workouts/2/like
  url(r'^(?P<routine_id>[0-9]+)/like/$', views.like, name='like'),
  # e.g. /workouts/sort_by_likes
  url(r'^sort_by_likes/$', views.sort_by_likes, name='sort_by_likes'),

]
