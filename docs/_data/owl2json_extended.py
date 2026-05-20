#!/usr/bin/env python3

from collections import defaultdict
from datetime import datetime, timezone
import json

from pyld import jsonld
from rdflib import Graph


CONTEXT = {
    "id": "@id",
    "type": "@type",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "iao": "http://purl.obolibrary.org/obo/",
    "dct": "http://purl.org/dc/terms/",
    "schema": "http://schema.org/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "label": "rdfs:label",
    "comment": "rdfs:comment",
    "subClassOf": {"@id": "rdfs:subClassOf", "@type": "@id"},
    "subPropertyOf": {"@id": "rdfs:subPropertyOf", "@type": "@id"},
    "domain": {"@id": "rdfs:domain", "@type": "@id"},
    "range": {"@id": "rdfs:range", "@type": "@id"},
    "seeAlso": {"@id": "rdfs:seeAlso", "@type": "@id"},
    "altLabel": "skos:altLabel",
    "definition": "iao:IAO_0000115",
    "source": "iao:IAO_0000119",
    "created": "dct:created",
    "license": {"@id": "dct:license", "@type": "@id"},
    "name": "schema:name",
    "personName": "foaf:name",
    "affiliation": {"@id": "schema:affiliation", "@type": "@id"},
    "equivalentClass": {"@id": "owl:equivalentClass", "@type": "@id"},
    "intersectionOf": "owl:intersectionOf",
    "onProperty": {"@id": "owl:onProperty", "@type": "@id"},
    "someValuesFrom": {"@id": "owl:someValuesFrom", "@type": "@id"},
    "versionInfo": "owl:versionInfo",
    "homepage": {"@id": "foaf:homepage", "@type": "@id"},
}


OWL_CLASS = "owl:Class"
OWL_RESTRICTION = "owl:Restriction"
OWL_OBJECT_PROPERTY = "owl:ObjectProperty"
OWL_ONTOLOGY = "owl:Ontology"
FOAF_PERSON = "foaf:Person"


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def first_literal(node, key):
    value = node.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("@value") or value.get("id")
    if isinstance(value, list) and value:
        item = value[0]
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            return item.get("@value") or item.get("id")
    return None


def first_id(node, key):
    value = node.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("id") or value.get("@id")
    if isinstance(value, list) and value:
        item = value[0]
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            return item.get("id") or item.get("@id")
    return None


def ids(node, key):
    output = []
    for item in as_list(node.get(key)):
        if isinstance(item, str):
            output.append(item)
        elif isinstance(item, dict):
            item_id = item.get("id") or item.get("@id")
            if item_id:
                output.append(item_id)
    return output


def has_type(node, rdf_type):
    return rdf_type in as_list(node.get("type"))


def anchor(iri):
    return iri.rsplit("/", 1)[-1] if iri else ""


def ref(iri, index):
    n = index.get(iri, {})
    return {"id": iri, "label": first_literal(n, "label") or iri, "anchor": anchor(iri)}


def sorted_refs(iris, index):
    return sorted((ref(i, index) for i in iris), key=lambda x: x["label"].casefold())


def extract_intersection_members(node):
    value = node.get("intersectionOf")
    if isinstance(value, dict):
        return value.get("@list", [])
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0].get("@list", [])
    return []


def main():
    g = Graph()
    g.parse("PaNET_reasoned.owl", format="xml")

    data = json.loads(g.serialize(format="json-ld"))

    # Compact and flatten once, then build everything from the flat graph.
    compacted = jsonld.compact(data, CONTEXT)
    flattened = jsonld.flatten(compacted, CONTEXT)
    nodes = flattened.get("@graph", []) if isinstance(flattened, dict) else []

    index = {n.get("id"): n for n in nodes if n.get("id")}

    classes_raw = [
        n
        for n in nodes
        if has_type(n, OWL_CLASS)
        and n.get("id")
        and not n["id"].startswith("_:")
        and first_literal(n, "label")
    ]
    object_props_raw = [
        n
        for n in nodes
        if has_type(n, OWL_OBJECT_PROPERTY)
        and n.get("id")
        and not n["id"].startswith("_:")
        and first_literal(n, "label")
    ]
    people_raw = [n for n in nodes if has_type(n, FOAF_PERSON) and first_literal(n, "personName")]
    ontology_raw = next((n for n in nodes if has_type(n, OWL_ONTOLOGY)), {})

    subclass_children = defaultdict(list)
    for cls in classes_raw:
        for parent in ids(cls, "subClassOf"):
            subclass_children[parent].append(cls["id"])

    subproperty_children = defaultdict(list)
    for prop in object_props_raw:
        for parent in ids(prop, "subPropertyOf"):
            subproperty_children[parent].append(prop["id"])

    classes = []
    for cls in classes_raw:
        cls_id = cls["id"]

        equivalent_to = []
        for eq_id in ids(cls, "equivalentClass"):
            eq_node = index.get(eq_id, {})
            eq_types = as_list(eq_node.get("type"))

            if OWL_RESTRICTION in eq_types:
                on_prop = first_id(eq_node, "onProperty")
                some_from = first_id(eq_node, "someValuesFrom")
                if on_prop and some_from:
                    equivalent_to.append(
                        {
                            "kind": "restriction",
                            "property": ref(on_prop, index),
                            "some_values_from": ref(some_from, index),
                        }
                    )

            members = []
            for member in extract_intersection_members(eq_node):
                member_id = member.get("id") or member.get("@id") if isinstance(member, dict) else None
                if member_id:
                    members.append(ref(member_id, index))
            if members:
                equivalent_to.append({"kind": "intersection", "members": members})

        classes.append(
            {
                "id": cls_id,
                "anchor": anchor(cls_id),
                "label": first_literal(cls, "label"),
                "alt_labels": [
                    v if isinstance(v, str) else v.get("@value")
                    for v in as_list(cls.get("altLabel"))
                    if (isinstance(v, str) and v) or (isinstance(v, dict) and v.get("@value"))
                ],
                "definition": first_literal(cls, "definition"),
                "source": first_literal(cls, "source"),
                "super_classes": sorted_refs(ids(cls, "subClassOf"), index),
                "sub_classes": sorted_refs(subclass_children.get(cls_id, []), index),
                "equivalent_to": equivalent_to,
            }
        )

    object_properties = []
    for prop in object_props_raw:
        prop_id = prop["id"]

        characteristics = []
        for t in as_list(prop.get("type")):
            if t != OWL_OBJECT_PROPERTY:
                characteristics.append(
                    {"id": t, "label": t.rsplit("#", 1)[-1] if "#" in t else t}
                )

        object_properties.append(
            {
                "id": prop_id,
                "anchor": anchor(prop_id),
                "label": first_literal(prop, "label"),
                "alt_labels": [
                    v if isinstance(v, str) else v.get("@value")
                    for v in as_list(prop.get("altLabel"))
                    if (isinstance(v, str) and v) or (isinstance(v, dict) and v.get("@value"))
                ],
                "definition": first_literal(prop, "definition"),
                "source": first_literal(prop, "source"),
                "characteristics": sorted(characteristics, key=lambda x: x["label"].casefold()),
                "super_properties": sorted_refs(ids(prop, "subPropertyOf"), index),
                "sub_properties": sorted_refs(subproperty_children.get(prop_id, []), index),
                "domain": ref(first_id(prop, "domain"), index) if first_id(prop, "domain") else None,
                "range": ref(first_id(prop, "range"), index) if first_id(prop, "range") else None,
            }
        )

    authors = []
    for p in people_raw:
        person_name = first_literal(p, "personName")
        if not person_name:
            continue

        aff = None
        aff_id = first_id(p, "affiliation")
        if aff_id and aff_id in index:
            aff_node = index[aff_id]
            aff = {
                "id": aff_id,
                "name": first_literal(aff_node, "personName"),
                "homepage": first_id(aff_node, "homepage"),
            }

        authors.append(
            {
                "id": p.get("id"),
                "name": person_name,
                "orcid": first_id(p, "seeAlso"),
                "affiliation": aff,
            }
        )

    classes.sort(key=lambda x: x["label"].casefold())
    object_properties.sort(key=lambda x: x["label"].casefold())
    authors.sort(key=lambda x: x["name"].casefold())

    extended = {
        "@context": CONTEXT,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_from": "PaNET_reasoned.owl",
        "ontology": {
            "id": ontology_raw.get("id"),
            "name": first_literal(ontology_raw, "name"),
            "created": first_literal(ontology_raw, "created"),
            "version_info": first_literal(ontology_raw, "versionInfo"),
            "license": first_id(ontology_raw, "license"),
            "comment": first_literal(ontology_raw, "comment"),
        },
        "authors": authors,
        "classes": classes,
        "object_properties": object_properties,
    }

    with open("PaNET_reasoned_extended.json", "w", encoding="utf-8") as f:
        json.dump(extended, f, indent=2, ensure_ascii=False)

    print(
        f"Wrote PaNET_reasoned_extended.json with {len(classes)} classes and {len(object_properties)} object properties"
    )


if __name__ == "__main__":
    main()
