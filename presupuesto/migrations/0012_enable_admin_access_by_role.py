from django.db import migrations


def enable_admin_access_by_role(apps, schema_editor):
    Usuario = apps.get_model("presupuesto", "Usuario")
    Usuario.objects.filter(rol__in=["admin", "anfitrion", "huesped"]).update(is_staff=True)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("presupuesto", "0011_propiedad_politica_cancelacion_reserva_cancelada_por_and_more"),
    ]

    operations = [
        migrations.RunPython(enable_admin_access_by_role, noop),
    ]
