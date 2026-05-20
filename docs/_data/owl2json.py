import json
from pyld import jsonld
from rdflib import Graph


# ── CONTEXT / FRAMES ───────────────────────────────────────────────────────────

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
    "altLabel": {"@id": "skos:altLabel", "@container": "@set"},
    "definition": "iao:IAO_0000115",
    "source": "iao:IAO_0000119",
    "subClassOf": {"@id": "rdfs:subClassOf", "@container": "@set"},
    "hasSubClass": {"@reverse": "rdfs:subClassOf", "@container": "@set"},
    "equivalentClass": {"@id": "owl:equivalentClass", "@container": "@set"},
    "onProperty": "owl:onProperty",
    "someValuesFrom": "owl:someValuesFrom",
    "intersectionOf": {"@id": "owl:intersectionOf", "@container": "@list"},
    "subPropertyOf": {"@id": "rdfs:subPropertyOf", "@container": "@set"},
    "hasSubProperty": {"@reverse": "rdfs:subPropertyOf", "@container": "@set"},
    "domain": "rdfs:domain",
    "range": "rdfs:range",
    "seeAlso": {"@id": "rdfs:seeAlso", "@type": "@id"},
    "versionInfo": "owl:versionInfo",
    "created": "dct:created",
    "license": {"@id": "dct:license", "@type": "@id"},
    "name": "schema:name",
    "creator": "dct:creator",
    "personName": "foaf:name",
    "affiliation": "schema:affiliation",
    "homepage": {"@id": "foaf:homepage", "@type": "@id"},
}

ONTOLOGY_FRAME = {
    "@context": CONTEXT,
    "@type": "owl:Ontology",
    "creator": [{
        "@explicit": True,
        "personName": {},
        "seeAlso": {},
        "affiliation": {"personName": {}, "homepage": {}, "seeAlso": {}}
    }],
}

CLASS_FRAME = {
    "@context": CONTEXT,
    "@explicit": True,
    "@type": "owl:Class",
    "label": {},
    "altLabel": {},
    "definition": {},
    "source": {},
    "subClassOf": {"@explicit": True, "label": {}},
    "hasSubClass": {"@explicit": True, "label": {}},
    "equivalentClass": {
        "@explicit": True,
        "onProperty": {"@explicit": True, "label": {}},
        "someValuesFrom": {"@explicit": True, "label": {}},
        "intersectionOf": {"@explicit": True, "label": {}},
    },
}

OBJPROP_FRAME = {
    "@context": CONTEXT,
    "@explicit": True,
    "@type": "owl:ObjectProperty",
    "label": {},
    "altLabel": {},
    "definition": {},
    "source": {},
    "subPropertyOf": {"@explicit": True, "label": {}},
    "hasSubProperty": {"@explicit": True, "label": {}},
    "domain": {"@explicit": True, "label": {}},
    "range": {"@explicit": True, "label": {}},
}


# ── LOAD & FRAME ───────────────────────────────────────────────────────────────
g = Graph()
g.parse("PaNET_reasoned.owl", format="xml")
data = json.loads(g.serialize(format="json-ld"))

onto = jsonld.frame(data, ONTOLOGY_FRAME)
classes_framed = jsonld.frame(data, CLASS_FRAME, {"embed": "@always"})
props_framed = jsonld.frame(data, OBJPROP_FRAME)


# ── POST-PROCESSING ────────────────────────────────────────────────────────────

def has_label_and_is_not_bnode(node):
    return node.get("label") and not node.get("id", "").startswith("_:")

classes_framed["@graph"] = list(filter(has_label_and_is_not_bnode, classes_framed.get("@graph", [])))
props_framed["@graph"] = list(filter(has_label_and_is_not_bnode, props_framed.get("@graph", [])))

classes_framed["@graph"].sort(key=lambda x: x["label"])
props_framed["@graph"].sort(key=lambda x: x["label"])

onto["creator"].sort(key=lambda x: x["personName"])

# ── WRITE ──────────────────────────────────────────────────────────────────────
with open("PaNET_ontology.json", "w", encoding="utf-8") as f:
    json.dump(onto, f, indent=2, ensure_ascii=False)
    print("Wrote PaNET_ontology.json")

with open("PaNET_classes.json", "w", encoding="utf-8") as f:
    json.dump(classes_framed, f, indent=2, ensure_ascii=False)
    print(f"Wrote PaNET_classes.json: {len(classes_framed['@graph'])} classes")

with open("PaNET_object_properties.json", "w", encoding="utf-8") as f:
    json.dump(props_framed, f, indent=2, ensure_ascii=False)
    print(f"Wrote PaNET_object_properties.json: {len(props_framed['@graph'])} object properties")
