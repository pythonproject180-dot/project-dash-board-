def role_context(request):
    return {'current_user_role': getattr(request.user, 'role', '')}
