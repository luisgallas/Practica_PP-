from django.db import migrations, models
import django.utils.timezone


def uppercase_amenities(apps, schema_editor):
    Amenity = apps.get_model("presupuesto", "Amenity")
    PropiedadAmenity = apps.get_model("presupuesto", "PropiedadAmenity")

    amenities_by_upper = {}
    for amenity in Amenity.objects.order_by("id"):
        upper_name = amenity.nombre.strip().upper()
        existing_id = amenities_by_upper.get(upper_name)

        if existing_id:
            for relation in PropiedadAmenity.objects.filter(id_amenity=amenity):
                PropiedadAmenity.objects.get_or_create(
                    id_propiedad_id=relation.id_propiedad_id,
                    id_amenity_id=existing_id,
                )
            PropiedadAmenity.objects.filter(id_amenity=amenity).delete()
            amenity.delete()
            continue

        amenity.nombre = upper_name
        amenity.save(update_fields=["nombre"])
        amenities_by_upper[upper_name] = amenity.id


def copy_amenities_to_direct_relation(apps, schema_editor):
    Propiedad = apps.get_model("presupuesto", "Propiedad")
    PropiedadAmenity = apps.get_model("presupuesto", "PropiedadAmenity")

    for relation in PropiedadAmenity.objects.all():
        propiedad = Propiedad.objects.get(id=relation.id_propiedad_id)
        propiedad.amenities.add(relation.id_amenity_id)


class Migration(migrations.Migration):

    dependencies = [
        ("presupuesto", "0002_alter_usuario_options_alter_usuario_managers_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="propiedad",
            name="calle",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AlterField(
            model_name="propiedad",
            name="ubicacion",
            field=models.CharField(help_text="Ciudad donde se encuentra la propiedad.", max_length=255),
        ),
        migrations.AddField(
            model_name="disponibilidad",
            name="fecha_inicio_reserva",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="disponibilidad",
            name="fecha_publicacion",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.RunPython(uppercase_amenities, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="propiedad",
            name="amenities",
        ),
        migrations.AddField(
            model_name="propiedad",
            name="amenities",
            field=models.ManyToManyField(blank=True, related_name="propiedades", to="presupuesto.amenity"),
        ),
        migrations.RunPython(copy_amenities_to_direct_relation, migrations.RunPython.noop),
        migrations.DeleteModel(
            name="PropiedadAmenity",
        ),
    ]
