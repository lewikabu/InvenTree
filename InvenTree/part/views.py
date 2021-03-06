# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from django.urls import reverse_lazy

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from company.models import Company
from .models import PartCategory, Part, BomItem
from .models import SupplierPart

from .forms import EditPartForm
from .forms import EditCategoryForm
from .forms import EditBomItemForm

from .forms import EditSupplierPartForm

from InvenTree.views import AjaxCreateView, AjaxUpdateView, AjaxDeleteView

class PartIndex(ListView):
    model = Part
    template_name = 'part/index.html'
    context_object_name = 'parts'

    def get_queryset(self):
        return Part.objects.all()  # filter(category=None)

    def get_context_data(self, **kwargs):

        context = super(PartIndex, self).get_context_data(**kwargs).copy()

        # View top-level categories
        children = PartCategory.objects.filter(parent=None)

        context['children'] = children

        return context


class PartCreate(AjaxCreateView):
    """ Create a new part
    - Optionally provide a category object as initial data
    """
    model = Part
    form_class = EditPartForm
    template_name = 'part/create.html'

    ajax_form_title = 'Create new part'
    ajax_template_name = 'modal_form.html'

    def get_category_id(self):
        return self.request.GET.get('category', None)

    # If a category is provided in the URL, pass that to the page context
    def get_context_data(self, **kwargs):
        context = super(PartCreate, self).get_context_data(**kwargs)

        # Add category information to the page
        cat_id = self.get_category_id()

        if cat_id:
            context['category'] = get_object_or_404(PartCategory, pk=cat_id)

        return context

    # Pre-fill the category field if a valid category is provided
    def get_initial(self):

        initials = super(PartCreate, self).get_initial().copy()

        if self.get_category_id():
            initials['category'] = get_object_or_404(PartCategory, pk=self.get_category_id())

        return initials


class PartDetail(DetailView):
    context_object_name = 'part'
    queryset = Part.objects.all()
    template_name = 'part/detail.html'


class PartEdit(AjaxUpdateView):
    model = Part
    form_class = EditPartForm
    template_name = 'part/edit.html'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Part Properties'


class PartDelete(AjaxDeleteView):
    model = Part
    template_name = 'part/delete.html'
    ajax_template_name = 'part/partial_delete.html'
    ajax_form_title = 'Confirm Part Deletion'

    success_url = '/part/'

    """
    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(PartDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())
    """


class CategoryDetail(DetailView):
    model = PartCategory
    context_object_name = 'category'
    queryset = PartCategory.objects.all()
    template_name = 'part/category_detail.html'


class CategoryEdit(UpdateView):
    model = PartCategory
    template_name = 'part/category_edit.html'
    form_class = EditCategoryForm

    def get_context_data(self, **kwargs):
        context = super(CategoryEdit, self).get_context_data(**kwargs).copy()

        context['category'] = get_object_or_404(PartCategory, pk=self.kwargs['pk'])

        return context


class CategoryDelete(DeleteView):
    model = PartCategory
    template_name = 'part/category_delete.html'
    context_object_name = 'category'
    success_url = '/part/'

    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(CategoryDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())


class CategoryCreate(AjaxCreateView):
    model = PartCategory
    ajax_form_action = reverse_lazy('category-create')
    ajax_form_title = 'Create new part category'
    ajax_template_name = 'modal_form.html'
    template_name = 'part/category_new.html'
    form_class = EditCategoryForm

    def get_context_data(self, **kwargs):
        context = super(CategoryCreate, self).get_context_data(**kwargs).copy()

        parent_id = self.request.GET.get('category', None)

        if parent_id:
            context['category'] = get_object_or_404(PartCategory, pk=parent_id)

        return context

    def get_initial(self):
        initials = super(CategoryCreate, self).get_initial().copy()

        parent_id = self.request.GET.get('category', None)

        if parent_id:
            initials['parent'] = get_object_or_404(PartCategory, pk=parent_id)

        return initials


class BomItemDetail(DetailView):
    context_object_name = 'item'
    queryset = BomItem.objects.all()
    template_name = 'part/bom-detail.html'


class BomItemCreate(AjaxCreateView):
    model = BomItem
    form_class = EditBomItemForm
    template_name = 'part/bom-create.html'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Create BOM item'

    def get_initial(self):
        # Look for initial values
        initials = super(BomItemCreate, self).get_initial().copy()

        # Parent part for this item?
        parent_id = self.request.GET.get('parent', None)

        if parent_id:
            initials['part'] = get_object_or_404(Part, pk=parent_id)

        return initials


class BomItemEdit(AjaxUpdateView):
    model = BomItem
    form_class = EditBomItemForm
    template_name = 'part/bom-edit.html'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit BOM item'


class BomItemDelete(AjaxDeleteView):
    model = BomItem
    template_name = 'part/bom-delete.html'
    context_object_name = 'item'
    ajax_form_title = 'Confim BOM item deletion'

    #success_url = '/part'

    """
    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(BomItemDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())
    """

class SupplierPartDetail(DetailView):
    model = SupplierPart
    template_name = 'company/partdetail.html'
    context_object_name = 'part'
    queryset = SupplierPart.objects.all()


class SupplierPartEdit(UpdateView):
    model = SupplierPart
    template_name = 'company/partedit.html'
    context_object_name = 'part'
    form_class = EditSupplierPartForm


class SupplierPartCreate(CreateView):
    model = SupplierPart
    form_class = EditSupplierPartForm
    template_name = 'company/partcreate.html'
    context_object_name = 'part'

    def get_initial(self):
        initials = super(SupplierPartCreate, self).get_initial().copy()

        supplier_id = self.request.GET.get('supplier', None)
        part_id = self.request.GET.get('part', None)

        if supplier_id:
            initials['supplier'] = get_object_or_404(Company, pk=supplier_id)
            # TODO
            # self.fields['supplier'].disabled = True
        if part_id:
            initials['part'] = get_object_or_404(Part, pk=part_id)
            # TODO
            # self.fields['part'].disabled = True

        return initials


class SupplierPartDelete(DeleteView):
    model = SupplierPart
    success_url = '/supplier/'
    template_name = 'company/partdelete.html'

    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(SupplierPartDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())
