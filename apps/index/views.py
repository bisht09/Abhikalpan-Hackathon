from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from account.forms import RegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import Complaint, Comment, Like, Company
import json
from django.core import serializers
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, KeywordsOptions,EntitiesOptions, RelationsOptions


natural_language_understanding = NaturalLanguageUnderstandingV1(
   version='2018-11-16',
   iam_apikey='sgggLr1OhziffHvNtMnrcXAZdrwlhRdk_khhWV1BFK_o',
   url='https://gateway-fra.watsonplatform.net/natural-language-understanding/api'
)

def recognize(input_text):
    response = natural_language_understanding.analyze(
       text=input_text,
       features=Features(
           entities=EntitiesOptions(model ='73914a25-4c07-4174-923e-74852b373117')))
    return(response.result['entities'])

def index(request):
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            status = 2
            context = {
                'status' : status,
                'form': form
            }
            return render(request, 'index/index.html', context);
        else:
            status = 3
            context = {
                'form': form,
                'status': status
            }
            return render(request, 'index/index.html', context)

    else:
        form = RegistrationForm()
    context = {
        'form': form
    }
    return render(request, 'index/index.html', context)

@login_required
def dashboard(request):
    complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')
    all_complaints = Complaint.objects.filter(~Q(user=request.user)).order_by('-created_at')
    company_names = Company.objects.all()

    if request.method == 'POST':
        print(request.POST['company_name'])
        company = Company.objects.get(company_name=request.POST['company_name'])
        curr_complaint = Complaint.objects.create(
            user=request.user,
            title=request.POST['title'],
            meta_description=request.POST['meta_description'],
            description=request.POST['description'],
            company=company)

        result = recognize(request.POST['description'])
        curr_complaint = Complaint.objects.filter(id=curr_complaint.id).order_by('-created_at')
        curr_complaint = serializers.serialize('json', list(curr_complaint))

        context = {
            'result': result,
            'curr_complaint': curr_complaint
        }

        return HttpResponse(JsonResponse(context), content_type='application/json')

    if 'delete' in request.session:
        delete = 1
        del request.session['delete']
    else:
        delete = 0

    if 'first_time_login' in request.session:
        first_time_login = 1
        del request.session['first_time_login']
    else:
        first_time_login = 0

    context = {
        'complaints': complaints,
        'delete': delete,
        'first_time_login': first_time_login,
        'all_complaints': all_complaints,
        'company_names': company_names
    }
    return render(request, 'index/dashboard.html', context)


@login_required
def complaintSave(request):
	if request.method == 'POST':
		ComplaintId = request.POST['complaint_id']
		desc = request.POST['description']
		comp = Complaint.objects.get(pk=ComplaintId)
		comp.description = desc
		comp.save()
		res="success"
		return HttpResponse(res)
	else:
		res="error"
		return HttpResponse(res)

@login_required
def complaintDetails(request, id):
    complaint = Complaint.objects.get(id=id)
    comment = Comment.objects.filter(complaint=complaint)

    try:
        like_object = Like.objects.get(complaint=complaint, liked_by=request.user)
        like = 1
    except:
        like = 0

    likes_count = Like.objects.filter(complaint=complaint).count()

    context = {
        'complaint': complaint,
        'comment': comment,
        'like': like,
        'likes_count': likes_count
    }
    return render(request, 'index/complaintDetails.html', context)


@login_required
def deleteDetails(request, id):
    if request.method == 'POST':
        delete_complaints = Complaint.objects.filter(id=id)
        delete_complaints.delete()
        complaints = Complaint.objects.all()
        context = {
            'complaints': complaints ,
            'delete': 1
        }
        request.session['delete'] = 1
    else:
        context = {
            'delete': 0
        }
    return redirect('index:dashboard')




def LoginView(request):
    if request.user.is_authenticated:
        return render(request, 'index/dashboard.html', {})
    logout(request)
    username = password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                request.session['first_time_login'] = 1
                return redirect('index:dashboard')
    form = RegistrationForm()
    status = 4
    context = {
        'form': form,
        'status': status
    }
    return render(request, 'index/index.html', context)

def LogoutView(request):
    logout(request)
    form = RegistrationForm()
    context = {
        'form':form
    }
    return render(request, 'index/index.html', context)


def CommentView(request):
    if request.method == 'POST':
        complaint_id = request.POST['complaint_id']
        complaint = Complaint.objects.get(id=request.POST['complaint_id'])
        Comment.objects.create(
            user=request.user,
            complaint=complaint,
            comment=request.POST['comment'])

        comment = Comment.objects.filter(complaint=complaint).order_by('-commented_at')
        comment = serializers.serialize('json', list(comment))

        context = {
            'comment': comment
        }

        return HttpResponse(JsonResponse(context), content_type='application/json')


def LikeView(request):
    if request.method == 'POST':
        complaint = Complaint.objects.get(id=request.POST['complaint_id'])
        try:
            like_object = Like.objects.get(complaint=complaint, liked_by=request.user)
            like_object.delete()
            like = 0
        except:
            Like.objects.create(
                complaint=complaint,
                liked_by=request.user)
            like = 1

        likes_count = Like.objects.filter(complaint=complaint).count()

        context = {
            'like': like,
            'likes_count': likes_count
        }
        return HttpResponse(JsonResponse(context), content_type='application/json')
