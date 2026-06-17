from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Usuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("username", models.CharField(error_messages={"unique": "A user with that username already exists."}, help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.", max_length=150, unique=True, validators=[], verbose_name="username")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="email address")),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("rol", models.CharField(choices=[("admin", "Admin"), ("anfitrion", "Anfitrion"), ("huesped", "Huesped")], default="huesped", max_length=20)),
                ("telefono", models.CharField(blank=True, max_length=20, null=True)),
                ("fecha_registro", models.DateTimeField(default=django.utils.timezone.now)),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Amenity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100, unique=True)),
            ],
            options={"verbose_name_plural": "Amenities"},
        ),
        migrations.CreateModel(
            name="Propiedad",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=200)),
                ("descripcion", models.TextField()),
                ("ubicacion", models.CharField(max_length=255)),
                ("precio_noche", models.DecimalField(decimal_places=2, max_digits=12)),
                ("precio_fin_semana", models.DecimalField(decimal_places=2, max_digits=12)),
                ("tarifa_limpieza", models.DecimalField(decimal_places=2, max_digits=12)),
                ("estado", models.CharField(choices=[("disponible", "Disponible"), ("pausada", "Pausada"), ("inactiva", "Inactiva")], default="disponible", max_length=20)),
                ("id_anfitrion", models.ForeignKey(limit_choices_to={"rol": "anfitrion"}, on_delete=django.db.models.deletion.CASCADE, related_name="propiedades", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Reserva",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha_inicio", models.DateField()),
                ("fecha_fin", models.DateField()),
                ("cantidad_huespedes", models.IntegerField()),
                ("estado", models.CharField(choices=[("pendiente", "Pendiente"), ("confirmada", "Confirmada"), ("cancelada", "Cancelada"), ("rechazada", "Rechazada")], default="pendiente", max_length=20)),
                ("precio_total", models.DecimalField(decimal_places=2, max_digits=12)),
                ("id_huesped", models.ForeignKey(limit_choices_to={"rol": "huesped"}, on_delete=django.db.models.deletion.CASCADE, related_name="reservas", to=settings.AUTH_USER_MODEL)),
                ("id_propiedad", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reservas", to="presupuesto.propiedad")),
            ],
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("calificacion", models.IntegerField()),
                ("comentario", models.TextField()),
                ("fecha", models.DateTimeField(default=django.utils.timezone.now)),
                ("id_propiedad", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="presupuesto.propiedad")),
                ("id_reserva", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="presupuesto.reserva")),
                ("id_usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="PropiedadAmenity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("id_amenity", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="presupuesto.amenity")),
                ("id_propiedad", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="presupuesto.propiedad")),
            ],
            options={"unique_together": {("id_propiedad", "id_amenity")}},
        ),
        migrations.AddField(
            model_name="propiedad",
            name="amenities",
            field=models.ManyToManyField(blank=True, related_name="propiedades", through="presupuesto.PropiedadAmenity", to="presupuesto.amenity"),
        ),
        migrations.CreateModel(
            name="Notificacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("mensaje", models.TextField()),
                ("estado", models.CharField(default="pendiente", max_length=20)),
                ("fecha", models.DateTimeField(default=django.utils.timezone.now)),
                ("id_reserva", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="presupuesto.reserva")),
                ("id_usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Disponibilidad",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha", models.DateField()),
                ("estado", models.CharField(choices=[("disponible", "Disponible"), ("bloqueada", "Bloqueada"), ("reservada", "Reservada")], default="disponible", max_length=20)),
                ("id_propiedad", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="disponibilidades", to="presupuesto.propiedad")),
            ],
            options={"unique_together": {("fecha", "id_propiedad")}},
        ),
    ]
