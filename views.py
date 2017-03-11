from django.shortcuts import render

from django.http import Http404
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.forms.models import model_to_dict

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import models

FIELD_DB_NAME = 0
FIELD_DISPLAY_NAME = 1


class BaseRestInventoryOrder(APIView):
    def initial(self, request, *args, **kwargs):
        self.nv_models = kwargs.get('nv_params', {}).get('models', None)
        self.InventoryOrderSerializer = kwargs.get('nv_params', {}).get('InventoryOrderSerializer', None)
        super(BaseRestInventoryOrder, self).initial(request, *args, **kwargs)

    def post(self, request, format=None):
        """ Current user will place order"""
        inventory_id = request.data.get('inventory_id', None)

        user_id = None
        if hasattr(request, 'user'):
            user_id = request.user.id

        if inventory_id is not None and user_id is not None:
            try:
                inventory_item = self.nv_models.Inventory.objects.get(
                    pk=inventory_id)
            except self.nv_models.Inventory.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            try:
                user = self.nv_models.ExtendedUser.objects.get(pk=user_id)
            except self.nv_models.ExtendedUser.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            try:
                new_data = {}
                new_data['inventory'] = inventory_item
                new_data['customer'] = user
                new_order = self.nv_models.InventoryOrder(**new_data)
                new_order.save()

                return Response(self.InventoryOrderSerializer(new_order).data)
            except Exception as e:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class BaseListView(ListView):
    template_name = 'generic/list.html'

    def get_context_data(self, **kwargs):
        context = super(BaseListView, self).get_context_data(**kwargs)

        # self.title handling
        if getattr(self, 'title', None) is None:
            context['title'] = self.model.__name__
        else:
            context['title'] = self.title

        context['fields'] = []
        context['row_data'] = []

        if self.fields is not None:
            for field in self.fields:
                context['fields'].append(_(field[FIELD_DISPLAY_NAME]))
            context['fields'].append(_("Actions"))

            for value in context['object_list']:
                current_row = []
                for field in self.fields:
                    if hasattr(value, field[FIELD_DB_NAME]):
                        current_row.append(getattr(value, field[0]))
                    else:
                        # for debugging
                        current_row.append('<data does not exist>')

                # adding Action-Edit
                detail_button_html = '<a href="/order/' + \
                    str(value.id) + \
                    '" class="btn btn-info" role="button">{}</a>'.format(
                        _('Details'))

                # adding Action-Edit
                edit_button_html = '<a href="/order/edit/' + \
                    str(value.id) + \
                    '" class="btn btn-warning" role="button">{}</a>'.format(
                        _('Edit'))

                # adding Action-Delete
                delete_button_html = '<a href="/order/delete/' + \
                    str(value.id) + \
                    '" class="btn btn-danger" role="button">{}</a>'.format(
                        _('Delete'))

                current_row.append(
                    mark_safe(mark_safe(detail_button_html) + " " + mark_safe(edit_button_html) + " " + mark_safe(delete_button_html)))

                context['row_data'].append(current_row)

        return context


class BaseDetailView(DetailView):
    template_name = 'generic/detail.html'

    def get_context_data(self, **kwargs):
        context = super(BaseDetailView, self).get_context_data(**kwargs)
        context['fields_display_name'] = [field[FIELD_DB_NAME]
                                          for field in self.fields]
        context['fields_db_name'] = [field[FIELD_DB_NAME]
                                     for field in self.fields]
        context['fields'] = self.fields

        return context

    def get_object(self):
        obj = model_to_dict(super(BaseDetailView, self).get_object())

        for key, value in obj.iteritems():
            field_data = self.model._meta.get_field(key)
            if field_data.__class__ is models.ForeignKey:
                cls_relatedto = self.model._meta.get_field(key).rel.to
                try:
                    if hasattr(cls_relatedto, "allobjects"):
                        associated_data = cls_relatedto.allobjects.get(
                            pk=value)
                    else:
                        associated_data = cls_relatedto.objects.get(pk=value)
                    obj[key] = str(associated_data)
                except Exception as e:
                    # todo:mal need to log this eventually
                    # cos sometimes associated data might be hard deleted
                    print e

        return obj


class BaseCreateView(CreateView):
    # using same template: Add && Edit
    template_name = 'generic/add.html'


class BaseUpdateView(UpdateView):
    # using same template: Add && Edit
    template_name = 'generic/add.html'


class BaseDeleteView(DeleteView):
    # using same template
    template_name = 'generic/delete.html'
