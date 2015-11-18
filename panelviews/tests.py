# coding: utf-8

# import os
from django.test import LiveServerTestCase
from django.test import Client
from django import forms
from django.http import JsonResponse

from panelviews.views import BasePanelView
from panelviews.views import Panel
from panelviews.views import PANEL_IDENTIFIER


class NameForm(forms.Form):
    email = forms.EmailField(label='E-Mail')

    class Media:
        # css = {'all': ('pretty.css',)}
        js = ('panelviews/js/bootstrap.min.js', )


class DashboardView1(Panel):
    title=u"Übersichts-Seite"
    template_name='tests/view1.html'

    class Media:
        js = ('panelviews/js/test.js', )
        css = {'all': ('panelviews/css/test.css', )}

    def get_context_data(self):
        return {
            'additional_context': 'this is a content of additional_context'
        }


class DashboardView2(Panel):
    title=u"Übersichts-Seite 2"


class FormView(Panel):
    form_class = NameForm
    template_name='tests/view3.html'

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
    template_name = "tests/dashboard.html"
    panels = {
        'panel1': DashboardView1,
        'panel2': DashboardView2,
        'panel3': FormView,
    }

    def get_context_data(self, *args, **kwargs):
        return {'page_context': 'content of page_context'}



class NotPanelClass1(object):
    pass

class NotPanelClass2(object):
    def __init__(self, view, name):
        pass

class ErrorPage(BasePanelView):
    template_name = "tests/dashboard.html"
    panels = {
        12313: DashboardView1,
    }

class ErrorPage2(BasePanelView):
    template_name = "tests/dashboard.html"
    panels = {
        'identifier': NotPanelClass1,
    }

class ErrorPage3(BasePanelView):
    template_name = "tests/dashboard.html"
    panels = {
        'identifier': NotPanelClass2,
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
        self.panel1_resp = self.client.get(
            '/test/?{}=panel1'.format(PANEL_IDENTIFIER),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.panel2_resp = self.client.get(
            '/test/?{}=panel2'.format(PANEL_IDENTIFIER),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.panel3_resp = self.client.get(
            '/test/?{}=panel3'.format(PANEL_IDENTIFIER),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

    def test_panel_name_validation(self):
        self.assertRaises(ValueError, ErrorPage)

        self.assertRaises(ValueError, ErrorPage2().get, 'afawf')
        self.assertRaises(ValueError, ErrorPage3().get, 'awfwf')

        try:
            DashboardPage()
        except ValueError:
            self.fail('DashboardPage raises ValueError on initialization')

    def test_dashboard_inherit(self):
        self.assertTrue('base.html' in self.page.content)
        # Dashboard
        self.assertTrue('dashboard' in self.page.content)

    def test_collected_panel_media(self):
        self.assertTrue('test.js' in self.page.content)
        self.assertTrue('test.css' in self.page.content)

    def test_page_post_not_supported(self):
        resp = self.client.post('/test/', {})
        self.assertEqual(resp.status_code, 400)

    def test_page_unicode_rendered(self):
        content = self.page.content.decode("utf-8")
        self.assertTrue(u"öäüß" in content)

    def test_page_view_urls(self):
        # views urls
        self.assertTrue('?{}=panel1'.format(PANEL_IDENTIFIER) in self.page.content)
        self.assertTrue('?{}=panel2'.format(PANEL_IDENTIFIER) in self.page.content)
        self.assertTrue('?{}=panel3'.format(PANEL_IDENTIFIER) in self.page.content)

    def test_page_context(self):
        # views rendered content
        self.assertTrue('content of page_context' in self.page.content)

    def test_view_rendered(self):
        # views rendered content
        self.assertTrue('panel1' in self.page.content)
        self.assertTrue('panel2' in self.page.content)
        self.assertTrue('panel3' in self.page.content)

    def test_page_view_context(self):
        # panels rendered content
        self.assertTrue('additional_context' in self.page.content)

    def test_page_static_url_available(self):
        self.assertTrue('/static/' in self.page.content)

    def test_page_media_url_available(self):
        self.assertTrue('/media/' in self.page.content)

    def test_panel_view(self):
        self.assertTrue('additional_context' in self.panel1_resp.content)

    def test_panel_call(self):
        resp = self.client.get('/test/?{}=panel1'.format(PANEL_IDENTIFIER))
        self.assertEqual(resp.status_code, 400)

        self.assertEqual(self.panel1_resp.status_code, 200)
        self.assertTrue('panel1' in self.panel1_resp.content)
        self.assertTrue('panel2' in self.panel2_resp.content)
        self.assertTrue('panel3' in self.panel3_resp.content)

    def test_panel_unicode_rendered(self):
        content = self.panel1_resp.content.decode("utf-8")
        self.assertTrue(u"öäüß" in content)

    def test_panel2_media_static(self):
        # Media is available
        self.assertTrue('/static/' in self.panel2_resp.content)
        # Media is available
        # self.assertTrue('/media/' in self.panel2_resp.content)

    def test_panel3_csrftoken(self):
        self.assertTrue('csrfmiddlewaretoken' in self.panel3_resp.content)

    def test_panel3_form_media(self):
        static_url = '/static/panelviews/js/bootstrap.min.js'
        self.assertTrue(static_url in self.panel3_resp.content)

    def test_panel_post_bad_request(self):
        resp = self.client.post('/test/?{}=panel3'.format(PANEL_IDENTIFIER), {})
        self.assertEqual(resp.status_code, 400)

    def test_panel_post(self):
        # Post on a panel
        resp = self.client.post(
            '/test/?{}=panel3'.format(PANEL_IDENTIFIER),
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertTrue('errors' in resp.content)
        self.assertTrue('email' in resp.content)

        resp = self.client.post(
            '/test/?{}=panel3'.format(PANEL_IDENTIFIER),
            {'email': 'invalid'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertTrue('errors' in resp.content)
        self.assertTrue('email' in resp.content)

    def test_user_not_logged_in(self):
        resp = self.client.get('/test-login-required/')
        self.assertEqual(resp.status_code, 302)
