# coding: utf-8

import copy
import six

from django.views.generic import TemplateView
from django.views.generic.base import ContextMixin
from django.shortcuts import render, render_to_response
from django.http import HttpResponseBadRequest, HttpResponse
from django.template import RequestContext, loader
from django.forms.widgets import media_property, Media
from django.forms.forms import DeclarativeFieldsMetaclass


PANEL_IDENTIFIER = 'panel'


class BasePanelView(six.with_metaclass(DeclarativeFieldsMetaclass, TemplateView)):
    template_name_suffix = '_panelview'
    panels = {}
    url = None

    @property
    def media(self):
        """
        Collect Media.
        """
        media = Media()
        for panel in self.panels.values():
            media = media + panel.media
        return media

    def __init__(self,  *args, **kwargs):
        super(BasePanelView, self).__init__(*args, **kwargs)
        for name in self.panels.keys():
            if not isinstance(name, basestring):
                raise ValueError(
                    u'panel name must be string not {}'.format(name.__class__)
                )
        self.context = {'view': self,}

    def __setup_panels(self, request):
        panels = {}
        for name, panel_class in self.panels.items():
            panel = panel_class(self, name)
            if not isinstance(panel, Panel):
                raise ValueError(
                    'Tab must be instance of Panel. found %s'
                    % panel.__class__
                )
            panel.set_up(request)
            panels[panel.name] = panel
        self.panels = panels
        self.url = request.path

    def get_url(self):
        return self.url

    def get(self, request, *args, **kwargs):
        self.__setup_panels(request)
        self.request = request
        panel_name = request.GET.get(PANEL_IDENTIFIER, None)
        if panel_name and panel_name in self.panels.keys():
            if not request.is_ajax():
                return HttpResponseBadRequest()
            return self.panels[panel_name].get(request)

        self.context.update(self.get_context_data(**kwargs))
        self.context.update(self.base_context_data())
        return self.render_to_response(self.context)

    def post(self, request, *args, **kwargs):
        self.__setup_panels(request)
        panel_name = request.GET.get(PANEL_IDENTIFIER, None)
        if panel_name and panel_name in self.panels.keys():
            if not request.is_ajax():
                return HttpResponseBadRequest()
            return self.panels[panel_name].post(request, *args, **kwargs)
        return HttpResponseBadRequest("This View does not support POST")


    def base_context_data(self):
        return {}

class Panel(six.with_metaclass(DeclarativeFieldsMetaclass, ContextMixin)):
    title = 'title'
    template_name_suffix = u'{}_panel'

    @property
    def media(self):
        return Media()

    def __init__(self, view, name):
        self.name = name
        if not hasattr(self, 'template_name'):
            self.template_name_suffix =\
                self.template_name_suffix.format(self.name)
        self.view = view
        self.context = {'panel': self, 'view': self.view}

    def set_up(self, request):
        self.request = request

    def get_url(self):
        return u"{}?{}={}".format(
            self.view.get_url(),
            PANEL_IDENTIFIER,
            self.name
        )

    def get_template(self, **kwargs):
        if hasattr(self, 'template_name'):
            return self.template_name
        view_template = self.view.get_template_names()[0]
        return view_template.replace(
            self.view.template_name_suffix,
            self.template_name_suffix
        )

    def content(self, *args, **kwargs):
        self.context.update(self.get_context_data(*args, **kwargs))
        template = self.get_template(**kwargs)
        return loader.get_template(self.template_name).render(
            RequestContext(self.request, self.context)
            # self.context
        )

    def get(self, request, *args, **kwargs):
        return HttpResponse(self.content())

    def post(self, request, *args, **kwargs):
        raise NotImplementedError('This function is not implemented now')
