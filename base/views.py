from base.forms import LoginForm, UserCreateForm
from userprofile.models import UserProfile
from transaction.models import Transaction
from groupaccount.forms import NewGroupAccountForm
from groupaccountinvite.models import GroupAccountInvite 

from registration.backends.simple.views import RegistrationView
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import auth
from django.views.generic.edit import UpdateView
from django.views.generic.edit import FormView

from itertools import chain
import logging
logger = logging.getLogger(__name__)


class BaseView(TemplateView):
  template_name = "base/base.html"
  context_object_name = "base"
  
  def getActiveMenu(self):
    return ''
  
  def get_context_data(self, **kwargs):
    # Call the base implementation first to get a context
    context = super(BaseView, self).get_context_data(**kwargs)
    if self.request.user.is_authenticated():
      userProfile = UserProfile.objects.get(user=self.request.user)
      invites = GroupAccountInvite.objects.filter(invitee=userProfile, isAccepted=False, isDeclined=False)
      context['user'] = self.request.user
      context['hasInvites'] = invites.exists()
      context['nInvites'] = invites.count()
      context['displayname'] = userProfile.displayname
      context['activeMenu'] = self.getActiveMenu()
      context['isLoggedin'] = True
    return context


class BaseUpdateView(UpdateView):
  template_name = "base/base.html"
  context_object_name = "base"
  
  def get_context_data(self, **kwargs):
    # Call the base implementation first to get a context
    context = super(BaseUpdateView, self).get_context_data(**kwargs)
    if self.request.user.is_authenticated():
      userProfile = UserProfile.objects.get(user=self.request.user)
      invites = GroupAccountInvite.objects.filter(invitee=userProfile, isAccepted=False, isDeclined=False)
      context['user'] = self.request.user
      context['hasInvites'] = invites.exists()
      context['nInvites'] = invites.count()
      context['displayname'] = userProfile.displayname
      context['isLoggedin'] = True
    return context


class NewRegistrationView(RegistrationView):
  
  def get_success_url(self, request, new_user):
    return '/'


class HomeView(BaseView):
  template_name = "base/index.html"
  context_object_name = "homepage"

  def getActiveMenu(self):
    return 'account'
  
  def getTransactions(self, buyerId):
    transactions = Transaction.objects.filter(buyer__id=buyerId)
    return transactions
  
  def get_context_data(self, **kwargs):
    from groupaccount.views import MyTransactionView
    # Call the base implementation first to get a context
    context = super(HomeView, self).get_context_data(**kwargs)
    user = self.request.user

    userProfile = UserProfile.objects.get(user=user)
    groupAccounts = userProfile.groupAccounts.all()
    
    transactionView = MyTransactionView()
    buyerTransactions = transactionView.getBuyerTransactions(userProfile.id)
    consumerTransactions = transactionView.getConsumerTransactions(userProfile.id)
    transactionsAll = list(chain(buyerTransactions, consumerTransactions))
    for transaction in transactionsAll:
      logger.debug(transaction.date)
    transactionsAllSorted = sorted(transactionsAll, key=lambda instance: instance.date, reverse=True)
    
    sentTransactions = transactionView.getSentTransactionsReal(userProfile.id)
    receivedTransactions = transactionView.getReceivedTransactionsReal(userProfile.id)
    transactionsRealAll = list(chain(sentTransactions, receivedTransactions))
    transactionsRealAllSorted = sorted(transactionsRealAll, key=lambda instance: instance.date, reverse=True)
    
    myTotalBalanceFloat = 0.0
    
    for groupAccount in groupAccounts:
      groupAccount.myBalanceFloat = MyTransactionView.getBalance(transactionView, groupAccount.id, userProfile.id)
      groupAccount.myBalance = '%.2f' % groupAccount.myBalanceFloat
      myTotalBalanceFloat += groupAccount.myBalanceFloat
    
    myTotalBalance = '%.2f' % myTotalBalanceFloat
    context['myTotalBalance'] = myTotalBalance
    context['myTotalBalanceFloat'] = myTotalBalanceFloat

    friends = UserProfile.objects.filter(groupAccounts__in=groupAccounts).distinct()
    logger.debug(friends)
    
    from groupaccountinvite.views import MyGroupAccountInvitesView
    
    groupAccountView = MyGroupAccountInvitesView()
    
    invitesSent = groupAccountView.getSentInvites(user);
    invitesReceived = groupAccountView.getReceivedInvites(user);
    invitesAll = list(chain(invitesSent, invitesReceived))
    invitesAll = set(invitesAll)
    invitesAllSorted = sorted(invitesAll, key=lambda instance: instance.createdDateAndTime, reverse=True)
    
    slowLastN = 10
    context['invitesAll'] = invitesAllSorted[0:slowLastN]
    context['friends'] = friends
    context['transactionsAll'] = transactionsAllSorted[0:slowLastN]
    context['transactionsRealAll'] = transactionsRealAllSorted[0:slowLastN]
    context['groups'] = groupAccounts
    context['homesection'] = True
    return context
  
  
class AboutView(BaseView):
  template_name = "base/about.html"
  context_object_name = "about"
  
  def getActiveMenu(self):
    return 'about'
  
  def get_context_data(self, **kwargs):
    # Call the base implementation first to get a context
    context = super(AboutView, self).get_context_data(**kwargs)
    context['aboutsection'] = True
    return context


class HelpView(BaseView):
  template_name = "base/help.html"
  context_object_name = "help"
  
  def get_context_data(self, **kwargs):
    # Call the base implementation first to get a context
    context = super(HelpView, self).get_context_data(**kwargs)
    context['helpsection'] = True
    return context


def newGroupAccount(request):
  def errorHandle(error):
    form = NewGroupAccountForm()
    context = RequestContext(request)
    if request.user.is_authenticated():
      context['user'] = request.user
      context['isLoggedin'] = True
    context['error'] = error
    context['form'] = form
    context['groupssection'] = True
    return render_to_response('base/newgroup.html', context)
  
  if request.method == 'POST': # If the form has been submitted...
    form = NewGroupAccountForm(request.POST) # A form bound to the POST data
    if form.is_valid():
      groupAccount = form.save()
      userProfile = UserProfile.objects.get(user=request.user)
      userProfile.groupAccounts.add(groupAccount)
      userProfile.save()
      context = RequestContext(request)
      if request.user.is_authenticated():
        context['user'] = request.user
        context['isLoggedin'] = True
      context['registered'] = True
      context['groupssection'] = True
      return render_to_response('groupaccount/newsuccess.html', context)
    else:
      error = u'form is invalid'
      return errorHandle(error)
  else:
    form = NewGroupAccountForm() # An unbound form
    context = RequestContext(request)
    if request.user.is_authenticated():
      context['user'] = request.user
      context['isLoggedin'] = True
    context['form'] = form
    context['groupssection'] = True
    return render_to_response('base/newgroup.html', context)

        
def login(request):
  def errorHandle(error):
    form = LoginForm()
    context = RequestContext(request)
    context['error'] = error
    context['form'] = form
    return render_to_response('registration/login.html', context)
        
  if request.method == 'POST': # If the form has been submitted...
    form = LoginForm(request.POST) # A form bound to the POST data
    if form.is_valid(): # All validation rules pass
      username = request.POST['username']
      password = request.POST['password']
      user = auth.authenticate(username=username, password=password)
      if user is not None:
        if user.is_active:
          # Redirect to a success page.
          auth.login(request, user)
          context = RequestContext(request)
          context['user'] = user
          context['isLoggedin'] = True
          return render_to_response('base/index.html', context)
        else:
          # Return a 'disabled account' error message
          error = u'account disabled'
          return errorHandle(error)
      else:
        # Return an 'invalid login' error message.
        error = u'invalid login'
        return errorHandle(error)
    else:
      error = u'form is invalid'
      return errorHandle(error)
  else:
    form = LoginForm() # An unbound form
    context = RequestContext(request)
    context['form'] = form
    return render_to_response('registration/login.html', context)

    
def logout(request):
  auth.logout(request)
  context = RequestContext(request)
  return render_to_response('base/index.html', context)
