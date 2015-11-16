# coding: utf-8

from django.views.generic import TemplateView
from django.shortcuts import render
from django.http import HttpResponseBadRequest, HttpResponse
from django.template import RequestContext, loader

VIEW_IDENTIFIER = 'view'


class BasePanelView(TemplateView):
    panels = {}
    context = {}
    url = None

    def __init__(self, template_name=None, panels=None, *args, **kwargs):
        super(BasePanelView, self).__init__(*args, **kwargs)

        self.template_name = template_name
        self.panels = panels

        self.context = {
            'panels': panels if panels else self.panels,
            'current_view': self
        }

    def __setup_views(self, request):
        for name, view in self.panels.items():
            view.set_up(request, name)

        self.url = request.path

    def get_url(self):
        return self.url

    def get(self, request, *args, **kwargs):
        self.__setup_views(request)

        self.request = request
        ajax_view = request.GET.get(VIEW_IDENTIFIER, None)
        if ajax_view and ajax_view in self.panels:
            if not request.is_ajax():
                return HttpResponseBadRequest()
            return self.panels[ajax_view].get(request)

        self.context.update(self.get_context_data(**kwargs))
        return self.render_to_response(self.context)

    def post(self, request, *args, **kwargs):
        self.__setup_views(request)
        ajax_view = request.GET.get(VIEW_IDENTIFIER, None)
        if ajax_view and ajax_view in self.panels:
            if not request.is_ajax():
                return HttpResponseBadRequest()
            return self.panels[ajax_view].post(request, *args, **kwargs)

        return HttpResponseBadRequest("This View does not support POST")


class Panel(object):
    template_name = None
    page = None
    title = ''
    name = ''
    request = {}
    context = {}

    def __init__(self, page, template_name='', title='', *args, **kwargs):
        if template_name:
            self.template_name = template_name
        self.page = page
        self.title = title
        self.context = {'self': self}

    def set_up(self, request, name):
        self.request = request
        self.name = name
        if not self.title:
            self.title = name

    def get_url(self):
        return u"{}?{}={}".format(
            self.page.get_url(),
            VIEW_IDENTIFIER,
            self.name
        )

    def get_context_data(self):
        return {}

    def content(self, *args, **kwargs):
        self.context.update(self.get_context_data(*args, **kwargs))
        return loader.get_template(self.template_name).render(
            RequestContext(self.request, self.context)
            # self.context
        )

    def get(self, request, *args, **kwargs):
        return HttpResponse(self.content())

    def post(self, request, *args, **kwargs):
        raise NotImplementedError('This function is not implemented now')
