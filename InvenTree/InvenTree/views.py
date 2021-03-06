# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.template.loader import render_to_string
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from django.views.generic import UpdateView, CreateView, DeleteView


class AjaxView(object):

    ajax_form_action = ''
    ajax_form_title = ''
    ajax_submit_text = 'Submit'

    def getAjaxTemplate(self):
        if hasattr(self, 'ajax_template_name'):
            return self.ajax_template_name
        else:
            return self.template_name


    def renderJsonResponse(self, request, form, data={}):

        context = {'form': form
                  }

        data['title'] = self.ajax_form_title

        data['submit_text'] = self.ajax_submit_text

        data['html_form'] = render_to_string(
            self.getAjaxTemplate(),
            context,
            request=request
        )

        return JsonResponse(data)


class AjaxCreateView(AjaxView, CreateView):

    def post(self, request, *args, **kwargs):

        if request.is_ajax():
            form = self.form_class(request.POST)

            data = {'form_valid': form.is_valid()}

            if form.is_valid():
                obj = form.save()

                # Return the PK of the newly-created object
                data['pk']  = obj.pk

            return self.renderJsonResponse(request, form, data)

        else:
            return super(CreateView, self).post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):

        response = super(CreateView, self).get(request, *args, **kwargs)

        if request.is_ajax():
            form = self.form_class(initial=self.get_initial())

            return self.renderJsonResponse(request, form)

        else:
            return response


class AjaxUpdateView(AjaxView, UpdateView):

    def post(self, request, *args, **kwargs):

        if request.is_ajax():
            form = self.form_class(request.POST, instance=self.get_object())

            data = {'form_valid': form.is_valid()}

            if form.is_valid():
                obj = form.save()

            return self.renderJsonResponse(request, form, data)

        else:
            response = super(UpdateView, self).post(request, *args, **kwargs)
            return response

    def get(self, request, *args, **kwargs):

        response = super(UpdateView, self).get(request, *args, **kwargs)

        if request.is_ajax():
            form = self.form_class(instance = self.get_object())

            return self.renderJsonResponse(request, form)

        else:
            return response


class AjaxDeleteView(AjaxView, DeleteView):

    def post(self, request, *args, **kwargs):

        if request.is_ajax():
            obj = self.get_object()
            pk = obj.id
            obj.delete()

            data = {'id': pk,
                    'delete': True}

            return JsonResponse(data)

        else:
            return super(DeleteView, self).post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):

        response = super(DeleteView, self).get(request, *args, **kwargs)

        if request.is_ajax():

            data = {'id': self.get_object().id,
                    'title': self.ajax_form_title,
                    'delete': False,
                    'html_data': render_to_string(self.getAjaxTemplate(),
                                                  self.get_context_data(),
                                                  request=request)
                   }

            return JsonResponse(data)

        else:
            return response
