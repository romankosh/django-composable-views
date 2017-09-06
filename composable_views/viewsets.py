from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)

from .mixins.viewset import ViewSet


class CRUDViewSet(ViewSet):
    shared_properties = [
        'model',
    ]

    list_view_base = ListView
    detail_view_base = DetailView
    create_view_base = CreateView
    update_view_base = UpdateView
    delete_view_base = DeleteView
