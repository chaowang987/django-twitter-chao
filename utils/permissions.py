from rest_framework.permissions import BasePermission


class IsObjectOwner(BasePermission):

    # if detail=False, just check has_permission
    # if detail=True, need to check both has_permission and has_object_permission

    message = 'You do not have permission to access this object.'

    def has_permission(self, request, view):
        return True

    # obj is /api/comments/<obj>/
    def has_object_permission(self, request, view, obj):
        # need to make sure the login user is same as the comment user
        return request.user == obj.user