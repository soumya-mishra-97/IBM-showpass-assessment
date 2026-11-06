# Initial checkout schema. If you edit models, run makemigrations.
from django.conf import settings
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("starts_at", models.DateTimeField()),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="EventSection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ("capacity", models.PositiveIntegerField()),
                ("reserved", models.PositiveIntegerField(default=0)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sections", to="core.event")),
            ],
        ),
        migrations.CreateModel(
            name="PromoCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("code", models.CharField(max_length=50, unique=True)),
                ("discount_type", models.CharField(choices=[("percentage", "Percentage"), ("fixed", "Fixed")], max_length=12)),
                ("discount_value", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ("max_discount", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ("min_tickets", models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ("max_uses", models.PositiveIntegerField(default=100)),
                ("current_uses", models.PositiveIntegerField(default=0)),
                ("valid_from", models.DateTimeField()),
                ("valid_to", models.DateTimeField()),
                ("event", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="promos", to="core.event")),
            ],
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subtotal", models.DecimalField(decimal_places=2, max_digits=12)),
                ("service_fee", models.DecimalField(decimal_places=2, max_digits=12)),
                ("facility_fee", models.DecimalField(decimal_places=2, max_digits=12)),
                ("processing_fee", models.DecimalField(decimal_places=2, max_digits=12)),
                ("discount_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("status", models.CharField(default="created", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.event")),
                ("promo_code", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="orders", to="core.promocode")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="showpass_orders", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Ticket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tickets", to="core.order")),
                ("section", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.eventsection")),
            ],
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("status", models.CharField(default="pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("order", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="payment", to="core.order")),
            ],
        ),
        migrations.AddConstraint(
            model_name="eventsection",
            constraint=models.UniqueConstraint(fields=("event", "name"), name="unique_event_section"),
        ),
    ]
