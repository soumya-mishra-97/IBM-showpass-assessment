from django.contrib import admin
from .models import Event, EventSection, PromoCode, Order, Ticket, Payment


class EventSectionInline(admin.TabularInline):
    model = EventSection
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "starts_at", "is_active")
    inlines = (EventSectionInline,)


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "event", "discount_type", "discount_value", "max_uses", "current_uses", "deleted_at")
    list_filter = ("discount_type", "event")
    search_fields = ("code",)

    def get_queryset(self, request):
        # Admin must also display soft-deleted records for debugging.
        return PromoCode.all_objects.all()


admin.site.register(Order)
admin.site.register(Ticket)
admin.site.register(Payment)
