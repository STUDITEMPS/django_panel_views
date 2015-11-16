# coding: utf-8

# import os
from django.test import LiveServerTestCase
from django.test import Client
from django import forms
from django.views.generic.edit import FormMixin
from django.http import JsonResponse

from panelviews.views import BasePanelView
from panelviews.views import Panel


class NameForm(forms.Form):
    email = forms.EmailField(label='E-Mail')

    class Media:
        # css = {'all': ('pretty.css',)}
        js = ('panelviews/js/bootstrap.min.js', )


class DashboardView1(Panel):
    def get_context_data(self):
        return {
            'additional_context': 'this is a content of additional_context'
        }


class DashboardView2(Panel):
    template_name = 'tests/view2.html'


class FormView(Panel, FormMixin):
    form_class = NameForm

    def get_context_data(self, *args, **kwargs):
        context = super(FormView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()()
        return context

    def get_form(self):
        return NameForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()(request.POST)
        form.is_valid()
        return JsonResponse({'errors': form.errors})


class DashboardPage(BasePanelView):
    def __init__(self, *args, **kwargs):
        view1 = DashboardView1(
            page=self,
            template_name='tests/view1.html',
            title=u"Übersichts-Seite"
        )
        view2 = DashboardView2(page=self, title=u"Übersichts-Seite 2")
        view3 = FormView(page=self, template_name='tests/view3.html')

        super(DashboardPage, self).__init__(
            template_name="tests/dashboard.html",
            panels={'view1': view1, 'view2': view2, 'view3': view3}
        )

    def get_context_data(self, *args, **kwargs):
        return {
            'page_context': 'content of page_context'
        }


class LoginDashboardPage(BasePanelView):
    template_name = "tests/dashboard.html"


class NotLoggedIPage(BasePanelView):
    template_name = "tests/not-logged-in.html"


class PageViewTestCase(LiveServerTestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/test/"
        self.page = self.client.get('/test/')
        self.view1_resp = self.client.get(
            '/test/?view=view1',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.view2_resp = self.client.get(
            '/test/?view=view2',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.view3_resp = self.client.get(
            '/test/?view=view3',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

    def test_dashboard_inherit(self):
        self.assertTrue('base.html' in self.page.content)
        # Dashboard
        self.assertTrue('dashboard' in self.page.content)

    def test_page_post_not_supported(self):
        resp = self.client.post('/test/', {})
        self.assertEqual(resp.status_code, 400)

    def test_page_unicode_rendered(self):
        content = self.page.content.decode("utf-8")
        self.assertTrue(u"öäüß" in content)

    def test_page_view_urls(self):
        # views urls
        self.assertTrue('?view=view1' in self.page.content)
        self.assertTrue('?view=view2' in self.page.content)
        self.assertTrue('?view=view3' in self.page.content)

    def test_page_context(self):
        # views rendered content
        self.assertTrue('content of page_context' in self.page.content)

    def test_view_rendered(self):
        # views rendered content
        self.assertTrue('view1' in self.page.content)
        self.assertTrue('view2' in self.page.content)
        self.assertTrue('view3' in self.page.content)

    def test_page_view_context(self):
        # views rendered content
        self.assertTrue('additional_context' in self.page.content)

    def test_page_static_url_available(self):
        self.assertTrue('/static/' in self.page.content)

    def test_page_media_url_available(self):
        self.assertTrue('/media/' in self.page.content)

    def test_ajax_view(self):
        self.assertTrue('additional_context' in self.view1_resp.content)

    def test_view_call(self):
        resp = self.client.get('/test/?view=view1')
        self.assertEqual(resp.status_code, 400)

        self.assertEqual(self.view1_resp.status_code, 200)
        self.assertTrue('view1' in self.view1_resp.content)
        self.assertTrue('view2' in self.view2_resp.content)
        self.assertTrue('view3' in self.view3_resp.content)

    def test_view_unicode_rendered(self):
        content = self.view1_resp.content.decode("utf-8")
        self.assertTrue(u"öäüß" in content)

    def test_view2_media_static(self):
        # Media is available
        self.assertTrue('/static/' in self.view2_resp.content)
        # Media is available
        self.assertTrue('/media/' in self.view2_resp.content)

    def test_view3_csrftoken(self):
        self.assertTrue('csrfmiddlewaretoken' in self.view3_resp.content)

    def test_view3_form_media(self):
        static_url = '/static/panelviews/js/bootstrap.min.js'
        self.assertTrue(static_url in self.view3_resp.content)

    def test_view_post_bad_request(self):
        resp = self.client.post('/test/?view=view3', {})
        self.assertEqual(resp.status_code, 400)

    def test_view_post(self):
        # Post on a view
        resp = self.client.post(
            '/test/?view=view3',
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertTrue('errors' in resp.content)
        self.assertTrue('email' in resp.content)

        resp = self.client.post(
            '/test/?view=view3',
            {'email': 'invalid'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertTrue('errors' in resp.content)
        self.assertTrue('email' in resp.content)

    def test_user_not_logged_in(self):
        resp = self.client.get('/test-login-required/')
        self.assertEqual(resp.status_code, 302)
