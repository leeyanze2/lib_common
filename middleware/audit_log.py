from django.db.models import signals
from django.utils import timezone
from django.utils.functional import curry

import jwt
from shoe_shop.models import ExtendedUser as User
from rest_framework.authentication import get_authorization_header
from rest_framework_jwt.settings import api_settings


class AuditLogMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        if not request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            user = None
            if hasattr(request, 'user') and request.user.is_authenticated():
                user = request.user
            else:
                # handling jwt
                user = self.get_user_from_auth_header(request)

            mark_actor = curry(self.mark_actor, user)
            signals.pre_save.connect(mark_actor, dispatch_uid=(
                self.__class__, request,), weak=False)

        response = self.get_response(request)

        return response

    def process_response(self, request, response):
        signals.pre_save.disconnect(dispatch_uid=(self.__class__, request,))
        return response

    def mark_actor(self, user, sender, instance, **kwargs):
        if user is not None:
            if not getattr(instance, 'created_by_id', None):
                instance.created_by_id = user.id
            if not getattr(instance, 'created', None):
                instance.created = timezone.now()

            instance.modified_by_id = user.id
            instance.modified = timezone.now()

    def get_user_from_auth_header(self, request):
        try:
            auth_keyword, token = get_authorization_header(request).split()
            jwt_header, claims, signature = token.split('.')

            try:
                payload = api_settings.JWT_DECODE_HANDLER(token)
                try:
                    user_id = api_settings.JWT_PAYLOAD_GET_USER_ID_HANDLER(
                        payload)

                    if user_id:
                        user = User.objects.get(pk=user_id, is_active=True)
                        return user
                    else:
                        msg = 'Invalid payload'
                        return None
                except User.DoesNotExist:
                    msg = 'Invalid signature'
                    return None

            except jwt.ExpiredSignature:
                msg = 'Signature has expired.'
                return None
            except jwt.DecodeError:
                msg = 'Error decoding signature.'
                return None
        except ValueError:
            return None
