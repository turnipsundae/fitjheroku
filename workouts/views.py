from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User 
from django.contrib.auth.decorators import login_required

from .models import Routine, Comment, Journal
from .utils import valid_name, valid_username, valid_password, valid_email, valid_title, valid_content_input, valid_tag_list, valid_digit, get_page_num


# Create your views here.
# TODO create recommendations based on likes
# TODO create search functionality
# TODO convert index numbers to title of workouts
# TODO show other users' journals? Recently completed items.
def index(request):
  RESULTS_PER_PAGE = 10
  if request.method == 'GET':
    s = request.GET.get('start', 0)
    if valid_digit(s):
      s = int(s)
    # get the current page results
    routine_list = Routine.objects.order_by('-likes')[s:s+RESULTS_PER_PAGE]
    # get the current page number
    current_page = get_page_num(s)
    # initialize params
    params = {'list': routine_list, 'current_page': current_page}
    # check if next results and get next page number
    results_remaining = Routine.objects.count() - RESULTS_PER_PAGE - s
    if results_remaining > 0:
      next_start = s + RESULTS_PER_PAGE
      params['next_start'] = next_start
      params['next_page'] = get_page_num(next_start)
    # check if prev results and get prev page number
    prev_start = s - RESULTS_PER_PAGE
    if prev_start >= 0:
      params['prev_start'] = prev_start
      params['prev_page'] = max(get_page_num(prev_start), 1)
    return render(request, 'workouts/index.html', params)

def login(request):
  if request.method == "POST":
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
      auth_login(request, user)
      return HttpResponseRedirect(reverse("workouts:index"))
    else:
      # return an 'invalid login' error message
      return render(request, "workouts/login.html", {
        "error_message" : "Username and password did not match",
        "username" : username,
        })
  else:
    return render(request, 'workouts/login.html')

def logout(request):
  auth_logout(request)
  return render(request, "workouts/logout.html")

def profile(request):
  if not request.user.is_authenticated:
    return HttpResponseRedirect(reverse('workouts:login'))
  else:
    return render(request, "workouts/profile.html") 

def sign_up(request):
  if request.method == "POST":
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    username = request.POST['username']
    email = request.POST['email']
    password = request.POST['password']
    error_exists = False
    params = dict(first_name=first_name, last_name=last_name, email=email)

    if not valid_name(first_name) or not valid_name(last_name):
      error_exists = True
      params['error_name'] = "Enter a first and last name using only letters, apostrophes and hyphens"
    if not valid_username(username):
      error_exists = True
      params['error_username'] = "Enter a username using only letters, numbers, underscore and hyphens"
    if not valid_email(email):
      error_exists = True
      params['error_email'] = "Please enter in the format example@domain.com"
    if not valid_password(password):
      error_exists = True
      params['error_password'] = "Minimum password length is 6 characters"
    if error_exists:
      return render(request, "workouts/sign_up.html", params)

    user = User(first_name = first_name,
                last_name = last_name,
                email = email,
                username = username)
    user.set_password(password)
    user.save()
    # TODO add sign up success message to login
    return HttpResponseRedirect(reverse("workouts:login"))
  else:
    return render(request, "workouts/sign_up.html")

@login_required()
def journal(request):
  # TODO get_object_or_404?
  journal = Journal.objects.filter(user=request.user)
  journal_planned = journal.filter(completed_count=0)
  journal_completed = journal.filter(completed_count__gt=0)

  params = dict(journal_planned=journal_planned, 
                journal_completed=journal_completed)

  if request.method == 'POST':
    if 'entry_id' in request.POST:
      error_exists = False
      entry_id = request.POST['entry_id']
      if not valid_digit(entry_id):
        error_exists = True
        params['error_entry_id'] = "The journal entry did not match any records"
      if error_exists:
        return render(request, 'workouts/journal.html', params)

      entry_id = int(entry_id)
      entry = get_object_or_404(Journal, user=request.user, pk=entry_id)

      if 'mark_complete' in request.POST:
        entry.completed_count = F('completed_count') + 1
        entry.completed_on = timezone.now()
        entry.save()
      if 'remove_from_journal' in request.POST:
        entry.delete()

  return render(request, "workouts/journal.html", params)

def results(request, routine_id):
  response = "You're looking at the results of routine %s."
  return HttpResponse(response % routine_id)


# TODO add delete comment capability
def detail(request, routine_id):
  routine = get_object_or_404(Routine, pk=routine_id)
  if request.method == 'POST':
    if "add_to_journal" in request.POST:
      if not request.user.is_authenticated:
        return render(request, 'workouts/detail.html', { 'routine': routine, 'error_add_to_journal': "You must log in first"})
      if request.user.journal_set.filter(routine=routine).exists():
        return render(request, "workouts/detail.html", { 'routine': routine, 'error_add_to_journal': 'Already added to journal'})
      entry = Journal(user=request.user, routine=routine)
      entry.save()
      return render(request, "workouts/detail.html", {'routine': routine, 'add_to_journal_success': "Added routine to journal"})
    if "like" in request.POST:
      if not request.user.is_authenticated:
        return render(request, 'workouts/detail.html', { 'routine': routine, 'error_like': "You must log in first"})
      # get row out of db
      l = request.user.like_set.filter(routine=routine)
      if l.exists():
        routine.likes = F('likes') - 1
        routine.save()
        l.delete()
      else:
        routine.likes = F('likes') + 1
        routine.save()
        request.user.like_set.create(routine=routine)
      # reload the object to show the DB update
      routine = Routine.objects.filter(pk=routine_id).get()
      return render(request, "workouts/detail.html", {'routine': routine})
    # TODO ask for confirmation to delete (pop-up)
    if "delete_routine" in request.POST:
      if request.user.is_authenticated:
        if request.user != routine.created_by:
          return render(request, 'workouts/detail.html', { 'routine': routine, 'error_delete':"you aren't the creator of this routine"})
        routine.delete()
        return HttpResponseRedirect(reverse('workouts:index'))
    if "comment" in request.POST:
      if request.user.is_authenticated:
        comment_text = request.POST["comment_text"]
        params = dict(routine=routine, comment_text=comment_text)
        if not valid_content_input(comment_text):
          params['error_text'] = "Please enter the details"
          return render(request, 'workouts/detail.html', params)
        routine.comment_set.create(created_by=request.user,
                                   comment_text=comment_text,
                                   pub_date=timezone.now())
        return HttpResponseRedirect(reverse('workouts:detail', args=[routine.id]))
    # redirect anonymous users to login
    return HttpResponseRedirect(reverse('workouts:login'))
  else:
    # TODO grey out add to journal if already in journal
    tag_list = " ".join(routine.tag_set.values_list('tag_text', flat=True))
    return render(request, 'workouts/detail.html', {
      'routine': routine,
      'tag_list': tag_list,
    })


def get_routine_form_params(request):
  routine_title = request.POST['routine_title']
  routine_text = request.POST['routine_text']
  tag_list = request.POST['tag_list']
  return dict(routine_title=routine_title,routine_text=routine_text,
              tag_list=tag_list, created_by=request.user)

def valid_routine_form(request):
  """Checks routine form for routine_title, routine_text, and tag_list. Returns tuple of an error check and params. Does not check for post method."""
  params = get_routine_form_params(request)
  error_exists = False
  if not valid_title(params['routine_title']):
    error_exists = True
    params['error_title'] = "Enter a title under 70 characters long. Only letters and numbers allowed."
  if not valid_content_input(params['routine_text']):
    error_exists = True
    params['error_text'] = "Enter details under 1000 characters long."
  if not valid_tag_list(params['tag_list']):
    error_exists = True
    params['error_tag_list'] = "Tags should be at least 3 characters long using only letters and numbers. Separate tags with a space."
  return (error_exists, params)

@login_required()
def add_routine(request):
  if request.method == 'POST':
    error_exists, params = valid_routine_form(request)
    if error_exists:
      return render(request, 'workouts/add_routine.html', params)
    r = Routine(routine_title=params['routine_title'],
                routine_text=params['routine_text'], 
                created_by=request.user)
    r.save()
    [r.tag_set.create(tag_text=tag_text) for tag_text in params['tag_list'].split()]
    return HttpResponseRedirect(reverse('workouts:index'))
  else:
    return render(request, 'workouts/add_routine.html')

@login_required()
def edit_routine(request, routine_id):
  routine = get_object_or_404(Routine, pk=routine_id)
  if request.method == 'POST':
    error_exists, params = valid_routine_form(request)
    if request.user != routine.created_by:
      error_exists = True
      params['error_owner'] = "You're not the owner of this routine"
    if error_exists:
      return render(request, 'workouts/edit_routine.html', params)
    routine.routine_title = params['routine_title']
    routine.routine_text = params['routine_text']
    routine.save()
    routine.tag_set.all().delete()
    # TODO ensure no duplicate tags
    [routine.tag_set.create(tag_text=tag_text) for tag_text in params['tag_list'].split()]
    return HttpResponseRedirect(reverse('workouts:detail', args=[routine_id]))
  else:
    tag_list = " ".join(routine.tag_set.values_list('tag_text', flat=True))
    return render(request, "workouts/edit_routine.html", {
      'routine_title': routine.routine_title,
      'routine_text': routine.routine_text,
      'tag_list': tag_list,
      })

@login_required()
def customize_routine(request, routine_id):
  routine = get_object_or_404(Routine, pk=routine_id)
  if request.method == 'POST':
    error_exists, params = valid_routine_form(request)
    if error_exists:
      return render(request, 'workouts/customize_routine.html', params)
    # create copy of routine
    # TODO track who modified and who was previous author, add links
    customized_routine = Routine(routine_title=params['routine_title'],
                                 routine_text=params['routine_text'],
                                 pub_date=timezone.now(),
                                 created_by=request.user)
    customized_routine.save()
    # TODO ensure no duplicate tags
    [customized_routine.tag_set.create(tag_text=tag_text) for tag_text in params['tag_list'].split()]
    request.user.journal_set.create(routine=customized_routine)
    return HttpResponseRedirect(reverse('workouts:journal'))
  else:
    tag_list = " ".join(routine.tag_set.values_list('tag_text', flat=True))
    return render(request, "workouts/customize_routine.html", {
      'routine_title': routine.routine_title,
      'routine_text': routine.routine_text,
      'tag_list': tag_list,
      })


def parse_exercises(exercises):
  return exercises.split("\r\n")

def add_exercise(request, routine_id):
  if request.method == 'GET':
    return render(request, 'workouts/add_exercise.html')
  elif request.method == 'POST' and request.POST['exercise_text']:
    exercises = parse_exercises(request.POST['exercise_text'])
    r = get_object_or_404(Routine, pk=routine_id)
    for exercise in exercises:
      r.exercise_set.create(exercise_text=exercise, pub_date=timezone.now())
    return HttpResponseRedirect(reverse('workouts:detail', args=[routine_id]))
  else:
    return render(request, 'workouts/add_exercise.html', {
      'error_message': "You didn't enter a name"
    })

def sort_by_likes(request):
  highest_likes_routine_list = Routine.objects.order_by('-likes')[:10]
  context = {'list': highest_likes_routine_list}
  return render(request, 'workouts/index.html', context)

# TODO created list of trending--reddit's hot mechanism
def trending(request):
  trending_list = Routine.objects.order_by('-pub_date')[:10]
  context = {'list': trending_list}
  return render(request, 'workouts/index.html', context)
  
def user(request):
  user_list = User.objects.all()
  context = {'list': user_list}
  return render(request, 'workouts/user.html', context)

def user_detail(request, user_id):
  # TODO get_object_or_404?
  user = get_object_or_404(User, pk=user_id)
  journal = Journal.objects.filter(user=user)
  journal_planned = journal.filter(completed_count=0)
  journal_completed = journal.filter(completed_count__gt=0)

  params = dict(user=user, journal_planned=journal_planned, 
                journal_completed=journal_completed)

  return render(request, "workouts/journal_browse.html", params)

def follow_user(request, user_id):
  """
  user = get_object_or_404(User, pk=user_id)
  user_list = User.objects.all()
  currently_following = user.follower.values_list("user", flat=True)
  currently_following_all = user.follower.all()
  if request.method == 'POST':
    new_following_ids = request.POST.getlist('follow')
    # compare current following to new list
    # if current following is in new list, do nothing
    # if current following isn't part of new list, remove it
    # if any new list isn't in current following, add it 
    for current_user in currently_following_all:
      if str(current_user.id) not in new_following_ids:
        current_user.delete()

    for new_id in new_following_ids:
      if int(new_id) not in user.follower.values_list("id", flat=True):
        user.follower.create(user=get_object_or_404(User, pk=int(new_id)), 
                             follower=user,
                             create_date=timezone.now())
        
    return HttpResponseRedirect(reverse('workouts:user'))
  else:
    # TODO replace with Django forms
    return render(request, 'workouts/follow_user.html', {
      'list': user_list,
      'current_following': currently_following,
    })
  """
  return HttpResponse("This is the follow a new user page")
