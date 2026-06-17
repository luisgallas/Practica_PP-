import unicodedata

from django.db import migrations


def normalize_name(name):
    normalized = unicodedata.normalize("NFD", name.strip().upper())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def normalize_existing_amenities(apps, schema_editor):
    Amenity = apps.get_model("presupuesto", "Amenity")

    groups = {}
    for amenity in Amenity.objects.order_by("id"):
        normalized_name = normalize_name(amenity.nombre)
        groups.setdefault(normalized_name, []).append(amenity.id)

    for normalized_name, amenity_ids in groups.items():
        amenities = list(Amenity.objects.filter(id__in=amenity_ids).order_by("id"))
        target = next((amenity for amenity in amenities if amenity.nombre == normalized_name), amenities[0])

        for amenity in amenities:
            if amenity.id == target.id:
                continue
            propiedades = list(amenity.propiedades.all())
            for propiedad in propiedades:
                propiedad.amenities.add(target)
                propiedad.amenities.remove(amenity)
            amenity.delete()

        if target.nombre != normalized_name:
            target.nombre = normalized_name
            target.save(update_fields=["nombre"])


class Migration(migrations.Migration):

    dependencies = [
        ("presupuesto", "0003_refactor_propiedad_amenities_and_availability"),
    ]

    operations = [
        migrations.RunPython(normalize_existing_amenities, migrations.RunPython.noop),
    ]
