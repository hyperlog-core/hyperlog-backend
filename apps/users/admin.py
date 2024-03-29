from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import User, DeletedUser
from apps.users.forms import UserChangeForm, UserCreationForm


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ["full_name", "email"]
    fieldsets = [
        [
            "Auth",
            {"fields": ["username", "password", "new_user", "login_types"]},
        ],
        ["Personal info", {"fields": ["last_name", "first_name"]}],
        [
            "Settings",
            {
                "fields": [
                    "groups",
                    "is_admin",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ]
            },
        ],
        ["Important dates", {"fields": ["last_login", "registered_at"]}],
        [
            "Hyperlog Personalization",
            {
                "fields": [
                    "tagline",
                    "social_links",
                    "about",
                    "theme_code",
                    "show_avatar",
                    "under_construction",
                    "setup_step",
                ]
            },
        ],
    ]
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = [
        [
            None,
            {
                "classes": ["wide"],
                "fields": [
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ],
            },
        ],
    ]
    search_fields = ["username", "email"]
    ordering = ["username"]
    readonly_fields = ["last_login", "registered_at"]


# Now register the new UserAdmin...
admin.site.register(User, UserAdmin)
# Unregister the Group model from admin.
admin.site.unregister(Group)

admin.site.register(DeletedUser)
