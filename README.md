# Django Pagel Views

Logicaly separates panels in django-based views.
Panels can be loaded via Ajax or rendered directly in View.


# Repo-Status

[![Build Status](https://travis-ci.org/STUDITEMPS/django_panel_views.svg?branch=master)](https://travis-ci.org/STUDITEMPS/django_panel_views)

[![Coverage Status](https://coveralls.io/repos/STUDITEMPS/django_panel_views/badge.svg?branch=master&service=github)](https://coveralls.io/github/STUDITEMPS/django_panel_views?branch=master)


# Usage

**Define Panels**

In your Project: views.py

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

**Define PanelView**

    class DashboardPanelView(BasePanelView):
        template_name = "tests/dashboard.html"
        panels = {
            'panel1': DashboardView1,
        }

        def get_context_data(self, *args, **kwargs):
            return {'page_context': 'content of page_context'}

**Register in URLS.py**

In urls.py

    from your_project.views import DashboardPanelView

    urlpatterns = [
        url(r'^test/', DashboardPanelView.as_view(), name='test'),
    ]

**Template variables**

In **dashboard.html** you can access all context variables from **DashboardPanelView**

    {{ additional_context }}

Renders collected js/css from view and panels

    {{ view.media }}


Panels can be accessed via **panels**-variable.
Panel-Ajax-Url can be accessed via **get_url**

    {% for name, panel in view.panels.items %}
    <tr>
      <td>{{ name }}</td>
      <td>{{ panel.title }}</td>
      <td><a href="{{ panel.get_url }}">{{ panel.get_url }}</a></td>
    </tr>
    {% endfor %}

Render panel directly without to use ajax

    {{ view.panels.panel1.content }}
    # or
    {{ view.panel1.content }}

Accessing PanelView from Panel

    {{ panel.view.VIEW_ATTR }}


**For detail examples see test.py and test/tempates**


# Changelog

* Bumped Version: 0.1.0

