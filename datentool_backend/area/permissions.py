from rest_framework import permissions


class ProtectPresetPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # presets can not be deleted and name, label and
        # source type (except date) can not be changed
        if (obj.is_preset and
            (
                request.method == 'DELETE' or
                'name' in request.data or
                'label_field' in request.data or
                'key_field' in request.data or
                'ftype' in request.data or
                (
                    'source' in request.data and
                    set(request.data['source']) > set(['date'])
                )
            )):
            return False
        return True

