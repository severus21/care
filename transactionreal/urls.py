from django.conf.urls import patterns, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView

from transaction.models import Transaction
from transactionreal.views import NewRealTransactionView, MyRealTransactionView, EditRealTransactionView


urlpatterns = patterns('',
                       url(r'^(?P<tableView>\d+)$', login_required(MyRealTransactionView.as_view())),
                       url(r'^new/$', login_required(NewRealTransactionView.as_view())),
                       url(r'^new/(?P<group_account_id>\d+)/$', login_required(NewRealTransactionView.as_view())),
                       url(r'^edit/(?P<pk>\d+)$', login_required(EditRealTransactionView.as_view())),
                       url(r'^(?P<pk>\d+)/$', login_required(
                           DetailView.as_view(model=Transaction, template_name='transaction/detail.html'))),
)

urlpatterns += staticfiles_urlpatterns()
